from django.urls import path
from . import views

app_name = 'departments'

urlpatterns = [
    path('', views.department_list, name='department_list'),
    path('<int:pk>/', views.department_detail, name='department_detail'),
    path('course/<int:pk>/', views.course_detail, name='course_detail'),
]
