from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from prospect.models import (
    Prospect, CreditReport, ProofOfIncome, PhotoID,
    RentalApplication, UnitQuote, ScreeningResult, Flag
)


class Command(BaseCommand):
    help = 'Seed the database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        # --- Prospect 1: John Smith (approved) ---
        john = Prospect.objects.create(
            first_name='John',
            last_name='Smith',
            middle_name='A',
            date_of_birth=date(1990, 5, 15),
            ssn='123-45-6789',
            email='john.smith@email.com',
            phone='555-101-2020',
            current_address='123 Main St',
            city='Austin',
            state='TX',
            zip_code='78701',
        )

        CreditReport.objects.create(
            prospect=john,
            report_date=date(2026, 4, 1),
            credit_score=720,
            total_debt=5000.00,
            monthly_debt_payments=300.00,
            repayment_history_status='good',
            has_eviction_history=False,
            eviction_count=0,
            has_criminal_record=False,
            pending_payments_amount=0,
            bankruptcy_history=False,
            report_file='',
        )

        ProofOfIncome.objects.create(
            prospect=john,
            employer_name='Acme Corp',
            employer_address='456 Corp Ave, Austin, TX',
            employer_phone='555-200-3000',
            occupation='Software Engineer',
            employment_start_date=date(2020, 1, 10),
            employment_status='full-time',
            gross_monthly_income=7000.00,
            pay_frequency='biweekly',
            document_type='paystub',
            document_file='',
            verified=True,
        )

        PhotoID.objects.create(
            prospect=john,
            id_type='driver_license',
            id_number='DL-JOHN-001',
            issuing_authority='Texas DPS',
            issue_date=date(2020, 3, 1),
            expiration_date=date(2028, 3, 1),
            name_on_id='John A Smith',
            address_on_id='123 Main St, Austin, TX',
            date_of_birth_on_id=date(1990, 5, 15),
            document_file='',
        )

        RentalApplication.objects.create(
            prospect=john,
            applicant_name='John Smith',
            current_address='123 Main St, Austin, TX',
            move_in_date_requested=date(2026, 6, 1),
            current_landlord_name='Bob Landlord',
            current_landlord_contact='555-999-8888',
            reason_for_moving='Closer to work',
            number_of_occupants=2,
            pets=False,
            emergency_contact_name='Jane Smith',
            emergency_contact_phone='555-111-2222',
            references=[{'name': 'Alice Brown', 'phone': '555-333-4444'}],
            document_file='',
        )

        UnitQuote.objects.create(
            prospect=john,
            unit_number='A101',
            property_name='Sunset Apartments',
            property_address='789 Sunset Blvd, Austin, TX',
            monthly_rent=1800.00,
            security_deposit=1800.00,
            lease_term_months=12,
            lease_start_date=date(2026, 6, 1),
            lease_end_date=date(2027, 5, 31),
            additional_fees={'parking': 50, 'pet_fee': 0},
            quote_expiration=date(2026, 5, 15),
        )

        john_screening = ScreeningResult.objects.create(
            prospect=john,
            address_mismatch=False,
            name_mismatch=False,
            debt_to_income_ratio=8.57,
            dti_flag=False,
            repayment_history_flag=False,
            ability_to_pay_score=92.00,
            overall_risk_level='low',
            recommendation='approve',
            screened_by='admin',
        )

        # --- Prospect 2: Sara Lee (denied) ---
        sara = Prospect.objects.create(
            first_name='Sara',
            last_name='Lee',
            date_of_birth=date(1985, 8, 22),
            ssn='987-65-4321',
            email='sara.lee@email.com',
            phone='555-202-3030',
            current_address='456 Oak Ave',
            city='Dallas',
            state='TX',
            zip_code='75201',
        )

        CreditReport.objects.create(
            prospect=sara,
            report_date=date(2026, 4, 5),
            credit_score=580,
            total_debt=12000.00,
            monthly_debt_payments=800.00,
            repayment_history_status='poor',
            has_eviction_history=True,
            eviction_count=1,
            has_criminal_record=False,
            criminal_record_details=None,
            pending_payments_amount=500.00,
            bankruptcy_history=False,
            report_file='',
        )

        ProofOfIncome.objects.create(
            prospect=sara,
            employer_name='Tech Inc',
            employer_address='100 Tech Park, Dallas, TX',
            employer_phone='555-400-5000',
            occupation='Support Specialist',
            employment_start_date=date(2022, 6, 1),
            employment_status='part-time',
            gross_monthly_income=3200.00,
            pay_frequency='monthly',
            document_type='w2',
            document_file='',
            verified=True,
        )

        PhotoID.objects.create(
            prospect=sara,
            id_type='passport',
            id_number='PP-SARA-002',
            issuing_authority='US State Dept',
            issue_date=date(2019, 1, 15),
            expiration_date=date(2029, 1, 15),
            name_on_id='Sara Lee',
            address_on_id='456 Oak Ave, Dallas, TX',
            date_of_birth_on_id=date(1985, 8, 22),
            document_file='',
        )

        sara_screening = ScreeningResult.objects.create(
            prospect=sara,
            address_mismatch=True,
            address_mismatch_details='ID address does not match application address',
            name_mismatch=False,
            debt_to_income_ratio=45.00,
            dti_flag=True,
            repayment_history_flag=True,
            ability_to_pay_score=42.00,
            overall_risk_level='high',
            recommendation='deny',
            screened_by='admin',
        )

        Flag.objects.create(
            screening_result=sara_screening,
            flag_type='eviction',
            severity='high',
            description='Past eviction record in 2022',
            source_document='credit_report',
        )

        Flag.objects.create(
            screening_result=sara_screening,
            flag_type='debt',
            severity='medium',
            description='Debt-to-income ratio exceeds 40%',
            source_document='proof_of_income',
        )

        # --- Prospect 3: Marcus Johnson (conditional) ---
        marcus = Prospect.objects.create(
            first_name='Marcus',
            last_name='Johnson',
            middle_name='T',
            date_of_birth=date(1995, 3, 10),
            ssn='555-66-7777',
            email='marcus.johnson@email.com',
            phone='555-303-4040',
            current_address='789 Elm Street',
            city='Houston',
            state='TX',
            zip_code='77001',
        )

        CreditReport.objects.create(
            prospect=marcus,
            report_date=date(2026, 4, 10),
            credit_score=640,
            total_debt=8000.00,
            monthly_debt_payments=450.00,
            repayment_history_status='fair',
            has_eviction_history=False,
            eviction_count=0,
            has_criminal_record=False,
            pending_payments_amount=200.00,
            bankruptcy_history=False,
            report_file='',
        )

        ProofOfIncome.objects.create(
            prospect=marcus,
            employer_name='Global Solutions LLC',
            employer_address='200 Business Park, Houston, TX',
            employer_phone='555-600-7000',
            occupation='Marketing Coordinator',
            employment_start_date=date(2023, 3, 15),
            employment_status='full-time',
            gross_monthly_income=4500.00,
            pay_frequency='biweekly',
            document_type='paystub',
            document_file='',
            verified=True,
        )

        PhotoID.objects.create(
            prospect=marcus,
            id_type='state_id',
            id_number='SI-MARCUS-003',
            issuing_authority='Texas DPS',
            issue_date=date(2021, 7, 1),
            expiration_date=date(2027, 7, 1),
            name_on_id='Marcus T Johnson',
            address_on_id='789 Elm Street, Houston, TX',
            date_of_birth_on_id=date(1995, 3, 10),
            document_file='',
        )

        RentalApplication.objects.create(
            prospect=marcus,
            applicant_name='Marcus Johnson',
            current_address='789 Elm Street, Houston, TX',
            move_in_date_requested=date(2026, 7, 1),
            current_landlord_name='Linda Property',
            current_landlord_contact='555-777-8888',
            reason_for_moving='Lease ending',
            number_of_occupants=1,
            pets=True,
            pet_details='One small dog, under 20lbs',
            emergency_contact_name='Carol Johnson',
            emergency_contact_phone='555-222-3333',
            references=[{'name': 'David Green', 'phone': '555-444-5555'}],
            document_file='',
        )

        UnitQuote.objects.create(
            prospect=marcus,
            unit_number='B205',
            property_name='Sunset Apartments',
            property_address='789 Sunset Blvd, Austin, TX',
            monthly_rent=1500.00,
            security_deposit=1500.00,
            lease_term_months=12,
            lease_start_date=date(2026, 7, 1),
            lease_end_date=date(2027, 6, 30),
            additional_fees={'parking': 50, 'pet_fee': 30},
            quote_expiration=date(2026, 5, 20),
        )

        marcus_screening = ScreeningResult.objects.create(
            prospect=marcus,
            address_mismatch=False,
            name_mismatch=False,
            debt_to_income_ratio=28.00,
            dti_flag=False,
            repayment_history_flag=True,
            ability_to_pay_score=65.00,
            overall_risk_level='medium',
            recommendation='conditional',
            screened_by='admin',
        )

        Flag.objects.create(
            screening_result=marcus_screening,
            flag_type='repayment',
            severity='medium',
            description='Fair repayment history with minor late payments',
            source_document='credit_report',
        )

        self.stdout.write(self.style.SUCCESS('Sample data seeded successfully!'))
