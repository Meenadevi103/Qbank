from django.urls import path
from . import views

app_name = 'papers'

urlpatterns = [
    path('subject/<int:pk>/', views.subject_detail, name='subject_detail'),
    path('<int:pk>/view/', views.view_paper, name='view_paper'),
    path('<int:pk>/download/', views.download_paper, name='download_paper'),
]
