from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext


def get_remediation_plan(tool_context: ToolContext) -> list[dict]:
    """Reads the 'remediation_plan' from the state."""
    print("[Tool Log] Report writer is reading 'remediation_plan' from state.")
    plan = tool_context.state.get('remediation_plan', [])
    return plan

report_agent=Agent(
    name="report_agent",
    model="gemini-2.5-flash",
    description="Generate a final report with remediation steps.",
    instruction="""
    You are a professional report writer.
    Your input is a JSON *string* representing a remediation plan.
    Your *only* job is to generate a final, human-readable Markdown report
    from this JSON string.
    
    1.  Parse the JSON string.
    2.  If the string represents an empty list, state clearly that "No audit findings were
        found and the configuration is fully compliant."
    3.  If the string has findings, iterate through each object.
        For each object, you will find a "finding" key and a "remediation" key.
        - Use the "finding" key to describe the problem (resource, property, etc.)
        - Use the "remediation" key to provide the fix.
        - Format this clearly in Markdown, using headers (##) for sections
          and bullet points (*) for each finding.
    
    Example for one finding:
    
    ##  1 Violation Found
    
    * **Resource:** `s3-bucket-logs`
        * **Problem:** `encryption` was `None` (Expected: `AES256`)
        * **Remediation:** `aws s3api put-bucket-encryption ...`
    """,
    tools=[]
)