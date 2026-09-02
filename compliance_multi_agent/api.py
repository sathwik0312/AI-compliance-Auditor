from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import asyncio
import json
import os
import time
import uuid
import logging
from collections import defaultdict
from compliance_agents.auditor_agent.agent  import auditor_agent
from compliance_agents.policy_agent.agent import policy_agent
from compliance_agents.report_agent.agent import report_agent
from compliance_agents.remediator_agent import remediator_agent
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.runners import Runner
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AuditorAPI")

app = FastAPI()

# Comma-separated list, e.g. "https://compliance.example.com,https://compliance-api.example.com".
# Defaults to "*" so local dev / the old CLI-only usage keeps working unconfigured.
_allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = ["*"] if _allowed_origins_env == "*" else [o.strip() for o in _allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_service = InMemorySessionService()


@app.get("/health")
async def health():
    return {"status": "ok"}
APP_NAME = "ComplianceApp"

async def get_agent_text(agent, request, app_name, session_id, user_id):
    runner = Runner(agent=agent, app_name=app_name, session_service=session_service)
    content = types.Content(role='user', parts=[types.Part(text=request)])
    output = ""
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    output += part.text
    return output

# --- Demo-endpoint guardrails ---
MAX_POLICY_CHARS = 2000
MAX_CONFIG_CHARS = 5000
PIPELINE_STAGE_TIMEOUT = 45  # seconds, per agent call
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 5  # per IP per window

# ponytail: in-memory per-process sliding window, fine for a single-instance demo;
# swap for a shared store (Redis) if this ever runs behind multiple workers.
_rate_buckets: dict[str, list[float]] = defaultdict(list)


class AuditStreamRequest(BaseModel):
    policy: str = Field(..., description="Plain-text security policy")
    config: str = Field(..., description="Raw config.json content as a string")


def _check_rate_limit(client_ip: str) -> None:
    now = time.monotonic()
    bucket = _rate_buckets[client_ip]
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW:
        bucket.pop(0)
    if len(bucket) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: max {RATE_LIMIT_MAX_REQUESTS} audits per {RATE_LIMIT_WINDOW}s. Please wait and try again.",
        )
    bucket.append(now)


def _validate_audit_request(req: AuditStreamRequest) -> None:
    if len(req.policy) > MAX_POLICY_CHARS:
        raise HTTPException(
            status_code=400,
            detail=f"Policy text is too long ({len(req.policy)} chars, max {MAX_POLICY_CHARS}).",
        )
    if len(req.config) > MAX_CONFIG_CHARS:
        raise HTTPException(
            status_code=400,
            detail=f"Config JSON is too long ({len(req.config)} chars, max {MAX_CONFIG_CHARS}).",
        )
    try:
        json.loads(req.config)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Config is not valid JSON: {e.msg} (line {e.lineno}, col {e.colno}).")


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"

@app.post("/audit")
async def start_audit(policy: UploadFile = File(...), config: UploadFile = File(...)):
    USER_ID = f"user-{uuid.uuid4()}"
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, state={})
    SESSION_ID = session.id

    policy_content = (await policy.read()).decode('utf-8')
    config_content = (await config.read()).decode('utf-8')

    # STEP 1: Forced JSON Extraction
    raw_json = await get_agent_text(policy_agent, policy_content, APP_NAME, SESSION_ID, USER_ID)
    try:
        # Clean potential AI markdown and parse
        cleaned_json = raw_json.strip().replace("```json", "").replace("```", "").strip()
        rules = json.loads(cleaned_json)
        # MANUAL INJECTION into state to guarantee success
        # Get the session to ensure we are modifying the right one
        current_session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
        current_session.state["parsed_rules"] = rules
        logger.info(f"Manually injected {len(rules)} rules into state.")
    except Exception as e:
        logger.error(f"Failed to parse AI JSON response: {raw_json}")
        return {"status": "error", "message": "Failed to parse compliance rules."}

    # STEP 2: Auditor
    auditor_prompt = f"Here is the configuration:\n{config_content}\n\nHere are the parsed compliance rules (pass this as parsed_rules_json to your tool):\n{json.dumps(rules)}"
    await get_agent_text(auditor_agent, auditor_prompt, APP_NAME, SESSION_ID, USER_ID)
    
    updated_session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    findings = updated_session.state.get("audit_findings", [])

    # STEP 3: Remediator
    await get_agent_text(remediator_agent, "Generate remediation plan.", APP_NAME, SESSION_ID, USER_ID)

    # STEP 4: Report
    report_prompt = f"Compile final report. Here are the audit findings: {findings}"
    report = await get_agent_text(report_agent, report_prompt, APP_NAME, SESSION_ID, USER_ID)
    
    return {
        "status": "success",
        "sessionId": SESSION_ID,
        "results": {
            "parsed_rules": rules,
            "findings": findings,
            "final_report": report
        }
    }

