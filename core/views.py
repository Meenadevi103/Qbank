from django.shortcuts import render
from departments.models import Department
from papers.models import QuestionPaper
from django.db.models import Q

def home(request):
    departments = Department.objects.all()
    return render(request, 'home.html', {'departments': departments})

def search(request):
    query = request.GET.get('q', '').strip()
    results = []
    
    if query:
        results = QuestionPaper.objects.filter(
            Q(subject__name__icontains=query) |
            Q(course__department__name__icontains=query) |
            Q(course__name__icontains=query) |
            Q(academic_year__icontains=query) |
            Q(exam_type__icontains=query) |
            Q(semester__name__icontains=query)
        ).select_related('subject', 'semester', 'course', 'course__department')
        
    return render(request, 'search_results.html', {'results': results, 'query': query})

