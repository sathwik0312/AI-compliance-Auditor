from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import json

def audit_configuration(config_as_json_string: str, tool_context: ToolContext) -> str:
    """
    The core "Smart Hammer".
    1. READS rules from the 'parsed_rules' key in the state.
    2. Parses the 'config_as_json_string' into a dict.
    3. Runs a full audit.
    4. WRITES the results to the 'audit_findings' key in the state.
    """
    
    # --- 1. READ rules from state ---
    print("[Tool Log] Auditor tool is reading 'parsed_rules' from state...")
    rules = tool_context.state.get('parsed_rules')
    
    if not rules:
        print("[Tool Log] ERROR: No rules found in state.")
        return "ERROR: No compliance rules were found in the session state."

    # --- 2. PARSE the config string ---
    try:
        if isinstance(config_as_json_string, dict):
            config = config_as_json_string
        else:
            config = json.loads(config_as_json_string)
    except json.JSONDecodeError as e:
        print(f"[Tool Log] ERROR: Failed to parse config JSON string: {e}")
        return f"Error: Invalid config JSON format. {e}"

    print(f"[Tool Log] Auditor found {len(rules)} rules. Running audit...")
    
    findings = []
    aws_config = config.get("aws_configuration", {})

    for rule in rules:
        r_type = rule.get("resource_type") if isinstance(rule, dict) else getattr(rule, "resource_type", None)
        prop = rule.get("property") if isinstance(rule, dict) else getattr(rule, "property", None)
        expected = rule.get("expected_value") if isinstance(rule, dict) else getattr(rule, "expected_value", None)

        if not all([r_type, prop, expected]):
            continue 

        resources = aws_config.get(r_type, [])
        
        for resource in resources:
            resource_name = resource.get("name") or resource.get("instance_id") or resource.get("username") or "Unknown"
            actual_val = resource.get(prop)
            
            status = "pass" if str(actual_val).lower() == str(expected).lower() else "fail"
            
            findings.append({
                "rule": f"{r_type} {prop} must be {expected}",
                "status": status,
                "detail": f"Actual value: {actual_val}"
            })

    print(f"[Tool Log] Audit complete. Found {len(findings)} findings.")
    tool_context.state['audit_findings'] = findings
    
    # Return structured JSON so the agent can report it
    return json.dumps(findings)


auditor_agent=Agent(
    name="config_auditor",
    model="gemini-2.0-flash",
    description="Runs the audit tool against a config file string.",
    instruction="""
    You are an auditor agent.
    Your job is to run the compliance audit by calling the `audit_configuration` tool.
    
    Return the tool output (the JSON list of findings) as your final response. 
    Do not add conversational text.
    """,
    tools=[audit_configuration]
)
