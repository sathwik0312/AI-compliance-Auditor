from google.adk.agents import Agent

report_agent = Agent(
    name="report_writer",
    model="gemini-2.0-flash",
    description="Summarizes the final compliance audit results into a professional report.",
    instruction="""
    You are a Senior Compliance Officer.
    
    You will be given the audit findings from the previous agent.
    
    TASK: Generate a professional, executive summary of the audit.
    1. State clearly how many rules passed and how many failed.
    2. Highlight the most critical security violations.
    3. Keep it professional and concise.
    
    Return your response as a clear, formatted text report.
    """
)
