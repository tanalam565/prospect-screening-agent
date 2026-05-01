The screening process is conducted by using the following documents:
=> Credit Report
=> Proof of Income
=> Photo ID
=> Rental Verification/application
=> Quote of Unit

The credit report report shows the prospect's credit history including debth, repayment history, credit score, eviction, criminal records, and pending payments.

The proof of income is a valid document from the employer of the prospect validating present occupation, salary/wage, and ability to pay the rent.

Photo ID includes, ID, passport, green card, and any valid photo ID issued by government

Rental application document contains info of the prospect.

Quote of Unit is the amount to lease the appartment.

Data collected from these documents, can be used for spotting potential flags:
        => Address mismatch
        => Name mismatch
        => High depth to income ratio
        => Bad repayment history
        => Any reasonable case that predicts the prospects inability to pay rent

=============================== DATA FIELDS =============================
**Prospect**

first_name, last_name, middle_name
date_of_birth
ssn (encrypted)
email, phone
current_address, city, state, zip
created_at, updated_at

**CreditReport**

prospect (FK)
report_date
credit_score
total_debt
monthly_debt_payments
repayment_history_status (good/fair/poor)
has_eviction_history (bool)
eviction_count
has_criminal_record (bool)
criminal_record_details
pending_payments_amount
bankruptcy_history (bool)
report_file (FileField)

**ProofOfIncome**

prospect (FK)
employer_name
employer_address, employer_phone
occupation/job_title
employment_start_date
employment_status (full-time/part-time/contract)
gross_monthly_income
pay_frequency
document_type (paystub/w2/offer_letter)
document_file (FileField)
verified (bool)

**PhotoID**

prospect (FK)
id_type (driver_license/passport/green_card/state_id)
id_number (encrypted)
issuing_authority
issue_date, expiration_date
name_on_id
address_on_id
date_of_birth_on_id
document_file (FileField)

**RentalApplication**

prospect (FK)
applicant_name
current_address, previous_address
move_in_date_requested
current_landlord_name, current_landlord_contact
reason_for_moving
number_of_occupants
pets (bool/details)
emergency_contact_name, emergency_contact_phone
references (JSON or related model)
document_file (FileField)

**UnitQuote**

prospect (FK)
unit_number
property_name/address
monthly_rent
security_deposit
lease_term_months
lease_start_date, lease_end_date
additional_fees (JSON)
quote_date, quote_expiration

**ScreeningResult**

prospect (FK)
address_mismatch (bool) + details
name_mismatch (bool) + details
debt_to_income_ratio (decimal)
dti_flag (bool)
repayment_history_flag (bool)
ability_to_pay_score
overall_risk_level (low/medium/high)
flags (JSON or related Flag model)
recommendation (approve/deny/conditional)
screened_at, screened_by

**Flag (optional separate model)**

screening_result (FK)
flag_type
severity
description
source_document

*********************** AGENTIC APPROACH ***********************

Multiagent processing:

Agent 1 → analyzes credit report
Agent 2 → analyzes income
Agent 3 → checks identity
Agent 4 → synthesizes and makes recommendation

Frameworks used for experiments:
=> Langchain
=> Langraph
=> CrewAI
=> BeeAI
=> AutoGen

