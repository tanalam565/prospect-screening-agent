from django.contrib import admin
from .models import Prospect, CreditReport, ProofOfIncome, PhotoID, RentalApplication, UnitQuote, ScreeningResult, Flag

admin.site.register(Prospect)
admin.site.register(CreditReport)
admin.site.register(ProofOfIncome)
admin.site.register(PhotoID)
admin.site.register(RentalApplication)
admin.site.register(UnitQuote)
admin.site.register(ScreeningResult)
admin.site.register(Flag)
