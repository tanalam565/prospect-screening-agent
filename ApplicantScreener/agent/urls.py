from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot_page, name='chatbot'),
    path('api/chat/', views.chat_api, name='chat-api'),
]
