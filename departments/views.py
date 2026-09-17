from django.shortcuts import render, get_object_or_404
from .models import Department, Course

def department_list(request):
    departments = Department.objects.all().order_by('name')
    return render(request, 'departments/department_list.html', {'departments': departments})

def department_detail(request, pk):
    department = get_object_or_404(Department, pk=pk)
    courses = department.courses.all().order_by('name')
    return render(request, 'departments/department_detail.html', {
        'department': department,
        'courses': courses
    })

def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    semesters = course.semesters.all().order_by('number')
    return render(request, 'departments/course_detail.html', {
        'course': course,
        'semesters': semesters
    })
