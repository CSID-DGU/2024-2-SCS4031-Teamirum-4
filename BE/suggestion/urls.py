from django.urls import path, include
from .views import *

urlpatterns = [
    path('suggest', SuggestionAPIView.as_view()),
]