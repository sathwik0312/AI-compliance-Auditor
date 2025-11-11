from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import json

def get_findings_as_json_string(tool_context:ToolContext)->str:
    """Reads the 'audit_findings' from the state and returns them as a JSON string."""
    print("[Tool Log] Reading 'audit findings' from state.")
    findings= tool_context.state.get('audit_findings',[])
    return json.dumps(findings)

def save_remediation_plan(plan_as_json_string: str, tool_context: ToolContext) -> str:
    """
    Takes a JSON *string* of the remediation plan and saves it
    to the 'remediation_plan' key in the state.
    """
    print(f"[Tool Log] Got remediation plan as JSON string. Parsing...")
    try:
        plan_list = json.loads(plan_as_json_string)
    except json.JSONDecodeError as e:
        print(f"[Tool Log] ERROR: Failed to parse plan JSON string: {e}")
        return f"Error: Invalid JSON format. {e}"
    
    tool_context.state['remediation_plan'] = plan_list
    print(f"[Tool Log] Saving remediation plan with {len(plan_list)} steps to state.")
    return f"Successfully saved remediation plan."

remediator_agent=Agent(
    name="remediator_agent",
    model="gemini-2.5-flash",
    description="Generate remediation steps for audit findings.",
    instruction="""
    You are a senior AWS Cloud Security expert. Your job is to create a
    remediation plan.
    
    1.  First, you MUST call the `get_findings_as_json_string` tool to get the
        JSON *string* of audit findings.
    
    2.  After you get the findings string from the tool, PARSE IT.
    
    3.  If the list of findings is empty, you are done. Your *only* action
        is to call the `save_remediation_plan` tool with an empty
        JSON string: '[]'.
    
    4.  If the list has findings, you will create a NEW JSON list.
        For EACH finding, create an object with "finding" and "remediation" keys.
        
    5.  After creating this new list, you MUST convert the
        *entire list* into a valid, single-line JSON STRING.
    
    6.  Your *final* and *only* action MUST be to call the
        `save_remediation_plan` tool. You must pass this
        single JSON string to the 'plan_as_json_string' argument.
    
    Do not output any other text. Your response must be a tool call.
    """,
    tools=[get_findings_as_json_string, save_remediation_plan]
)