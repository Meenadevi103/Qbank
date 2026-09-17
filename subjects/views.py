from django.shortcuts import render, get_object_or_404
from departments.models import Semester
from .models import Subject

def semester_detail(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    subjects = semester.subjects.all().order_by('name')
    return render(request, 'subjects/semester_detail.html', {
        'semester': semester,
        'course': semester.course,
        'department': semester.course.department,
        'subjects': subjects
    })
