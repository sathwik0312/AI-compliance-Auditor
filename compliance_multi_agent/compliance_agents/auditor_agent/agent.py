from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import json

def audit_configuration(config_as_json_string: str, tool_context: ToolContext) -> str:
    """
    Final Hardened Auditor Logic:
    1. Reads rules from session state
    2. Performs case-insensitive matching on resource types and properties
    3. Guarantees a JSON list return even on error
    """
    rules = tool_context.state.get('parsed_rules')
    if not rules:
        return json.dumps([{"rule": "System", "status": "fail", "detail": "No rules found in session state. Extraction failed."}])

    try:
        if isinstance(config_as_json_string, dict):
            config = config_as_json_string
        else:
            cleaned_config = str(config_as_json_string).strip().replace("```json", "").replace("```", "").strip()
            config = json.loads(cleaned_config)
    except Exception as e:
        return json.dumps([{"rule": "System", "status": "fail", "detail": f"Failed to parse config: {str(e)}"}])

    findings = []
    aws_config = config.get("aws_configuration", {})

    # The mapping based on the provided config.json structure
    # Matches natural language to the actual JSON keys
    key_mapping = {
        "s3 bucket": "s3_buckets",
        "s3 buckets": "s3_buckets",
        "iam user": "iam_users",
        "iam users": "iam_users",
        "ec2 instance": "ec2_instances",
        "ec2 instances": "ec2_instances"
    }

    for rule in rules:
        # Extract rule components (handling different possible key names from policy_agent)
        r_type_raw = rule.get("resource_type") or rule.get("resource") or ""
        prop = rule.get("property") or rule.get("attribute") or ""
        expected = str(rule.get("expected_value") or rule.get("value") or "").lower()

        if not r_type_raw: continue

        # Get the correct key for the aws_configuration dict
        json_key = key_mapping.get(r_type_raw.lower(), r_type_raw.lower().replace(" ", "_"))
        resources = aws_config.get(json_key, [])

        if not resources:
            findings.append({
                "rule": f"{r_type_raw} {prop}",
                "status": "pass",
                "detail": f"No {r_type_raw} resources found to audit."
            })
            continue

        for res in resources:
            res_name = res.get("name") or res.get("username") or res.get("instance_id") or "Unknown"
            # Get actual value, checking for exact prop name or lowercase
            actual_val = res.get(prop)
            if actual_val is None:
                actual_val = res.get(prop.lower())
            
            actual_str = str(actual_val).lower()
            
            # THE CORE CHECK
            is_pass = actual_str == expected
            
            findings.append({
                "rule": f"{r_type_raw}: {prop}",
                "status": "pass" if is_pass else "fail",
                "detail": f"Resource '{res_name}' has {prop}='{actual_val}' (Expected: {expected})"
            })

    tool_context.state['audit_findings'] = findings
    return json.dumps(findings)

auditor_agent = Agent(
    name="config_auditor",
    model="gemini-2.0-flash",
    description="Audits configuration JSON against extracted policy rules.",
    instruction="""
    SYSTEM: You are a compliance audit runner.
    
    TASK: Call the `audit_configuration` tool with the provided configuration JSON.
    
    RESPONSE: Return ONLY the JSON array output from the tool. 
    DO NOT provide any text summary, markdown, or explanation.
    """,
    tools=[audit_configuration]
)
