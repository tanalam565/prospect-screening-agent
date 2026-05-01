"""
Chatbot agent using AutoGen multi-agent group chat.
Agents talk to each other to make screening decisions:

- UserProxy         : receives user message, kicks off the conversation
- DataAgent         : converts natural language to SQL and fetches prospect data
- CreditAnalyst     : analyzes credit report
- IncomeVerifier    : verifies income and affordability
- IdentityChecker   : checks identity document consistency
- ScreeningManager  : synthesizes all reports and makes final recommendation

Install: pip install pyautogen
Requires: Ollama running locally e.g. `ollama pull llama3`
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ApplicantScreener.settings')
django.setup()

from django.conf import settings
from django.db import connection
import autogen

# ── LLM config pointing to local Ollama ─────────────────────────────────────
llm_config = {
    "config_list": [
        {
            "model": "llama3",
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",
        }
    ],
    "temperature": 0,
}


# ── Tool: run SQL against the database ───────────────────────────────────────
def run_sql(sql: str) -> str:
    """Execute a SQL query and return results as a string."""
    try:
        sql = sql.replace("```sql", "").replace("```", "").strip()
        with connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            if not rows:
                return "No results found."
            result = [dict(zip(columns, row)) for row in rows]
            return str(result)
    except Exception as e:
        return f"SQL Error: {str(e)}"


# ── Define Agents ─────────────────────────────────────────────────────────────
data_agent = autogen.AssistantAgent(
    name="DataAgent",
    system_message="""You are a data retrieval specialist with access to a SQLite database.
When asked to find or list prospects, write a SQL query against these tables:
- prospect_prospect (id, first_name, last_name, email, phone, city, state, date_of_birth)
- prospect_creditreport (id, prospect_id, credit_score, total_debt, monthly_debt_payments, repayment_history_status, has_eviction_history, eviction_count, has_criminal_record, bankruptcy_history, pending_payments_amount)
- prospect_proofofincome (id, prospect_id, employer_name, employment_status, gross_monthly_income, pay_frequency, verified)
- prospect_photoid (id_number, prospect_id, id_type, name_on_id, address_on_id, date_of_birth_on_id, expiration_date)
- prospect_screeningresult (id, prospect_id, overall_risk_level, recommendation, debt_to_income_ratio, ability_to_pay_score)
- prospect_flag (id, screening_result_id, flag_type, severity, description)

Call the run_sql function with your SQL query. Only speak when asked about data retrieval.""",
    llm_config={**llm_config, "functions": [
        {
            "name": "run_sql",
            "description": "Run a SQL query against the applicant database",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "The SQL query to execute"}
                },
                "required": ["sql"],
            },
        }
    ]},
    function_map={"run_sql": run_sql},
)

credit_analyst = autogen.AssistantAgent(
    name="CreditAnalyst",
    system_message="""You are a credit analyst specializing in rental applicant screening.
When given credit data, analyze it and return:
- risk_level: low / medium / high
- key_concerns: list of issues found
- summary: one paragraph conclusion
Only speak when asked to analyze credit information.""",
    llm_config=llm_config,
)

income_verifier = autogen.AssistantAgent(
    name="IncomeVerifier",
    system_message="""You are an income verification specialist.
Check if gross monthly income >= 3x monthly rent. Flag if debt-to-income ratio > 35%.
Return:
- income_sufficient: yes / no
- dti_assessment: pass / flag
- key_concerns: list of issues
- summary: one paragraph conclusion
Only speak when asked to verify income.""",
    llm_config=llm_config,
)

identity_checker = autogen.AssistantAgent(
    name="IdentityChecker",
    system_message="""You are an identity verification specialist.
Check for consistency between applicant personal info and their photo ID.
Return:
- identity_verified: yes / no
- mismatches: list of discrepancies found
- summary: one paragraph conclusion
Only speak when asked to verify identity.""",
    llm_config=llm_config,
)

screening_manager = autogen.AssistantAgent(
    name="ScreeningManager",
    system_message="""You are a senior rental screening manager coordinating the team.

For data questions: ask DataAgent to run the SQL query.
For screening evaluations:
  1. Ask DataAgent to fetch full prospect data by ID
  2. Ask CreditAnalyst to analyze the credit report
  3. Ask IncomeVerifier to verify income (monthly rent is $1800 unless specified)
  4. Ask IdentityChecker to verify identity
  5. Synthesize all reports into a final recommendation: approve / deny / conditional

Always end a completed screening with 'SCREENING COMPLETE' followed by the final decision.
For simple data queries, end with 'QUERY COMPLETE' after DataAgent responds.""",
    llm_config=llm_config,
)

user_proxy = autogen.UserProxyAgent(
    name="UserProxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=0,
    is_termination_msg=lambda msg: any(
        phrase in msg.get("content", "")
        for phrase in ["SCREENING COMPLETE", "QUERY COMPLETE"]
    ),
    code_execution_config=False,
)


# ── Run a single chat turn ────────────────────────────────────────────────────
def run_chat(message: str, chat_history: list = None) -> str:
    """Run the multi-agent chatbot with a user message."""

    # Detect if this is a screening request (needs all agents) or a simple query
    is_screening = any(word in message.lower() for word in ["screen", "evaluate", "assess", "analyze prospect"])

    if is_screening:
        # Full pipeline: ScreeningManager → DataAgent → CreditAnalyst → IncomeVerifier → IdentityChecker → ScreeningManager
        agents = [user_proxy, screening_manager, data_agent, credit_analyst, income_verifier, identity_checker, screening_manager]
    else:
        # Simple data query: DataAgent fetches, ScreeningManager summarizes
        agents = [user_proxy, data_agent, screening_manager]

    group_chat = autogen.GroupChat(
        agents=agents,
        messages=[],
        max_round=len(agents) + 2,
        speaker_selection_method="round_robin",
    )

    manager = autogen.GroupChatManager(
        groupchat=group_chat,
        llm_config=llm_config,
    )

    user_proxy.initiate_chat(manager, message=message)

    messages = group_chat.messages
    if messages:
        for msg in reversed(messages):
            if msg.get("name") in ["ScreeningManager", "DataAgent"] and msg.get("content"):
                return msg["content"]
        return messages[-1].get("content", "No response generated.")

    return "No response generated."

