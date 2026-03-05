from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import json

def save_rules_to_state(rules_as_json_string: str, tool_context: ToolContext) -> str:
    """Saves rules to the session's 'state'."""
    try:
        # Robust handling for list vs string
        if isinstance(rules_as_json_string, list):
            rules = rules_as_json_string
        else:
            # Clean possible markdown block markers
            cleaned = str(rules_as_json_string).strip().replace("```json", "").replace("```", "").strip()
            rules = json.loads(cleaned)
            
        tool_context.state["parsed_rules"] = rules
        print(f"[Tool Log] Saved {len(rules)} rules to state.")
        return f"SUCCESS: {len(rules)} rules saved."
    except Exception as e:
        print(f"[Tool Log] ERROR in save_rules_to_state: {e}")
        return f"ERROR: {str(e)}"

policy_agent = Agent(
    name="policy_agent",
    model="gemini-2.0-flash",
    description="Extracts structured rules from text.",
    instruction="""
    You are a specialized Data Extraction Agent. 
    
    Task: Convert the provided security policy text into a JSON list of rules.
    Format: Each rule MUST be an object with: "resource_type", "property", "expected_value".
    
    CRITICAL: 
    1. Your ONLY goal is to call the `save_rules_to_state` tool.
    2. You MUST pass the rules as a JSON-formatted string to the 'rules_as_json_string' parameter.
    3. Do NOT provide any text explanation or summary. Just call the tool.
    
    Source Text: 
    {text}
    """,
    tools=[save_rules_to_state]
)