STAGES = {
    "policy": "Policy Analyst",
    "auditor": "Config Auditor",
    "remediator": "Remediator",
    "report": "Report Writer",
}


class _StageFailed(Exception):
    """Raised (and already reported via an SSE 'error' event) to abort the pipeline."""


async def _run_stage(stage_key: str, coro):
    """Await coro with a timeout, translating failure into a reported _StageFailed."""
    name = STAGES[stage_key]
    try:
        return await asyncio.wait_for(coro, timeout=PIPELINE_STAGE_TIMEOUT)
    except asyncio.TimeoutError:
        raise _StageFailed(f"{name} timed out after {PIPELINE_STAGE_TIMEOUT}s.")
    except Exception as e:
        raise _StageFailed(f"{name} failed: {e}")


async def _run_pipeline_stream(policy_content: str, config_content: str):
    USER_ID = f"user-{uuid.uuid4()}"
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, state={})
    SESSION_ID = session.id

    try:
        # STEP 1: Policy Analyst
        yield _sse("stage_start", {"stage": "policy", "name": STAGES["policy"]})
        raw_json = await _run_stage("policy", get_agent_text(policy_agent, policy_content, APP_NAME, SESSION_ID, USER_ID))
        cleaned_json = raw_json.strip().replace("```json", "").replace("```", "").strip()
        try:
            rules = json.loads(cleaned_json)
        except json.JSONDecodeError:
            raise _StageFailed("Policy Analyst returned unparseable rules.")
        current_session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
        current_session.state["parsed_rules"] = rules
        yield _sse("stage_complete", {"stage": "policy", "name": STAGES["policy"], "output": rules})

        # STEP 2: Config Auditor
        yield _sse("stage_start", {"stage": "auditor", "name": STAGES["auditor"]})
        auditor_prompt = f"Here is the configuration:\n{config_content}\n\nHere are the parsed compliance rules (pass this as parsed_rules_json to your tool):\n{json.dumps(rules)}"
        await _run_stage("auditor", get_agent_text(auditor_agent, auditor_prompt, APP_NAME, SESSION_ID, USER_ID))
        updated_session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
        findings = updated_session.state.get("audit_findings", [])
        yield _sse("stage_complete", {"stage": "auditor", "name": STAGES["auditor"], "output": findings})

        # STEP 3: Remediator
        yield _sse("stage_start", {"stage": "remediator", "name": STAGES["remediator"]})
        await _run_stage("remediator", get_agent_text(remediator_agent, "Generate remediation plan.", APP_NAME, SESSION_ID, USER_ID))
        remediated_session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
        remediation_plan = remediated_session.state.get("remediation_plan", [])
        yield _sse("stage_complete", {"stage": "remediator", "name": STAGES["remediator"], "output": remediation_plan})

        # STEP 4: Report Writer
        yield _sse("stage_start", {"stage": "report", "name": STAGES["report"]})
        report_prompt = f"Compile final report. Here are the audit findings: {findings}"
        report = await _run_stage("report", get_agent_text(report_agent, report_prompt, APP_NAME, SESSION_ID, USER_ID))
        yield _sse("stage_complete", {"stage": "report", "name": STAGES["report"], "output": report})

        yield _sse("done", {
            "sessionId": SESSION_ID,
            "parsed_rules": rules,
            "findings": findings,
            "remediation_plan": remediation_plan,
            "final_report": report,
        })
    except _StageFailed as e:
        logger.error(f"Pipeline stage failed: {e}")
        yield _sse("error", {"message": str(e)})


@app.post("/audit/stream")
async def start_audit_stream(req: AuditStreamRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)
    _validate_audit_request(req)
    return StreamingResponse(
        _run_pipeline_stream(req.policy, req.config),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
