from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import json

def save_rules_to_state(rules_as_json_string: str, tool_context: ToolContext) -> str:
    """
    Saves the extracted compliance rules to the session state.
    Args:
        rules_as_json_string: A JSON string or list containing the rules.
    """
    try:
        print(f"[DEBUG] save_rules_to_state called with: {rules_as_json_string}")
        # Handle if model passes a list directly instead of a string
        if isinstance(rules_as_json_string, list):
            rules = rules_as_json_string
        else:
            # Clean possible markdown formatting
            cleaned = str(rules_as_json_string).strip().replace("```json", "").replace("```", "").strip()
            rules = json.loads(cleaned)
            
        if not isinstance(rules, list):
            return "Error: rules must be a list of objects."

        tool_context.state["parsed_rules"] = rules
        print(f"[DEBUG] State updated with {len(rules)} rules.")
        return f"Successfully saved {len(rules)} rules to session state."
    except Exception as e:
        print(f"[DEBUG] Tool Error: {str(e)}")
        return f"Error: {str(e)}"

policy_agent = Agent(
    name="policy_agent",
    model="gemini-2.0-flash",
    description="Analyzes security policy text and saves structured rules to state.",
    instruction="""
    You are a Security Policy Analyst. 
    Your ONLY task is to extract compliance rules from the user's input.
    
    For each rule, identify:
    - resource_type (e.g., S3 bucket, IAM user)
    - property (e.g., encryption, mfa_enabled)
    - expected_value (e.g., AES256, true)
    
    PROCEDURE:
    1. Extract all rules from the provided text.
    2. Convert the list of rules into a JSON string.
    3. CALL the `save_rules_to_state` tool with that JSON string.
    
    CRITICAL: 
    - Do not talk to the user. 
    - Do not summarize. 
    - JUST call the tool.
    - If you do not call the tool, the audit will fail.
    """,
    tools=[save_rules_to_state]
)
