import asyncio
import os
import shutil
import uuid
import json
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict

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
APP_NAME = "ComplianceApp"

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
    # Use a timeout to prevent infinite loops
    try:
        async with asyncio.timeout(90):
            async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
                if event.is_final_response() and event.content and event.content.parts:
                    for part in event.content.parts:
                        try:
                            if part.text:
                                output += part.text
                        except Exception:
                            # Handle cases where part.text access might fail (e.g. function calls)
                            continue
    except asyncio.TimeoutError:
        print(f"[ERROR] Agent {agent.name} timed out.")
        return "Error: Request timed out."
    return output

@app.post("/audit")
async def start_audit(policy: UploadFile = File(...), config: UploadFile = File(...)):
    USER_ID = f"user-{uuid.uuid4()}"
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, state={})
    SESSION_ID = session.id

    try:
        policy_content = (await policy.read()).decode('utf-8')
        config_content = (await config.read()).decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read upload files: {str(e)}")

    # Step 1: Policy Analyst
    print(f"[API] Step 1: Extracting rules from policy for session {SESSION_ID}")
    await run_agent_conversation(policy_agent, policy_content, APP_NAME, SESSION_ID, USER_ID)

    # Verify state
    state_session = await session_service.get_session(APP_NAME, SESSION_ID, USER_ID)
    parsed_rules = state_session.state.get("parsed_rules", [])
    print(f"[API] Rules stored in state: {len(parsed_rules)}")

    if not parsed_rules:
         return {"status": "error", "message": "Policy agent failed to extract rules. Please check the policy text format."}

    # Step 2: Auditor
    print(f"[API] Step 2: Running audit against configuration")
    findings_summary = await run_agent_conversation(auditor_agent, config_content, APP_NAME, SESSION_ID, USER_ID)

    # Step 3: Remediator
    print(f"[API] Step 3: Generating remediation plan")
    remediation = await run_agent_conversation(remediator_agent, "Based on the findings in the session state, generate a detailed remediation plan.", APP_NAME, SESSION_ID, USER_ID)

    # Step 4: Report Writer
    print(f"[API] Step 4: Compiling final report")
    report = await run_agent_conversation(report_agent, "Generate a professional compliance audit report summarizing the rules, findings, and remediation steps.", APP_NAME, SESSION_ID, USER_ID)

    return {
        "status": "success",
        "sessionId": SESSION_ID,
        "rule_count": len(parsed_rules),
        "results": {
            "summary": findings_summary,
            "remediation": remediation,
            "final_report": report
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
