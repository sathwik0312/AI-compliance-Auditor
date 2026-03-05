from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import os
import uuid
from compliance_agents.auditor_agent.agent  import auditor_agent
from compliance_agents.policy_agent.agent import policy_agent
from compliance_agents.report_agent.agent import report_agent
from compliance_agents.remediator_agent import remediator_agent
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.runners import Runner
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_service = InMemorySessionService()

async def run_agent_conversation(agent, request, app_name, session_id, user_id):
    runner = Runner(
        agent=agent,
        app_name=app_name,
        session_service=session_service
    )
    if isinstance(request, str):
        content = types.Content(role='user', parts=[types.Part(text=request)])
    else:
        content = types.Content(role='user', parts=[types.Part(data=request)])
    
    output = ""
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    output += part.text
    return output

@app.post("/audit")
async def start_audit(policy: UploadFile = File(...), config: UploadFile = File(...)):
    APP_NAME = "ComplianceApp"
    USER_ID = f"user-{uuid.uuid4()}" # Generate unique ID per request to prevent session pollution
    
    # Create a completely fresh session for every upload
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, state={})
    SESSION_ID = session.id

    policy_content = (await policy.read()).decode('utf-8')
    config_content = (await config.read()).decode('utf-8')

    # Step 1: Policy Analyst
    print(f"[API] Starting Step 1 for Session {SESSION_ID}")
    await run_agent_conversation(policy_agent, policy_content, APP_NAME, SESSION_ID, USER_ID)

    # Step 2: Verify state
    state_session = await session_service.get_session(APP_NAME, SESSION_ID, USER_ID)
    parsed_rules = state_session.state.get("parsed_rules", [])
    print(f"[API] Parsed Rules in State: {len(parsed_rules)}")

    if not parsed_rules:
         return {"status": "error", "message": "Policy agent failed to extract rules."}

    # Step 3: Auditor
    findings = await run_agent_conversation(auditor_agent, config_content, APP_NAME, SESSION_ID, USER_ID)

    # Step 4: Remediator
    remediation = await run_agent_conversation(remediator_agent, "Audit complete. Generate remediation plan.", APP_NAME, SESSION_ID, USER_ID)

    # Step 5: Report Writer
    report = await run_agent_conversation(report_agent, "Generate final report.", APP_NAME, SESSION_ID, USER_ID)

    return {
        "status": "success",
        "sessionId": SESSION_ID,
        "rule_count": len(parsed_rules),
        "results": {
            "findings": findings,
            "remediation": remediation,
            "final_report": report
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
