from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import json

def audit_configuration(config_as_json_string: str, tool_context: ToolContext) -> str:
    """
    The core "Smart Hammer".
    1. READS rules from the 'parsed_rules' key in the state.
    2. Runs a full audit against the config.
    3. WRITES results to state.
    """
    rules = tool_context.state.get('parsed_rules')
    if not rules:
        return "ERROR: No compliance rules found."

    try:
        if isinstance(config_as_json_string, dict):
            config = config_as_json_string
        else:
            config = json.loads(config_as_json_string)
    except Exception as e:
        return f"Error: Invalid JSON format. {e}"

    findings = []
    aws_config = config.get("aws_configuration", {})

    for rule in rules:
        r_type = rule.get("resource_type")
        prop = rule.get("property")
        expected = rule.get("expected_value")

        # Normalize lookups for the specific config.json structure provided
        lookup_keys = [
            r_type, 
            str(r_type).lower().replace(" ", "_"), 
            str(r_type).lower().replace(" ", "_") + "s"
        ]
        
        resources = []
        for k in lookup_keys:
            if k in aws_config:
                resources = aws_config[k]
                break

        for resource in resources:
            resource_name = resource.get("name") or resource.get("instance_id") or resource.get("username") or "Unknown"
            actual_val = resource.get(prop)
            
            # String comparison for robustness
            is_pass = str(actual_val).lower() == str(expected).lower()
            
            findings.append({
                "rule": f"{r_type} {prop} must be {expected}",
                "status": "pass" if is_pass else "fail",
                "detail": f"Resource '{resource_name}' has {prop}='{actual_val}'"
            })

    tool_context.state['audit_findings'] = findings
    return json.dumps(findings)

auditor_agent=Agent(
    name="config_auditor",
    model="gemini-2.0-flash",
    description="Runs the audit tool against a config file string.",
    instruction="""
    You are a technical auditor. 
    Your ONLY job is to call the `audit_configuration` tool.
    Pass the configuration data as the 'config_as_json_string' argument.
    Return ONLY the raw JSON output from the tool.
    """,
    tools=[audit_configuration]
)
