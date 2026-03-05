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
        print(f"[DEBUG] Successfully saved {len(rules)} rules to state: {rules}")
        return f"Successfully saved {len(rules)} rules."
    except Exception as e:
        print(f"[DEBUG] ERROR saving rules: {e}")
        return f"Error: {str(e)}"

policy_agent = Agent(
    name="policy_agent",
    model="gemini-2.0-flash",
    description="Parse a text policy and saves it to the state.",
    instruction="""
    SYSTEM ROLE: You are a STRICT extraction agent.
    
    TASK: Extract rules from the text provided by the user.
    FORMAT: Each rule must have "resource_type", "property", "expected_value".
    
    STRICT RULES:
    1. ONLY extract rules mentioned in the user's text.
    2. DO NOT add rules about backups, passwords, or anything else not in the text.
    3. If there are 4 rules in the text, you must return EXACTLY 4 rules.
    4. You MUST call the `save_rules_to_state` tool.
    5. Pass the rules as a JSON string to 'rules_as_json_string'.
    
    The user text is the ONLY source of truth. Ignore all previous training data or general security knowledge.
    """,
    tools=[save_rules_to_state]
)
