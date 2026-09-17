from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),
    
    # Departments
    path('departments/', views.departments, name='departments'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:pk>/update/', views.department_update, name='department_update'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    
    # Courses
    path('courses/', views.courses, name='courses'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:pk>/update/', views.course_update, name='course_update'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),
    
    # Semesters
    path('semesters/', views.semesters, name='semesters'),
    path('semesters/create/', views.semester_create, name='semester_create'),
    path('semesters/<int:pk>/update/', views.semester_update, name='semester_update'),
    path('semesters/<int:pk>/delete/', views.semester_delete, name='semester_delete'),
    
    # Subjects
    path('subjects/', views.subjects, name='subjects'),
    path('subjects/create/', views.subject_create, name='subject_create'),
    path('subjects/<int:pk>/update/', views.subject_update, name='subject_update'),
    path('subjects/<int:pk>/delete/', views.subject_delete, name='subject_delete'),
    
    # Question Papers
    path('papers/', views.papers, name='papers'),
    path('papers/create/', views.paper_create, name='paper_create'),
    path('papers/<int:pk>/update/', views.paper_update, name='paper_update'),
    path('papers/<int:pk>/delete/', views.paper_delete, name='paper_delete'),
    
    # AJAX
    path('ajax/get-courses/', views.get_courses, name='get_courses'),
    path('ajax/get-semesters/', views.get_semesters, name='get_semesters'),
    path('ajax/get-subjects/', views.get_subjects, name='get_subjects'),
]
