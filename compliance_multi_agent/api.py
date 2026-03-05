from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import os
import uuid
import logging
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_service = InMemorySessionService()
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
        session.state["parsed_rules"] = rules
        logger.info(f"Manually injected {len(rules)} rules into state.")
    except Exception as e:
        logger.error(f"Failed to parse AI JSON response: {raw_json}")
        return {"status": "error", "message": "Failed to parse compliance rules."}

    # STEP 2: Auditor
    findings = await get_agent_text(auditor_agent, config_content, APP_NAME, SESSION_ID, USER_ID)
    
    # STEP 3: Remediator
    remediation = await get_agent_text(remediator_agent, "Generate remediation plan.", APP_NAME, SESSION_ID, USER_ID)

    # STEP 4: Report
    report = await get_agent_text(report_agent, "Compile final report.", APP_NAME, SESSION_ID, USER_ID)

    return {
        "status": "success",
        "sessionId": SESSION_ID,
        "results": {
            "parsed_rules": session.state.get("parsed_rules"),
            "findings": findings,
            "final_report": report
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
