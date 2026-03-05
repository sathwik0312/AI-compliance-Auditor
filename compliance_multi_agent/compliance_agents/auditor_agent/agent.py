from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import json

def audit_configuration(config_as_json_string: str, tool_context: ToolContext) -> str:
    """
    Core Auditor Logic with strict key mapping for your specific config.json.
    """
    rules = tool_context.state.get('parsed_rules')
    if not rules:
        return json.dumps([{"rule": "System", "status": "fail", "detail": "No rules found in session state."}])

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

    # Map the exact natural language used in your 4 rules to the JSON keys
    mapping = {
        "s3 bucket": "s3_buckets",
        "s3 buckets": "s3_buckets",
        "ec2 instance": "ec2_instances",
        "ec2 instances": "ec2_instances",
        "iam user": "iam_users",
        "iam users": "iam_users"
    }

    for rule in rules:
        r_type_raw = rule.get("resource_type", "")
        prop = rule.get("property", "")
        expected = str(rule.get("expected_value", "")).lower()

        # Find the correct key in the JSON
        json_key = mapping.get(r_type_raw.lower())
        if not json_key:
             # Fallback to generic pluralization
             json_key = r_type_raw.lower().replace(" ", "_") + "s"
        
        resources = aws_config.get(json_key, [])
        
        if not resources:
             findings.append({
                "rule": f"{r_type_raw}: {prop}",
                "status": "fail", 
                "detail": f"No resources of type '{json_key}' found in config."
            })
             continue

        for res in resources:
            res_name = res.get("name") or res.get("username") or res.get("instance_id") or "Unknown"
            actual_val = res.get(prop)
            
            # Strict string matching for compliance
            actual_str = str(actual_val).lower() if actual_val is not None else "none"
            is_pass = (actual_str == expected)
            
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
    description="Audits configuration against parsed rules.",
    instruction="""
    You are a technical auditor. 
    You MUST call the `audit_configuration` tool with the configuration provided in the user's message.
    Return ONLY the tool's JSON output.
    """,
    tools=[audit_configuration]
)
