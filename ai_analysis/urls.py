from django.urls import path
from . import views

app_name = 'ai_analysis'

urlpatterns = [
    path('analyze/<int:subject_id>/', views.analyze_subject, name='analyze_subject'),
]
