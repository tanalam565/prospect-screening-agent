"""
BeeAI experiment: Multi-agent applicant screening using BeeAI framework.
Each agent is a ReActAgent with a specific role. Agents run sequentially,
passing their output as context to the next agent.

Install: pip install beeai-framework
Requires: Ollama running locally with a model pulled e.g. `ollama pull llama3`
"""

import os
import sys
import django
import asyncio

# Add the Django project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Setup Django so we can access models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ApplicantScreener.settings')
django.setup()

from prospect.models import Prospect, CreditReport, ProofOfIncome, PhotoID
from beeai_framework.adapters.ollama.backend.chat import OllamaChatModel
from beeai_framework.agents.bee.agent import BeeAgent
from beeai_framework.agents.types import BeeInput, BeeRunInput, AgentMeta
from beeai_framework.memory import UnconstrainedMemory

# ── Initialize LLM via BeeAI Ollama adapter ──────────────────────────────────
llm = OllamaChatModel("llama3")


# ── Helper: run an agent with a prompt ──────────────────────────────────────
async def run_agent(name: str, description: str, user_prompt: str) -> str:
    agent = BeeAgent(
        BeeInput(
            llm=llm,
            tools=[],
            memory=UnconstrainedMemory(),
            meta=AgentMeta(name=name, description=description, tools=[]),
        )
    )
    response = await agent.run(BeeRunInput(prompt=user_prompt))
    return response.result.text


# ── Agent 1: Credit Analyst ──────────────────────────────────────────────────
async def analyze_credit(credit_report) -> str:
    print("── Agent 1: Analyzing Credit Report...")
    user_prompt = f"""Analyze this credit report:
Credit Score: {credit_report.credit_score}
Total Debt: ${credit_report.total_debt}
Monthly Debt Payments: ${credit_report.monthly_debt_payments}
Repayment History: {credit_report.repayment_history_status}
Eviction History: {credit_report.has_eviction_history} (count: {credit_report.eviction_count})
Criminal Record: {credit_report.has_criminal_record}
Pending Payments: ${credit_report.pending_payments_amount}
Bankruptcy: {credit_report.bankruptcy_history}"""

    return await run_agent(
        "CreditAnalyst",
        "You are a credit analyst specializing in rental applicant screening. Analyze the credit report and return: risk_level (low/medium/high), key_concerns (list of issues), summary (one paragraph conclusion).",
        user_prompt,
    )


# ── Agent 2: Income Verifier ─────────────────────────────────────────────────
async def analyze_income(proof_of_income, monthly_rent: float) -> str:
    print("── Agent 2: Verifying Income...")
    user_prompt = f"""Verify this income:
Employer: {proof_of_income.employer_name}
Employment Status: {proof_of_income.employment_status}
Gross Monthly Income: ${proof_of_income.gross_monthly_income}
Pay Frequency: {proof_of_income.pay_frequency}
Document Type: {proof_of_income.document_type}
Verified: {proof_of_income.verified}
Monthly Rent: ${monthly_rent}
Required Income (3x rent): ${monthly_rent * 3}"""

    return await run_agent(
        "IncomeVerifier",
        "You are an income verification specialist. Check if gross income is at least 3x the monthly rent. Flag DTI above 35%. Return: income_sufficient (yes/no), dti_assessment (pass/flag), key_concerns (list), summary (one paragraph).",
        user_prompt,
    )


# ── Agent 3: Identity Checker ────────────────────────────────────────────────
async def analyze_identity(prospect, photo_id) -> str:
    print("── Agent 3: Checking Identity...")
    user_prompt = f"""Check identity consistency:
Applicant Name: {prospect.first_name} {prospect.last_name}
Applicant Address: {prospect.current_address}, {prospect.city}, {prospect.state}
Applicant DOB: {prospect.date_of_birth}

ID Type: {photo_id.id_type}
Name on ID: {photo_id.name_on_id}
Address on ID: {photo_id.address_on_id}
DOB on ID: {photo_id.date_of_birth_on_id}
Expiration: {photo_id.expiration_date}"""

    return await run_agent(
        "IdentityChecker",
        "You are an identity verification specialist. Check for consistency between the applicant's personal info and photo ID. Return: identity_verified (yes/no), mismatches (list of discrepancies), summary (one paragraph).",
        user_prompt,
    )


# ── Agent 4: Screening Manager ───────────────────────────────────────────────
async def make_recommendation(credit_analysis: str, income_analysis: str, identity_analysis: str) -> str:
    print("── Agent 4: Making Final Recommendation...")
    user_prompt = f"""Review these reports and make a final recommendation:

CREDIT ANALYSIS:
{credit_analysis}

INCOME ANALYSIS:
{income_analysis}

IDENTITY ANALYSIS:
{identity_analysis}"""

    return await run_agent(
        "ScreeningManager",
        "You are a senior rental screening manager. Based on all specialist reports, make a final decision. Return: recommendation (approve/deny/conditional), overall_risk_level (low/medium/high), reasons, conditions (if conditional), final_summary.",
        user_prompt,
    )


# ── Main ─────────────────────────────────────────────────────────────────────
async def screen_prospect(prospect_id: int, monthly_rent: float = 1800.0):
    from asgiref.sync import sync_to_async

    prospect = await sync_to_async(Prospect.objects.get)(id=prospect_id)
    credit_report = await sync_to_async(CreditReport.objects.filter(prospect=prospect).first)()
    proof_of_income = await sync_to_async(ProofOfIncome.objects.filter(prospect=prospect).first)()
    photo_id = await sync_to_async(PhotoID.objects.filter(prospect=prospect).first)()

    print(f"\n{'='*60}")
    print(f"BEEAI SCREENING: {prospect.first_name} {prospect.last_name}")
    print(f"{'='*60}\n")

    credit_analysis = await analyze_credit(credit_report)
    print(credit_analysis)

    income_analysis = await analyze_income(proof_of_income, monthly_rent)
    print(income_analysis)

    identity_analysis = await analyze_identity(prospect, photo_id)
    print(identity_analysis)

    recommendation = await make_recommendation(credit_analysis, income_analysis, identity_analysis)

    print(f"\n{'='*60}")
    print("FINAL RECOMMENDATION:")
    print(f"{'='*60}")
    print(recommendation)

    return recommendation


if __name__ == "__main__":
    asyncio.run(screen_prospect(prospect_id=1, monthly_rent=1800.0))
