"""
Models for the residents app, representing prospects, credit reports, proof of income, 
photo IDs, rental applications, unit quotes, screening results, and flags.
"""
from django.db import models


class Prospect(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField()
    ssn = models.CharField(max_length=255) 
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    current_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    

class CreditReport(models.Model):
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE)
    report_date = models.DateField()
    credit_score = models.IntegerField()
    total_debt = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_debt_payments = models.DecimalField(max_digits=10, decimal_places=2)
    repayment_history_status = models.CharField(max_length=20)  # good/fair/poor
    has_eviction_history = models.BooleanField()
    eviction_count = models.IntegerField(default=0)
    has_criminal_record = models.BooleanField()
    criminal_record_details = models.TextField(blank=True, null=True)
    pending_payments_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bankruptcy_history = models.BooleanField()
    report_file = models.FileField(upload_to='credit_reports/')


class ProofOfIncome(models.Model):
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE)
    employer_name = models.CharField(max_length=255)
    employer_address = models.CharField(max_length=255)
    employer_phone = models.CharField(max_length=20)
    occupation = models.CharField(max_length=255)
    employment_start_date = models.DateField()
    employment_status = models.CharField(max_length=20)  # full-time/part-time/contract
    gross_monthly_income = models.DecimalField(max_digits=10, decimal_places=2)
    pay_frequency = models.CharField(max_length=20)  # weekly/biweekly/monthly
    document_type = models.CharField(max_length=50)  # paystub/w2/offer_letter
    document_file = models.FileField(upload_to='proof_of_income/')
    verified = models.BooleanField(default=False)



class PhotoID(models.Model):
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE)
    id_type = models.CharField(max_length=50)  # driver_license/passport/green_card/state_id
    id_number = models.CharField(max_length=255, primary_key=True)  # Store encrypted ID number
    issuing_authority = models.CharField(max_length=255)
    issue_date = models.DateField()
    expiration_date = models.DateField()
    name_on_id = models.CharField(max_length=255)
    address_on_id = models.CharField(max_length=255)
    date_of_birth_on_id = models.DateField()
    document_file = models.FileField(upload_to='photo_ids/')


class RentalApplication(models.Model):
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE)
    applicant_name = models.CharField(max_length=255)
    current_address = models.CharField(max_length=255)
    previous_address = models.CharField(max_length=255, blank=True, null=True)
    move_in_date_requested = models.DateField()
    current_landlord_name = models.CharField(max_length=255)
    current_landlord_contact = models.CharField(max_length=20)
    reason_for_moving = models.TextField()
    number_of_occupants = models.IntegerField()
    pets = models.BooleanField()
    pet_details = models.TextField(blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=255)
    emergency_contact_phone = models.CharField(max_length=20)
    references = models.JSONField(blank=True, null=True)  # Store references as JSON
    document_file = models.FileField(upload_to='rental_applications/')


class UnitQuote(models.Model):
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE)
    unit_number = models.CharField(max_length=50)
    property_name = models.CharField(max_length=255)
    property_address = models.CharField(max_length=255)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2)
    lease_term_months = models.IntegerField()
    lease_start_date = models.DateField()
    lease_end_date = models.DateField()
    additional_fees = models.JSONField(blank=True, null=True)  # Store additional fees as JSON
    quote_date = models.DateField(auto_now_add=True)
    quote_expiration = models.DateField()


class ScreeningResult(models.Model):
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE)
    address_mismatch = models.BooleanField()
    address_mismatch_details = models.TextField(blank=True, null=True)
    name_mismatch = models.BooleanField()
    name_mismatch_details = models.TextField(blank=True, null=True)
    debt_to_income_ratio = models.DecimalField(max_digits=5, decimal_places=2)
    dti_flag = models.BooleanField()
    repayment_history_flag = models.BooleanField()
    ability_to_pay_score = models.DecimalField(max_digits=5, decimal_places=2)
    overall_risk_level = models.CharField(max_length=20)  # low/medium/high
    recommendation = models.CharField(max_length=20)  # approve/deny/conditional
    screened_at = models.DateTimeField(auto_now_add=True)
    screened_by = models.CharField(max_length=255)


class Flag(models.Model):
    screening_result = models.ForeignKey(ScreeningResult, on_delete=models.CASCADE)
    flag_type = models.CharField(max_length=50)
    severity = models.CharField(max_length=20)  # low/medium/high
    description = models.TextField()
    source_document = models.CharField(max_length=255)

# erDiagram
#     Prospect {
#         int id PK
#         string first_name
#         string last_name
#         string middle_name
#         date date_of_birth
#         string ssn
#         string email
#         string phone
#         string current_address
#         string city
#         string state
#         string zip_code
#         datetime created_at
#         datetime updated_at
#     }

#     CreditReport {
#         int id PK
#         int prospect_id FK
#         date report_date
#         int credit_score
#         decimal total_debt
#         decimal monthly_debt_payments
#         string repayment_history_status
#         bool has_eviction_history
#         int eviction_count
#         bool has_criminal_record
#         text criminal_record_details
#         decimal pending_payments_amount
#         bool bankruptcy_history
#         file report_file
#     }

#     ProofOfIncome {
#         int id PK
#         int prospect_id FK
#         string employer_name
#         string employer_address
#         string employer_phone
#         string occupation
#         date employment_start_date
#         string employment_status
#         decimal gross_monthly_income
#         string pay_frequency
#         string document_type
#         file document_file
#         bool verified
#     }

#     PhotoID {
#         string id_number PK
#         int prospect_id FK
#         string id_type
#         string issuing_authority
#         date issue_date
#         date expiration_date
#         string name_on_id
#         string address_on_id
#         date date_of_birth_on_id
#         file document_file
#     }

#     RentalApplication {
#         int id PK
#         int prospect_id FK
#         string applicant_name
#         string current_address
#         string previous_address
#         date move_in_date_requested
#         string current_landlord_name
#         string current_landlord_contact
#         text reason_for_moving
#         int number_of_occupants
#         bool pets
#         text pet_details
#         string emergency_contact_name
#         string emergency_contact_phone
#         json references
#         file document_file
#     }

#     UnitQuote {
#         int id PK
#         int prospect_id FK
#         string unit_number
#         string property_name
#         string property_address
#         decimal monthly_rent
#         decimal security_deposit
#         int lease_term_months
#         date lease_start_date
#         date lease_end_date
#         json additional_fees
#         date quote_date
#         date quote_expiration
#     }

#     ScreeningResult {
#         int id PK
#         int prospect_id FK
#         bool address_mismatch
#         text address_mismatch_details
#         bool name_mismatch
#         text name_mismatch_details
#         decimal debt_to_income_ratio
#         bool dti_flag
#         bool repayment_history_flag
#         decimal ability_to_pay_score
#         string overall_risk_level
#         json flags
#         string recommendation
#         datetime screened_at
#         string screened_by
#     }

#     Prospect ||--o{ CreditReport : "has"
#     Prospect ||--o{ ProofOfIncome : "has"
#     Prospect ||--o{ PhotoID : "has"
#     Prospect ||--o{ RentalApplication : "has"
#     Prospect ||--o{ UnitQuote : "has"
#     Prospect ||--o{ ScreeningResult : "has"