from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from pydantic import BaseModel
from typing import List
import json

class ComplianceRule(BaseModel):
    resource_type: str
    property: str
    expected_value: str

def save_rules_to_state(rules_as_json_string: str, tool_context: ToolContext) -> str:
    """
    Takes a JSON string of rules and saves them to the session's 'state'.
    """
    try:
        rules = json.loads(rules_as_json_string)
        print(f"[Tool Log] Saving {len(rules)} rules to state.")
        tool_context.state["parsed_rules"] = rules
        return f"Successfully saved {len(rules)} rules."
    except Exception as e:
        print(f"[Tool Log] Error saving rules: {e}")
        return f"Failed to save rules: {str(e)}"

policy_agent = Agent(
    name="policy_agent",
    model="gemini-2.0-flash", # Upgraded for better tool calling
    description="Parse a text policy and saves it to the state.",
    instruction="""
    You are a security policy analyst.
    Your job is to read the natural language policy provided by the user.
    You must convert the *provided text* into a structured list of rules.
    Each rule must have: "resource_type", "property", "expected_value".
    
    IMPORTANT: Do not use any internal knowledge or sample data. ONLY use the text provided in the current message.
    
    AFTER you have this list of rules, you MUST convert the
    *entire list* into a valid, single-line JSON string.
    
    Your *final* and *only* action MUST be to call the
    `save_rules_to_state` tool. You must pass this
    single JSON string to the 'rules_as_json_string' argument.
    
    Do not output any other text.
    """,
    tools=[save_rules_to_state]
)
