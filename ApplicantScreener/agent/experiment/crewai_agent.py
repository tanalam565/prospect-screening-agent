"""
CrewAI experiment: Multi-agent applicant screening using a crew of specialized agents.
Each agent has a defined role, goal, and backstory. They work on tasks sequentially.

Install: pip install crewai langchain-ollama
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
from crewai import Agent, Task, Crew, Process

# CrewAI expects a model string in "provider/model" format for Ollama
LLM = "ollama/llama3"


# ── Define Agents (roles, goals, backstories) ────────────────────────────────
credit_analyst = Agent(
    role="Credit Analyst",
    goal="Analyze the applicant's credit report and identify financial risks",
    backstory="""You are a senior credit analyst with 15 years of experience evaluating 
    rental applicants. You specialize in identifying financial red flags such as 
    eviction history, bankruptcy, and high debt loads.""",
    llm=LLM,
    verbose=True,
)

income_verifier = Agent(
    role="Income Verifier",
    goal="Verify the applicant's proof of income and assess affordability",
    backstory="""You are an income verification specialist. You ensure applicants 
    earn at least 3x the monthly rent and check that their debt-to-income ratio 
    does not exceed 35%.""",
    llm=LLM,
    verbose=True,
)

identity_checker = Agent(
    role="Identity Checker",
    goal="Verify the applicant's identity documents for authenticity and consistency",
    backstory="""You are an identity fraud detection expert. You cross-check personal 
    information against photo ID documents to detect mismatches in name, address, 
    and date of birth.""",
    llm=LLM,
    verbose=True,
)

screening_manager = Agent(
    role="Screening Manager",
    goal="Synthesize all specialist reports and make a final screening recommendation",
    backstory="""You are a senior rental screening manager responsible for final 
    approve/deny/conditional decisions. You weigh credit, income, and identity 
    reports to make fair and consistent decisions.""",
    llm=LLM,
    verbose=True,
)


# ── Build and run the crew ───────────────────────────────────────────────────
def screen_prospect(prospect_id, monthly_rent=1800):
    prospect = Prospect.objects.get(id=prospect_id)
    credit_report = CreditReport.objects.filter(prospect=prospect).first()
    proof_of_income = ProofOfIncome.objects.filter(prospect=prospect).first()
    photo_id = PhotoID.objects.filter(prospect=prospect).first()

    print(f"\n{'='*60}")
    print(f"CREWAI SCREENING: {prospect.first_name} {prospect.last_name}")
    print(f"{'='*60}\n")

    # ── Define Tasks ─────────────────────────────────────────────────────────
    credit_task = Task(
        description=f"""Analyze the following credit report for {prospect.first_name} {prospect.last_name}:

Credit Score: {credit_report.credit_score}
Total Debt: ${credit_report.total_debt}
Monthly Debt Payments: ${credit_report.monthly_debt_payments}
Repayment History: {credit_report.repayment_history_status}
Eviction History: {credit_report.has_eviction_history} (count: {credit_report.eviction_count})
Criminal Record: {credit_report.has_criminal_record}
Pending Payments: ${credit_report.pending_payments_amount}
Bankruptcy: {credit_report.bankruptcy_history}

Return: risk_level (low/medium/high), key_concerns, and a summary.""",
        expected_output="A credit risk assessment with risk_level, key_concerns, and summary.",
        agent=credit_analyst,
    )

    income_task = Task(
        description=f"""Verify the income for {prospect.first_name} {prospect.last_name}:

Employer: {proof_of_income.employer_name}
Employment Status: {proof_of_income.employment_status}
Gross Monthly Income: ${proof_of_income.gross_monthly_income}
Pay Frequency: {proof_of_income.pay_frequency}
Document Type: {proof_of_income.document_type}
Verified: {proof_of_income.verified}
Monthly Rent: ${monthly_rent}

Check: income >= 3x rent (${monthly_rent * 3}). Flag DTI above 35%.
Return: income_sufficient (yes/no), dti_assessment, key_concerns, and summary.""",
        expected_output="An income verification report with income_sufficient, dti_assessment, key_concerns, and summary.",
        agent=income_verifier,
    )

    identity_task = Task(
        description=f"""Check identity consistency for {prospect.first_name} {prospect.last_name}:

Applicant Info:
- Name: {prospect.first_name} {prospect.last_name}
- Address: {prospect.current_address}, {prospect.city}, {prospect.state}
- DOB: {prospect.date_of_birth}

Photo ID:
- ID Type: {photo_id.id_type}
- Name on ID: {photo_id.name_on_id}
- Address on ID: {photo_id.address_on_id}
- DOB on ID: {photo_id.date_of_birth_on_id}
- Expiration: {photo_id.expiration_date}

Return: identity_verified (yes/no), mismatches, and summary.""",
        expected_output="An identity verification report with identity_verified, mismatches, and summary.",
        agent=identity_checker,
    )

    recommendation_task = Task(
        description="""Based on the credit analysis, income verification, and identity check 
reports from your colleagues, make a final screening recommendation.

Return:
- recommendation: approve / deny / conditional
- overall_risk_level: low / medium / high  
- reasons: key reasons for the decision
- conditions: any conditions if recommendation is conditional
- final_summary: one paragraph explanation""",
        expected_output="A final screening recommendation with recommendation, risk_level, reasons, and summary.",
        agent=screening_manager,
        context=[credit_task, income_task, identity_task],
    )

    # ── Assemble and run the Crew ─────────────────────────────────────────────
    crew = Crew(
        agents=[credit_analyst, income_verifier, identity_checker, screening_manager],
        tasks=[credit_task, income_task, identity_task, recommendation_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    print(f"\n{'='*60}")
    print("FINAL RECOMMENDATION:")
    print(f"{'='*60}")
    print(result)
    return result


if __name__ == "__main__":
    screen_prospect(prospect_id=1, monthly_rent=1800)
