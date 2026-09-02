from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import json

policy_agent = Agent(
    name="policy_agent",
    model="gemini-2.5-flash",
    description="Extracts structured compliance rules from text.",
    instruction="""
    You are a JSON extraction engine. 
    Read the provided text and return ONLY a valid JSON list of rules.
    
    Each rule must have: "resource_type", "property", "expected_value".
    
    Example output:
    [{"resource_type": "S3 bucket", "property": "encryption", "expected_value": "AES256"}]
    
    CRITICAL: Output ONLY the raw JSON list. Do not include markdown code blocks. Do not include any other text.
    """
)
