from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import os
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

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
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
    
    output = None
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            output = event.content.parts[0].text
            break
    return output

@app.post("/audit")
async def start_audit(policy: UploadFile = File(...), config: UploadFile = File(...)):
    APP_NAME = "ComplianceApp"
    USER_ID = "portfolio-user"
    
    # Create Session
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, state={})
    SESSION_ID = session.id

    # Read files
    policy_content = (await policy.read()).decode('utf-8')
    config_content = (await config.read()).decode('utf-8')

    # Step 1: Policy Analyst
    step1_response = await run_agent_conversation(policy_agent, policy_content, APP_NAME, SESSION_ID, USER_ID)

    # Step 2: Auditor
    step2_response = await run_agent_conversation(auditor_agent, config_content, APP_NAME, SESSION_ID, USER_ID)

    # Step 3: Remediator
    step3_response = await run_agent_conversation(remediator_agent, "Audit complete. Generate remediation plan.", APP_NAME, SESSION_ID, USER_ID)

    # Step 4: Report Writer
    step4_response = await run_agent_conversation(report_agent, "Generate final report.", APP_NAME, SESSION_ID, USER_ID)

    return {
        "status": "success",
        "sessionId": SESSION_ID,
        "results": {
            "parsed_rules": step1_response,
            "findings": step2_response,
            "remediation": step3_response,
            "final_report": step4_response
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
