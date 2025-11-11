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
        raise ValueError("No rules found. Run the policy_agent first.")

    # --- 2. PARSE the config string ---
    try:
        config = json.loads(config_as_json_string)
    except json.JSONDecodeError as e:
        print(f"[Tool Log] ERROR: Failed to parse config JSON string: {e}")
        return f"Error: Invalid config JSON format. {e}"

    print(f"[Tool Log] Auditor found {len(rules)} rules. Running audit...")
    
    # --- 3. RUN AUDIT (THIS IS THE MISSING LOGIC) ---
    findings = []
    aws_config = config.get("aws_configuration", {})

    for rule in rules:
        resource_type = rule.get("resource_type")
        prop_to_check = rule.get("property")
        expected_val = rule.get("expected_value")

        if not all([resource_type, prop_to_check, expected_val]):
            continue 

        resources = aws_config.get(resource_type, [])
        
        for resource in resources:
            resource_name = resource.get("name") or resource.get("instance_id") or resource.get("username")
            actual_val = resource.get(prop_to_check)
            
            # This is the core check that was missing
            if str(actual_val).lower() != str(expected_val).lower():
                finding = {
                    "status": "NON-COMPLIANT",
                    "resource_name": resource_name,
                    "resource_type": resource_type,
                    "rule_property": prop_to_check,
                    "expected_value": expected_val,
                    "actual_value": actual_val # Will show 'None'
                }
                findings.append(finding)
    # --- END OF MISSING LOGIC ---

    print(f"[Tool Log] Audit complete. Found {len(findings)} findings.")

    # --- 4. WRITE to state ---
    tool_context.state['audit_findings'] = findings
    
    return f"Audit complete. Found {len(findings)} findings."


auditor_agent=Agent(
    name="config_auditor",
    model="gemini-2.5-flash",
    description="Runs the audit tool against a config file string.",
    instruction="""
    You are an auditor agent.
    Your *only* job is to run the compliance audit.
    You will be given the configuration data as a JSON string.
    You must immediately call the `audit_configuration` tool
    and pass the raw JSON string to its 'config_as_json_string' argument.
    """,
    tools=[audit_configuration]
)