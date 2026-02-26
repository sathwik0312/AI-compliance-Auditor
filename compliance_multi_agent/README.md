# AI Compliance Auditor 🛡️🔍

An autonomous multi-agent system designed to bridge the gap between static security policies and live cloud configurations. Built with the **Google ADK** and **LangChain**, this system automates the auditing process for commercial real estate (CRE) and fintech underwriting.

## 🚀 Overview

Manual compliance auditing is slow and prone to human error. The **AI Compliance Auditor** uses a team of specialized agents to:
1. **Analyze Policies:** Extract structured constraints from raw text documents.
2. **Audit Configurations:** Cross-reference live data (JSON/YAML) against those extracted rules.
3. **Generate Remediation Plans:** Provide clear, actionable steps to fix identified violations.

## 🏗️ Architecture

The system utilizes a hierarchical multi-agent orchestration:
- **Policy Agent:** Specialized in parsing regulatory and legal documents.
- **Auditor Agent:** Performs the technical comparison between policy and configuration.
- **Remediator Agent:** Formulates the final compliance report and fix-list.

## 🛠️ Tech Stack

- **Framework:** Google ADK, LangChain
- **Models:** Llama-3, Gemini
- **Backend:** Python, FastAPI
- **Data:** ChromaDB (RAG for high-fidelity reasoning)

## 🏁 Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the auditor:
   ```bash
   python main.py
   ```

---
*Developed for high-stakes automated auditing and underwriting analysis.*
