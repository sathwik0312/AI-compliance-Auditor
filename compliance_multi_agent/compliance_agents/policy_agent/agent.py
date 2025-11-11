from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from pydantic import BaseModel

class ComplianceRule(BaseModel):
    resource_type: str
    property: str
    expected_value: str

def save_rules_to_state(rules:list[ComplianceRule],tool_context:ToolContext)->str:
    """
    Takes a list of structured rules and saves them to the session's 'state'.
    """
    print(f"[Tool Log] Saving {len(rules)} rules to state.")

    #This is the "write operation"
    tool_context.state["parsed_rules"]=rules
    return f"Successfully saved {len(rules)} rules."

policy_agent= Agent(
    name="policy_agent",
    model="gemini-2.5-flash",
    description="Parse a text policy and saves it to the state.",
    instruction="""
    You are a security policy analyst.
    Your job is to read a natural language policy.
    You must convert it into a structured list of rules.
    Each rule must have: "resource_type", "property", "expected_value".
    
    EXAMPLE:
    Policy: "All S3 buckets must have 'encryption' set to 'AES256'."
    Result: [{"resource_type": "s3_buckets", "property": "encryption", "expected_value": "AES256"}]

    AFTER you have this list of rules, you MUST convert the
    *entire list* into a valid, single-line JSON STRING.
    
    Your *final* and *only* action MUST be to call the
    `save_rules_to_state` tool. You must pass this
    single JSON string to the 'rules_as_json_string' argument.
    
    Do not output any other text or commentary. Your *only* response
    must be the tool call.
    """,
    tools=[save_rules_to_state]
)