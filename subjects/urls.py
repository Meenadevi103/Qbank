from django.urls import path
from . import views

app_name = 'subjects'

urlpatterns = [
    path('semester/<int:pk>/', views.semester_detail, name='semester_detail'),
]
