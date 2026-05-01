from django.urls import path
from .views import ProspectListView, ProspectDetailView

urlpatterns = [
    path('', ProspectListView.as_view(), name='prospect-list'),
    path('<int:prospect_id>/', ProspectDetailView.as_view(), name='prospect-detail'),
]
