"""
LangChain experiment: Multi-step applicant screening using sequential LLM chains.
Each chain acts as a specialist agent analyzing one aspect of the applicant.

Install: pip install langchain langchain-ollama
Requires: Ollama running locally (https://ollama.com) with a model pulled e.g. `ollama pull llama3`
"""

import os
import sys
import django

# Add the Django project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Setup Django so we can access models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ApplicantScreener.settings')
django.setup()

from prospect.models import Prospect, CreditReport, ProofOfIncome, PhotoID, ScreeningResult
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Initialize LLM — change model to any model you have pulled in Ollama
# Run `ollama list` to see available models
llm = ChatOllama(model="llama3", temperature=0)
parser = StrOutputParser()


# ── Agent 1: Credit Analyst ──────────────────────────────────────────────────
def analyze_credit(credit_report):
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a credit analyst specializing in rental applicant screening.
Analyze the credit report and return a structured assessment with:
- risk_level: low / medium / high
- key_concerns: list of issues found
- summary: one paragraph conclusion"""),
        ("human", """Analyze this credit report:
Credit Score: {credit_score}
Total Debt: ${total_debt}
Monthly Debt Payments: ${monthly_debt_payments}
Repayment History: {repayment_history}
Eviction History: {has_eviction} (count: {eviction_count})
Criminal Record: {has_criminal}
Pending Payments: ${pending_payments}
Bankruptcy History: {bankruptcy}"""),
    ])

    chain = prompt | llm | parser
    return chain.invoke({
        "credit_score": credit_report.credit_score,
        "total_debt": credit_report.total_debt,
        "monthly_debt_payments": credit_report.monthly_debt_payments,
        "repayment_history": credit_report.repayment_history_status,
        "has_eviction": credit_report.has_eviction_history,
        "eviction_count": credit_report.eviction_count,
        "has_criminal": credit_report.has_criminal_record,
        "pending_payments": credit_report.pending_payments_amount,
        "bankruptcy": credit_report.bankruptcy_history,
    })


# ── Agent 2: Income Verifier ─────────────────────────────────────────────────
def analyze_income(proof_of_income, monthly_rent):
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an income verification specialist.
Check if the applicant meets the income requirement (gross income must be at least 3x monthly rent).
Flag if debt-to-income ratio exceeds 35%.
Return:
- income_sufficient: yes / no
- dti_ratio: calculated percentage
- key_concerns: list of issues
- summary: one paragraph conclusion"""),
        ("human", """Verify this income information:
Employer: {employer}
Employment Status: {employment_status}
Gross Monthly Income: ${gross_monthly_income}
Pay Frequency: {pay_frequency}
Document Type: {document_type}
Verified: {verified}
Monthly Rent: ${monthly_rent}"""),
    ])

    chain = prompt | llm | parser
    return chain.invoke({
        "employer": proof_of_income.employer_name,
        "employment_status": proof_of_income.employment_status,
        "gross_monthly_income": proof_of_income.gross_monthly_income,
        "pay_frequency": proof_of_income.pay_frequency,
        "document_type": proof_of_income.document_type,
        "verified": proof_of_income.verified,
        "monthly_rent": monthly_rent,
    })


# ── Agent 3: Identity Checker ────────────────────────────────────────────────
def analyze_identity(prospect, photo_id):
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an identity verification specialist.
Check for consistency between the applicant's personal information and their photo ID.
Flag any mismatches in name, address, or date of birth.
Return:
- identity_verified: yes / no
- mismatches: list of discrepancies found
- summary: one paragraph conclusion"""),
        ("human", """Check identity consistency:

Applicant Info:
- Name: {prospect_name}
- Address: {prospect_address}
- DOB: {prospect_dob}

Photo ID:
- ID Type: {id_type}
- Name on ID: {name_on_id}
- Address on ID: {address_on_id}
- DOB on ID: {dob_on_id}
- Expiration Date: {expiration_date}"""),
    ])

    chain = prompt | llm | parser
    return chain.invoke({
        "prospect_name": f"{prospect.first_name} {prospect.last_name}",
        "prospect_address": f"{prospect.current_address}, {prospect.city}, {prospect.state}",
        "prospect_dob": prospect.date_of_birth,
        "id_type": photo_id.id_type,
        "name_on_id": photo_id.name_on_id,
        "address_on_id": photo_id.address_on_id,
        "dob_on_id": photo_id.date_of_birth_on_id,
        "expiration_date": photo_id.expiration_date,
    })


# ── Agent 4: Screening Manager (Final Recommendation) ───────────────────────
def make_recommendation(credit_analysis, income_analysis, identity_analysis):
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a senior rental screening manager.
Based on the reports from the credit analyst, income verifier, and identity checker,
make a final decision.
Return:
- recommendation: approve / deny / conditional
- overall_risk_level: low / medium / high
- reasons: list of key reasons for the decision
- conditions: any conditions if recommendation is conditional
- final_summary: one paragraph explanation"""),
        ("human", """Review these specialist reports and make a final recommendation:

CREDIT ANALYSIS:
{credit_analysis}

INCOME ANALYSIS:
{income_analysis}

IDENTITY ANALYSIS:
{identity_analysis}"""),
    ])

    chain = prompt | llm | parser
    return chain.invoke({
        "credit_analysis": credit_analysis,
        "income_analysis": income_analysis,
        "identity_analysis": identity_analysis,
    })


# ── Main: Run the full screening pipeline ───────────────────────────────────
def screen_prospect(prospect_id, monthly_rent=1800):
    print(f"\n{'='*60}")
    print(f"SCREENING PROSPECT ID: {prospect_id}")
    print(f"{'='*60}\n")

    prospect = Prospect.objects.get(id=prospect_id)
    credit_report = CreditReport.objects.filter(prospect=prospect).first()
    proof_of_income = ProofOfIncome.objects.filter(prospect=prospect).first()
    photo_id = PhotoID.objects.filter(prospect=prospect).first()

    print(f"Applicant: {prospect.first_name} {prospect.last_name}\n")

    print("── Agent 1: Analyzing Credit Report...")
    credit_analysis = analyze_credit(credit_report)
    print(credit_analysis)

    print("\n── Agent 2: Verifying Income...")
    income_analysis = analyze_income(proof_of_income, monthly_rent)
    print(income_analysis)

    print("\n── Agent 3: Checking Identity...")
    identity_analysis = analyze_identity(prospect, photo_id)
    print(identity_analysis)

    print("\n── Agent 4: Making Final Recommendation...")
    recommendation = make_recommendation(credit_analysis, income_analysis, identity_analysis)
    print(recommendation)

    print(f"\n{'='*60}\n")
    return recommendation


if __name__ == "__main__":
    screen_prospect(prospect_id=1, monthly_rent=1800)
