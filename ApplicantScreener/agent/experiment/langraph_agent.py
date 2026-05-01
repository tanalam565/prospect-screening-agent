"""
LangGraph experiment: Multi-agent applicant screening using a state graph.
Each node in the graph is a specialist agent. The graph flows:
  START → credit_node → income_node → identity_node → recommendation_node → END

Install: pip install langgraph langchain langchain-ollama
Requires: Ollama running locally with a model pulled e.g. `ollama pull llama3`
"""

import os
import sys
import django
from typing import TypedDict

# Add the Django project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Setup Django so we can access models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ApplicantScreener.settings')
django.setup()

from prospect.models import Prospect, CreditReport, ProofOfIncome, PhotoID
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END

# Initialize LLM
llm = ChatOllama(model="llama3", temperature=0)
parser = StrOutputParser()


# ── State: shared data passed between all nodes ──────────────────────────────
class ScreeningState(TypedDict):
    prospect_id: int
    monthly_rent: float
    prospect_name: str
    credit_analysis: str
    income_analysis: str
    identity_analysis: str
    final_recommendation: str


# ── Node 1: Credit Analyst ───────────────────────────────────────────────────
def credit_node(state: ScreeningState) -> ScreeningState:
    print("── Node 1: Analyzing Credit Report...")
    prospect = Prospect.objects.get(id=state["prospect_id"])
    credit_report = CreditReport.objects.filter(prospect=prospect).first()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a credit analyst specializing in rental applicant screening.
Analyze the credit report and return:
- risk_level: low / medium / high
- key_concerns: list of issues
- summary: one paragraph conclusion"""),
        ("human", """Credit Score: {credit_score}
Total Debt: ${total_debt}
Monthly Debt Payments: ${monthly_payments}
Repayment History: {repayment_history}
Eviction History: {has_eviction} (count: {eviction_count})
Criminal Record: {has_criminal}
Bankruptcy: {bankruptcy}"""),
    ])

    result = (prompt | llm | parser).invoke({
        "credit_score": credit_report.credit_score,
        "total_debt": credit_report.total_debt,
        "monthly_payments": credit_report.monthly_debt_payments,
        "repayment_history": credit_report.repayment_history_status,
        "has_eviction": credit_report.has_eviction_history,
        "eviction_count": credit_report.eviction_count,
        "has_criminal": credit_report.has_criminal_record,
        "bankruptcy": credit_report.bankruptcy_history,
    })

    return {**state, "credit_analysis": result}


# ── Node 2: Income Verifier ──────────────────────────────────────────────────
def income_node(state: ScreeningState) -> ScreeningState:
    print("── Node 2: Verifying Income...")
    prospect = Prospect.objects.get(id=state["prospect_id"])
    proof_of_income = ProofOfIncome.objects.filter(prospect=prospect).first()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an income verification specialist.
Check if gross income is at least 3x the monthly rent. Flag DTI above 35%.
Return:
- income_sufficient: yes / no
- dti_assessment: pass / flag
- key_concerns: list of issues
- summary: one paragraph conclusion"""),
        ("human", """Employer: {employer}
Employment Status: {employment_status}
Gross Monthly Income: ${gross_monthly_income}
Pay Frequency: {pay_frequency}
Document Verified: {verified}
Monthly Rent: ${monthly_rent}"""),
    ])

    result = (prompt | llm | parser).invoke({
        "employer": proof_of_income.employer_name,
        "employment_status": proof_of_income.employment_status,
        "gross_monthly_income": proof_of_income.gross_monthly_income,
        "pay_frequency": proof_of_income.pay_frequency,
        "verified": proof_of_income.verified,
        "monthly_rent": state["monthly_rent"],
    })

    return {**state, "income_analysis": result}


# ── Node 3: Identity Checker ─────────────────────────────────────────────────
def identity_node(state: ScreeningState) -> ScreeningState:
    print("── Node 3: Checking Identity...")
    prospect = Prospect.objects.get(id=state["prospect_id"])
    photo_id = PhotoID.objects.filter(prospect=prospect).first()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an identity verification specialist.
Check for consistency between the applicant's personal info and their photo ID.
Return:
- identity_verified: yes / no
- mismatches: list of discrepancies
- summary: one paragraph conclusion"""),
        ("human", """Applicant Name: {prospect_name}
Applicant Address: {prospect_address}
Applicant DOB: {prospect_dob}

ID Type: {id_type}
Name on ID: {name_on_id}
Address on ID: {address_on_id}
DOB on ID: {dob_on_id}
Expiration: {expiration_date}"""),
    ])

    result = (prompt | llm | parser).invoke({
        "prospect_name": f"{prospect.first_name} {prospect.last_name}",
        "prospect_address": f"{prospect.current_address}, {prospect.city}, {prospect.state}",
        "prospect_dob": prospect.date_of_birth,
        "id_type": photo_id.id_type,
        "name_on_id": photo_id.name_on_id,
        "address_on_id": photo_id.address_on_id,
        "dob_on_id": photo_id.date_of_birth_on_id,
        "expiration_date": photo_id.expiration_date,
    })

    return {**state, "identity_analysis": result}


# ── Node 4: Screening Manager (Final Recommendation) ────────────────────────
def recommendation_node(state: ScreeningState) -> ScreeningState:
    print("── Node 4: Making Final Recommendation...")

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a senior rental screening manager.
Based on all specialist reports, make a final decision.
Return:
- recommendation: approve / deny / conditional
- overall_risk_level: low / medium / high
- reasons: key reasons for the decision
- final_summary: one paragraph explanation"""),
        ("human", """CREDIT ANALYSIS:
{credit_analysis}

INCOME ANALYSIS:
{income_analysis}

IDENTITY ANALYSIS:
{identity_analysis}"""),
    ])

    result = (prompt | llm | parser).invoke({
        "credit_analysis": state["credit_analysis"],
        "income_analysis": state["income_analysis"],
        "identity_analysis": state["identity_analysis"],
    })

    return {**state, "final_recommendation": result}


# ── Build the Graph ──────────────────────────────────────────────────────────
def build_screening_graph():
    graph = StateGraph(ScreeningState)

    graph.add_node("credit_node", credit_node)
    graph.add_node("income_node", income_node)
    graph.add_node("identity_node", identity_node)
    graph.add_node("recommendation_node", recommendation_node)

    # Define flow: START → credit → income → identity → recommendation → END
    graph.add_edge(START, "credit_node")
    graph.add_edge("credit_node", "income_node")
    graph.add_edge("income_node", "identity_node")
    graph.add_edge("identity_node", "recommendation_node")
    graph.add_edge("recommendation_node", END)

    return graph.compile()


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    prospect = Prospect.objects.get(id=1)

    print(f"\n{'='*60}")
    print(f"LANGGRAPH SCREENING: {prospect.first_name} {prospect.last_name}")
    print(f"{'='*60}\n")

    app = build_screening_graph()

    initial_state = ScreeningState(
        prospect_id=1,
        monthly_rent=1800.0,
        prospect_name=f"{prospect.first_name} {prospect.last_name}",
        credit_analysis="",
        income_analysis="",
        identity_analysis="",
        final_recommendation="",
    )

    final_state = app.invoke(initial_state)

    print(f"\n{'='*60}")
    print("FINAL RECOMMENDATION:")
    print(f"{'='*60}")
    print(final_state["final_recommendation"])
