"""
AutoGen experiment: Multi-agent applicant screening using conversational agents.
Agents talk to each other in a group chat to reach a final screening decision.

Key difference: AutoGen agents CONVERSE with each other rather than just passing
outputs sequentially. The screening manager can ask follow-up questions to other agents.

Install: pip install pyautogen
Requires: Ollama running locally with a model pulled e.g. `ollama pull llama3`
"""

import os
import sys
import django

# Add the Django project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Setup Django so we can access models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ApplicantScreener.settings')
django.setup()

from prospect.models import Prospect, CreditReport, ProofOfIncome, PhotoID
import autogen

# ── LLM config pointing to local Ollama ─────────────────────────────────────
llm_config = {
    "config_list": [
        {
            "model": "llama3",
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",  # required by AutoGen but not used by Ollama
        }
    ],
    "temperature": 0,
}


# ── Define Agents ────────────────────────────────────────────────────────────
credit_analyst = autogen.AssistantAgent(
    name="CreditAnalyst",
    system_message="""You are a credit analyst specializing in rental applicant screening.
When given a credit report, analyze it and return:
- risk_level: low / medium / high
- key_concerns: list of issues
- summary: one paragraph conclusion
Only speak when asked about credit analysis.""",
    llm_config=llm_config,
)

income_verifier = autogen.AssistantAgent(
    name="IncomeVerifier",
    system_message="""You are an income verification specialist.
Check if gross income is at least 3x the monthly rent. Flag DTI above 35%.
Return:
- income_sufficient: yes / no
- dti_assessment: pass / flag
- key_concerns: list of issues
- summary: one paragraph conclusion
Only speak when asked about income verification.""",
    llm_config=llm_config,
)

identity_checker = autogen.AssistantAgent(
    name="IdentityChecker",
    system_message="""You are an identity verification specialist.
Check for consistency between the applicant's personal info and photo ID.
Return:
- identity_verified: yes / no
- mismatches: list of discrepancies
- summary: one paragraph conclusion
Only speak when asked about identity verification.""",
    llm_config=llm_config,
)

screening_manager = autogen.AssistantAgent(
    name="ScreeningManager",
    system_message="""You are a senior rental screening manager coordinating the screening process.
Your job is to:
1. Ask CreditAnalyst to analyze the credit report
2. Ask IncomeVerifier to verify income
3. Ask IdentityChecker to verify identity
4. Synthesize all reports and make a final recommendation: approve / deny / conditional
5. End with 'SCREENING COMPLETE' followed by your final decision.
You drive the conversation and make the final call.""",
    llm_config=llm_config,
)

# Human proxy to kick off and terminate the conversation
user_proxy = autogen.UserProxyAgent(
    name="UserProxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=0,
    is_termination_msg=lambda msg: "SCREENING COMPLETE" in msg.get("content", ""),
    code_execution_config=False,
)


# ── Main ─────────────────────────────────────────────────────────────────────
def screen_prospect(prospect_id: int, monthly_rent: float = 1800.0):
    prospect = Prospect.objects.get(id=prospect_id)
    credit_report = CreditReport.objects.filter(prospect=prospect).first()
    proof_of_income = ProofOfIncome.objects.filter(prospect=prospect).first()
    photo_id = PhotoID.objects.filter(prospect=prospect).first()

    print(f"\n{'='*60}")
    print(f"AUTOGEN SCREENING: {prospect.first_name} {prospect.last_name}")
    print(f"{'='*60}\n")

    # Build the initial message with all applicant data
    initial_message = f"""Please screen this rental applicant:

APPLICANT: {prospect.first_name} {prospect.last_name}
Email: {prospect.email} | Phone: {prospect.phone}
Address: {prospect.current_address}, {prospect.city}, {prospect.state} {prospect.zip_code}
DOB: {prospect.date_of_birth}
Monthly Rent: ${monthly_rent}

CREDIT REPORT:
- Credit Score: {credit_report.credit_score}
- Total Debt: ${credit_report.total_debt}
- Monthly Debt Payments: ${credit_report.monthly_debt_payments}
- Repayment History: {credit_report.repayment_history_status}
- Eviction History: {credit_report.has_eviction_history} (count: {credit_report.eviction_count})
- Criminal Record: {credit_report.has_criminal_record}
- Pending Payments: ${credit_report.pending_payments_amount}
- Bankruptcy: {credit_report.bankruptcy_history}

PROOF OF INCOME:
- Employer: {proof_of_income.employer_name}
- Status: {proof_of_income.employment_status}
- Gross Monthly Income: ${proof_of_income.gross_monthly_income}
- Pay Frequency: {proof_of_income.pay_frequency}
- Document Type: {proof_of_income.document_type}
- Verified: {proof_of_income.verified}

PHOTO ID:
- ID Type: {photo_id.id_type}
- Name on ID: {photo_id.name_on_id}
- Address on ID: {photo_id.address_on_id}
- DOB on ID: {photo_id.date_of_birth_on_id}
- Expiration: {photo_id.expiration_date}

ScreeningManager: please coordinate the team and provide a final recommendation."""

    # Set up group chat with all agents
    group_chat = autogen.GroupChat(
        agents=[user_proxy, screening_manager, credit_analyst, income_verifier, identity_checker],
        messages=[],
        max_round=12,
        speaker_selection_method="auto",
    )

    manager = autogen.GroupChatManager(
        groupchat=group_chat,
        llm_config=llm_config,
    )

    # Kick off the conversation
    user_proxy.initiate_chat(manager, message=initial_message)


if __name__ == "__main__":
    screen_prospect(prospect_id=1, monthly_rent=1800.0)
