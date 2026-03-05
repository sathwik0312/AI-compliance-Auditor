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

# VERY permissive CORS for the interview
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_service = InMemorySessionService()
APP_NAME = "ComplianceApp"

@app.get("/health")
async def health():
    return {"status": "ok", "message": "Auditor API is online"}

async def run_agent_conversation(agent, request, app_name, session_id, user_id):
    logger.info(f"Triggering Agent: {agent.name}")
    runner = Runner(
        agent=agent,
        app_name=app_name,
        session_service=session_service
    )
    if isinstance(request, str):
        content = types.Content(role='user', parts=[types.Part(text=request)])
    else:
        content = types.Content(role='user', parts=[types.Part(data=request)])
    
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        pass
    
    session = await session_service.get_session(app_name, session_id, user_id)
    return session.state

@app.post("/audit")
async def start_audit(policy: UploadFile = File(...), config: UploadFile = File(...)):
    USER_ID = f"user-{uuid.uuid4()}"
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, state={})
    SESSION_ID = session.id
    logger.info(f"New session started: {SESSION_ID}")

    policy_content = (await policy.read()).decode('utf-8')
    config_content = (await config.read()).decode('utf-8')

    # Step 1: Policy Analyst
    state = await run_agent_conversation(policy_agent, policy_content, APP_NAME, SESSION_ID, USER_ID)
    
    if "parsed_rules" not in state or not state["parsed_rules"]:
         return {"status": "error", "message": "Policy agent failed to extract rules."}

    # Step 2: Auditor
    state = await run_agent_conversation(auditor_agent, config_content, APP_NAME, SESSION_ID, USER_ID)
    
    # Step 3: Remediator
    state = await run_agent_conversation(remediator_agent, "Generate remediation plan.", APP_NAME, SESSION_ID, USER_ID)

    # Step 4: Report Writer
    state = await run_agent_conversation(report_agent, "Compile final report.", APP_NAME, SESSION_ID, USER_ID)

    return {
        "status": "success",
        "sessionId": SESSION_ID,
        "results": {
            "parsed_rules": state.get("parsed_rules"),
            "findings": state.get("audit_findings"),
            "final_report": state.get("final_report")
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
