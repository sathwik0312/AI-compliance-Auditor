from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import json

def save_rules_to_state(rules: str, tool_context: ToolContext) -> str:
    """
    Saves the extracted compliance rules to the session state.
    Args:
        rules: A JSON-formatted string containing the list of rules.
    """
    try:
        print(f"[Tool Log] Received rules: {rules}")
        # Handle list vs string
        if isinstance(rules, list):
            data = rules
        else:
            # Clean possible markdown
            cleaned = str(rules).strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
            
        tool_context.state["parsed_rules"] = data
        return f"Successfully saved {len(data)} rules to state."
    except Exception as e:
        print(f"[Tool Log] Error parsing rules: {str(e)}")
        return f"Error: {str(e)}"

policy_agent = Agent(
    name="policy_agent",
    model="gemini-2.0-flash",
    description="Extracts structured compliance rules from text.",
    instruction="""
    You are a Data Extraction Specialist.
    
    TASK:
    1. Read the provided security policy.
    2. Extract each requirement into this format: {"resource_type": "...", "property": "...", "expected_value": "..."}
    3. Call the `save_rules_to_state` tool with the FULL LIST of rules as a JSON string.
    
    RULES:
    - ONLY extract rules explicitly mentioned.
    - Do not add rules from your own memory.
    - If the text mentions S3, EC2, and IAM, only extract those.
    - Your FIRST response must be a call to the `save_rules_to_state` tool.
    """,
    tools=[save_rules_to_state]
)
