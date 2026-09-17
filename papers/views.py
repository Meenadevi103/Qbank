from django.shortcuts import render, get_object_or_404
from django.http import FileResponse, Http404
from subjects.models import Subject
from .models import QuestionPaper

def subject_detail(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    papers = subject.papers.all().order_by('-academic_year')
    return render(request, 'papers/subject_detail.html', {
        'subject': subject,
        'semester': subject.semester,
        'course': subject.course,
        'department': subject.course.department,
        'papers': papers
    })

def view_paper(request, pk):
    paper = get_object_or_404(QuestionPaper, pk=pk)
    if not paper.pdf_file:
        raise Http404("PDF not found")
    
    response = FileResponse(paper.pdf_file.open('rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{paper.subject.name}_{paper.academic_year}.pdf"'
    return response

def download_paper(request, pk):
    paper = get_object_or_404(QuestionPaper, pk=pk)
    if not paper.pdf_file:
        raise Http404("PDF not found")
        
    response = FileResponse(paper.pdf_file.open('rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{paper.subject.name}_{paper.academic_year}.pdf"'
    return response
