from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import Prospect, CreditReport, ProofOfIncome, PhotoID, ScreeningResult, Flag

# This is function based view, we can also use class based views for better structure and reusability
# def prospect_list(request):
#     prospects = Prospect.objects.all()
#     return render(request, 'prospect/prospect_list.html', {'prospects': prospects})

# def prospect_detail(request, prospect_id):
#     prospect = Prospect.objects.get(id=prospect_id)
#     credit_report = CreditReport.objects.filter(prospect=prospect).first()
#     proof_of_income = ProofOfIncome.objects.filter(prospect=prospect).first()
#     photo_id = PhotoID.objects.filter(prospect=prospect).first()
#     screening_result = ScreeningResult.objects.filter(prospect=prospect).first()
#     flags = Flag.objects.filter(screening_result=screening_result)

#     context = {
#         'prospect': prospect,
#         'credit_report': credit_report,
#         'proof_of_income': proof_of_income,
#         'photo_id': photo_id,
#         'screening_result': screening_result,
#         'flags': flags,
#     }
#     return render(request, 'prospect/prospect_detail.html', context)


# Class based views can be implemented as follows:
class ProspectListView(ListView):
    model = Prospect
    template_name = 'prospect/prospect_list.html'
    context_object_name = 'prospects' # This will be the variable name used in the template to access the list of prospects


class ProspectDetailView(DetailView):
    model = Prospect
    template_name = 'prospect/prospect_detail.html'
    pk_url_kwarg = 'prospect_id' # This tells the view to look for 'prospect_id' in the URL to fetch the specific Prospect object
    context_object_name = 'prospect' # This will be the variable name used in the template to access the specific prospect object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prospect = self.object
        screening_result = ScreeningResult.objects.filter(prospect=prospect).first()
        context['credit_report'] = CreditReport.objects.filter(prospect=prospect).first()
        context['proof_of_income'] = ProofOfIncome.objects.filter(prospect=prospect).first()
        context['photo_id'] = PhotoID.objects.filter(prospect=prospect).first()
        context['screening_result'] = screening_result
        context['flags'] = Flag.objects.filter(screening_result=screening_result)
        return context
