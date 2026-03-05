from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import json

def save_rules_to_state(rules_as_json_string: str, tool_context: ToolContext) -> str:
    """
    Saves the extracted compliance rules to the session state.
    """
    try:
        if isinstance(rules_as_json_string, list):
            rules = rules_as_json_string
        else:
            cleaned = str(rules_as_json_string).strip().replace("```json", "").replace("```", "").strip()
            rules = json.loads(cleaned)
            
        tool_context.state["parsed_rules"] = rules
        return f"Successfully saved {len(rules)} rules."
    except Exception as e:
        return f"Error: {str(e)}"

policy_agent = Agent(
    name="policy_agent",
    model="gemini-2.0-flash",
    description="Analyzes security policy text and saves structured rules to state.",
    instruction="""
    You are a Security Policy Analyst. 
    Your ONLY task is to extract compliance rules from the provided text.
    
    For each rule, identify:
    - resource_type (e.g., S3 bucket, IAM user)
    - property (e.g., encryption, mfa_enabled)
    - expected_value (e.g., AES256, true)
    
    PROCEDURE:
    1. Extract all rules.
    2. Convert the list of rules into a JSON string.
    3. CALL the `save_rules_to_state` tool with that JSON string.
    
    CRITICAL: 
    - Do not use brackets like {{var}} in your response.
    - JUST call the tool.
    """,
    tools=[save_rules_to_state]
)
