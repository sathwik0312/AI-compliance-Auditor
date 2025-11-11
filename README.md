# Multi-Agent AI Compliance Auditor


This project is a 4-agent AI system built with the **Google Agent Development Kit (ADK)**. It demonstrates a stateful, sequential pipeline that audits a cloud configuration file (`config.json`) against a natural language security policy (`policy.txt`), identifies violations, and automatically generates the exact remediation commands to fix them.

The agents communicate by reading and writing to a shared **session state** (a "digital whiteboard"), allowing for a complex workflow where each agent builds on the work of the previous one.

---

## Architecture: A 4-Agent Pipeline

This project uses a sequential, stateful architecture. A central `main.py` script (the "Conductor") calls each agent in order. The agents communicate by reading and writing to a shared `ToolContext.state` object.



1.  **Agent 1: The Policy Analyst**
    * **Input:** A plain-text `policy.txt` file.
    * **Task:** Uses an LLM (Gemini) to parse the natural language policy into a strict JSON list of rules.
    * **Output:** Calls the `save_rules_to_state` tool to write the rules to `state['parsed_rules']`.

2.  **Agent 2: The Config Auditor**
    * **Input:** A `config.json` file.
    * **Task:** Calls the `audit_configuration` tool. This tool *reads* `state['parsed_rules']` and compares them against the `config.json`.
    * **Output:** The tool writes a list of findings to `state['audit_findings']`.

3.  **Agent 3: The Remediator**
    * **Input:** Triggers and reads `state['audit_findings']`.
    * **Task:** For each finding, this agent uses its LLM brain to generate the precise AWS CLI command required to fix the violation.
    * **Output:** Calls the `save_remediation_plan` tool to write a list of (finding + remediation) objects to `state['remediation_plan']`.

4.  **Agent 4: The Report Writer**
    * **Input:** The `main.py` script manually reads `state['remediation_plan']` and passes it to the agent.
    * **Task:** This simple, tool-less agent formats the final JSON data into a clean, human-readable Markdown report.
    * **Output:** The final report.

---

## 🚀 Demo Output

This is the output from running the pipeline with a `policy.txt` and a `config.json` that contains 3 violations.

```text
$ python main.py
Starting AI Compliance Auditor (4-Agent Pipeline)...
[Conductor] New session created: 65437fdb-2ff9-4a3d-b155-852f1b3f7648

--- STEP 1: Running Policy Analyst ---
[Tool Log] Got rules as JSON string. Parsing...
[Tool Log] Saving 4 rules to state.
[Conductor] Policy Agent response: Successfully saved 4 rules.

--- STEP 2: Running Config Auditor ---
[Tool Log] Auditor tool is reading 'parsed_rules' from state...
[Tool Log] Auditor found 4 rules. Running audit...
[Tool Log] Audit complete. Found 3 findings.
[Conductor] Auditor Agent response: Audit complete. Found 3 findings.

--- STEP 3: Running Remediator Agent ---
[Tool Log] Reading 'audit_findings' from state and converting to string.
[Tool Log] Got remediation plan as JSON string. Parsing...
[Tool Log] Saving remediation plan with 3 steps to state.
[Conductor] Remediator Agent response: Successfully saved remediation plan.

--- STEP 4: Running Report Writer ---
[Conductor] Manually loading session state...
[Conductor] Passing plan with 3 steps to Report Writer.

==============================
Final Compliance Report
==============================
## 3 Violations Found

* **Resource:** `s3-bucket-logs`
    * **Problem:** `encryption` was `None` (Expected: `AES256`)
    * **Remediation:** `aws s3api put-bucket-encryption --bucket s3-bucket-logs --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'`

* **Resource:** `s3-bucket-public`
    * **Problem:** `public_access` was `True` (Expected: `false`)
    * **Remediation:** `aws s3api put-public-access-block --bucket s3-bucket-public --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"`

* **Resource:** `alice`
    * **Problem:** `mfa_enabled` was `False` (Expected: `true`)
    * **Remediation:** `aws iam create-virtual-mfa-device --virtual-mfa-device-name MyVirtualMFA --outfile MyVirtualMFA.qr --bootstrap-method QRCode && aws iam enable-mfa-device --user-name alice --serial-number arn:aws:iam::ACCOUNT-ID:mfa/MyVirtualMFA --authentication-code-1 CODE1 --authentication-code-2 CODE2`


**How to Run
1.Build a Docker image:
    docker build -t compliance-auditor .

2. Run the container
    docker run --rm -e GOOGLE_API_KEY="YOUR_API_KEY_GOES_HERE" compliance-auditor