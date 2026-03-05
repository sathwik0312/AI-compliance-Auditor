from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import json

def save_rules_to_state(rules_as_json_string: str, tool_context: ToolContext) -> str:
    """Saves rules to the session's 'state'."""
    try:
        if isinstance(rules_as_json_string, list):
            rules = rules_as_json_string
        else:
            rules = json.loads(rules_as_json_string)
        tool_context.state["parsed_rules"] = rules
        return f"Successfully saved {len(rules)} rules."
    except Exception as e:
        return f"Error: {str(e)}"

policy_agent = Agent(
    name="policy_agent",
    model="gemini-2.0-flash",
    description="Parse a text policy and saves it to the state.",
    instruction="""
    You are a security policy analyst. 
    Read the provided text and extract a list of rules: "resource_type", "property", "expected_value".
    
    CRITICAL: You MUST call the `save_rules_to_state` tool to proceed. 
    Convert your extracted rules into a single JSON string and pass it to the 'rules_as_json_string' argument.
    
    Do not give any preamble. Your FIRST and ONLY action is the tool call.
    """,
    tools=[save_rules_to_state]
)
