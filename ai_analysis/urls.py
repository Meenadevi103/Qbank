from django.urls import path
from . import views

app_name = 'ai_analysis'

urlpatterns = [
    path('analyze/<int:subject_id>/', views.analyze_subject, name='analyze_subject'),
    path('download/<int:subject_id>/', views.download_report, name='download_report'),
]
