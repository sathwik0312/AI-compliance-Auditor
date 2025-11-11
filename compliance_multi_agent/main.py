import asyncio
import json

from compliance_agents.auditor_agent.agent  import auditor_agent
from compliance_agents.policy_agent.agent import policy_agent
from compliance_agents.report_agent.agent import report_agent
from compliance_agents.remediator_agent import remediator_agent
from google.adk.sessions import InMemorySessionService
from dotenv import load_dotenv
from google.genai import types
from google.adk.runners import Runner

load_dotenv()

async def run_agent_conversation(agent, request, app_name, session_id, user_id):
    runner = Runner(
        agent=agent,
        app_name=app_name,
        session_service=session_service
    )
    # Prepare message depending on the format
    if isinstance(request, str):
        content = types.Content(role='user', parts=[types.Part(text=request)])
    else:
        content = types.Content(role='user', parts=[types.Part(data=request)])
    # Run async and extract the final output
    output = None
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            output = event.content.parts[0].text
            break
    return output


async def main():

    print("Starting AI Compliance Auditor..")

    APP_NAME="ComplianceApp"
    USER_ID="hackathon-user"

    global session_service
    session_service = InMemorySessionService()

    session=await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        state={}
    )
    SESSION_ID=session.id
    print(f"[Conductor] New session created:{SESSION_ID}")


    # = = STEP 1: Run Policy Agent = =
    # Load the policy file and pass its content to the agent
    print("\n--- STEP 1: Running Policy Analyst ---")
    with open("policy.txt",'rb') as f:
        policy_bytes = f.read()
    policy_text = policy_bytes.decode('utf-8')
    
    step1_response= await run_agent_conversation(
        agent=policy_agent,
        request=policy_text,
        app_name=APP_NAME,
        session_id=SESSION_ID,
        user_id=USER_ID
    )

    print(f"[Conductor] Policy Agent response: {step1_response}")

    # == STEP 2: Run Auditor Agent ==
    # Load the config file and pass its content to the agent
    print("\n--- STEP 2: Running config Auditor ---")
    with open("config.json", 'rb') as f:
        config_bytes = f.read()
    config_text = config_bytes.decode('utf-8')

    step2_response=await run_agent_conversation(
        agent=auditor_agent,
        request=config_text,
        app_name=APP_NAME,
        session_id=SESSION_ID,
        user_id=USER_ID
    )

    print(f"[Conductor] Auditor Agent response: {step2_response}")

    # ==STEP 3: Run Report Writer Agent ==
    # We just need to trigger the agent. Its instructions will
    # tell it to call the tool to get findings from the state.
    print("\n--- STEP 3: Running remediator agent ---")
    step3_response= await run_agent_conversation(
        agent=remediator_agent,
        request="The audit is complete. Please generate the remediation plan.",
        app_name=APP_NAME,
        session_id=SESSION_ID,
        user_id=USER_ID
    )
    print(f"[Conductor] Remediator Agent response: {step3_response}")


    print("\n--- STEP 4: Running Report Writer ---")
    step4_response= await run_agent_conversation(
        agent=report_agent,
        request="The remediation plan is ready. Please generate the final compliance report.",
        app_name=APP_NAME,
        session_id=SESSION_ID,
        user_id=USER_ID
    )

    final_report=step4_response

    print("\n" + "="*30)
    print("Final Compliance Report")
    print("="*30)
    print(final_report)

if __name__ == "__main__":
    asyncio.run(main())

