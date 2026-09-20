from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse

from departments.models import Department, Course, Semester
from subjects.models import Subject
from papers.models import QuestionPaper
from ai_analysis.models import ExtractionStatus

from .forms import DepartmentForm, CourseForm, SemesterForm, SubjectForm, QuestionPaperForm

@staff_member_required(login_url='/admin-login/')
def home(request):
    total_extracted = ExtractionStatus.objects.filter(status='COMPLETED').count()
    total_failed = ExtractionStatus.objects.filter(status='FAILED').count()
    
    context = {
        'total_departments': Department.objects.count(),
        'total_semesters': Semester.objects.count(),
        'total_subjects': Subject.objects.count(),
        'total_papers': QuestionPaper.objects.count(),
        'total_extracted': total_extracted,
        'total_failed': total_failed,
        'recent_papers': QuestionPaper.objects.select_related(
            'subject', 'extraction_status', 'subject__ai_analysis'
        ).order_by('-upload_date')[:5],
    }
    return render(request, 'dashboard/home.html', context)

from django.core.paginator import Paginator
from django.db.models import Q

# --- DEPARTMENTS ---

@staff_member_required(login_url='/admin-login/')
def departments(request):
    q = request.GET.get('q', '')
    deps = Department.objects.all().order_by('name')
    if q:
        deps = deps.filter(name__icontains=q)
        
    paginator = Paginator(deps, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'departments': page_obj, 'q': q, 'page_obj': page_obj}
    return render(request, 'dashboard/departments.html', context)

@staff_member_required(login_url='/admin-login/')
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Department created successfully.")
            return redirect('dashboard:departments')
    else:
        form = DepartmentForm()
    
    return render(request, 'dashboard/form.html', {
        'form': form, 'action': 'Add', 'entity_name': 'Department', 'cancel_url': reverse('dashboard:departments')
    })

@staff_member_required(login_url='/admin-login/')
def department_update(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, "Department updated successfully.")
            return redirect('dashboard:departments')
    else:
        form = DepartmentForm(instance=department)
    
    return render(request, 'dashboard/form.html', {
        'form': form, 'action': 'Edit', 'entity_name': 'Department', 'cancel_url': reverse('dashboard:departments')
    })

@staff_member_required(login_url='/admin-login/')
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        department.delete()
        messages.success(request, "Department deleted successfully.")
    return redirect('dashboard:departments')

# --- COURSES ---

@staff_member_required(login_url='/admin-login/')
def courses(request):
    q = request.GET.get('q', '')
    course_list = Course.objects.all().select_related('department').order_by('department__name', 'name')
    if q:
        course_list = course_list.filter(Q(name__icontains=q) | Q(department__name__icontains=q))
        
    paginator = Paginator(course_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'courses': page_obj, 'q': q, 'page_obj': page_obj}
    return render(request, 'dashboard/courses.html', context)

@staff_member_required(login_url='/admin-login/')
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Course created successfully.")
            return redirect('dashboard:courses')
    else:
        form = CourseForm()
    
    return render(request, 'dashboard/form.html', {
        'form': form, 'action': 'Add', 'entity_name': 'Course', 'cancel_url': reverse('dashboard:courses')
    })

@staff_member_required(login_url='/admin-login/')
def course_update(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated successfully.")
            return redirect('dashboard:courses')
    else:
        form = CourseForm(instance=course)
    
    return render(request, 'dashboard/form.html', {
        'form': form, 'action': 'Edit', 'entity_name': 'Course', 'cancel_url': reverse('dashboard:courses')
    })

@staff_member_required(login_url='/admin-login/')
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        course.delete()
        messages.success(request, "Course deleted successfully.")
    return redirect('dashboard:courses')

# --- SEMESTERS ---

@staff_member_required(login_url='/admin-login/')
def semesters(request):
    q = request.GET.get('q', '')
    sem_list = Semester.objects.all().select_related('course', 'course__department').order_by('course__name', 'number')
    if q:
        sem_list = sem_list.filter(Q(name__icontains=q) | Q(course__name__icontains=q))
        
    paginator = Paginator(sem_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'semesters': page_obj, 'q': q, 'page_obj': page_obj}
    return render(request, 'dashboard/semesters.html', context)

@staff_member_required(login_url='/admin-login/')
def semester_create(request):
    if request.method == 'POST':
        form = SemesterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Semester created successfully.")
            return redirect('dashboard:semesters')
    else:
        form = SemesterForm()
    
    return render(request, 'dashboard/form.html', {
        'form': form, 'action': 'Add', 'entity_name': 'Semester', 'cancel_url': reverse('dashboard:semesters')
    })

@staff_member_required(login_url='/admin-login/')
def semester_update(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    if request.method == 'POST':
        form = SemesterForm(request.POST, instance=semester)
        if form.is_valid():
            form.save()
            messages.success(request, "Semester updated successfully.")
            return redirect('dashboard:semesters')
    else:
        form = SemesterForm(instance=semester)
    
    return render(request, 'dashboard/form.html', {
        'form': form, 'action': 'Edit', 'entity_name': 'Semester', 'cancel_url': reverse('dashboard:semesters')
    })

@staff_member_required(login_url='/admin-login/')
def semester_delete(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    if request.method == 'POST':
        semester.delete()
        messages.success(request, "Semester deleted successfully.")
    return redirect('dashboard:semesters')


# --- SUBJECTS ---

@staff_member_required(login_url='/admin-login/')
def subjects(request):
    q = request.GET.get('q', '')
    sub_list = Subject.objects.all().select_related('course', 'semester').order_by('name')
    if q:
        sub_list = sub_list.filter(Q(name__icontains=q) | Q(code__icontains=q) | Q(course__name__icontains=q))
        
    paginator = Paginator(sub_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'subjects': page_obj, 'q': q, 'page_obj': page_obj}
    return render(request, 'dashboard/subjects.html', context)

@staff_member_required(login_url='/admin-login/')
def subject_create(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Subject created successfully.")
            return redirect('dashboard:subjects')
    else:
        form = SubjectForm()
    
    return render(request, 'dashboard/form.html', {
        'form': form, 'action': 'Add', 'entity_name': 'Subject', 'cancel_url': reverse('dashboard:subjects')
    })

@staff_member_required(login_url='/admin-login/')
def subject_update(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, "Subject updated successfully.")
            return redirect('dashboard:subjects')
    else:
        form = SubjectForm(instance=subject)
    
    return render(request, 'dashboard/form.html', {
        'form': form, 'action': 'Edit', 'entity_name': 'Subject', 'cancel_url': reverse('dashboard:subjects')
    })

@staff_member_required(login_url='/admin-login/')
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        messages.success(request, "Subject deleted successfully.")
    return redirect('dashboard:subjects')

# --- PAPERS ---

@staff_member_required(login_url='/admin-login/')
def papers(request):
    q = request.GET.get('q', '')
    paper_list = QuestionPaper.objects.all().select_related(
        'subject', 'course', 'semester', 'extraction_status', 'subject__ai_analysis'
    ).order_by('-upload_date')
    if q:
        paper_list = paper_list.filter(Q(subject__name__icontains=q) | Q(academic_year__icontains=q))
        
    paginator = Paginator(paper_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'papers': page_obj, 'q': q, 'page_obj': page_obj}
    return render(request, 'dashboard/papers.html', context)

@staff_member_required(login_url='/admin-login/')
def paper_create(request):
    if request.method == 'POST':
        form = QuestionPaperForm(request.POST, request.FILES)
        if form.is_valid():
            paper = form.save()
            ExtractionStatus.objects.get_or_create(question_paper=paper, defaults={'status': 'PENDING'})
            messages.success(request, "Question Paper uploaded successfully.")
            return redirect('dashboard:papers')
    else:
        form = QuestionPaperForm()
    
    return render(request, 'dashboard/form.html', {
        'form': form, 'action': 'Upload', 'entity_name': 'Question Paper', 'cancel_url': reverse('dashboard:papers')
    })

@staff_member_required(login_url='/admin-login/')
def paper_update(request, pk):
    paper = get_object_or_404(QuestionPaper, pk=pk)
    if request.method == 'POST':
        form = QuestionPaperForm(request.POST, request.FILES, instance=paper)
        if form.is_valid():
            form.save()
            messages.success(request, "Question Paper updated successfully.")
            return redirect('dashboard:papers')
    else:
        form = QuestionPaperForm(instance=paper)
    
    return render(request, 'dashboard/form.html', {
        'form': form, 'action': 'Edit', 'entity_name': 'Question Paper', 'cancel_url': reverse('dashboard:papers')
    })

@staff_member_required(login_url='/admin-login/')
def paper_delete(request, pk):
    paper = get_object_or_404(QuestionPaper, pk=pk)
    if request.method == 'POST':
        paper.delete()
        messages.success(request, "Question Paper deleted successfully.")
    return redirect('dashboard:papers')


@staff_member_required(login_url='/admin-login/')
def settings(request):
    return render(request, 'dashboard/settings.html')

@staff_member_required(login_url='/admin-login/')
def get_courses(request):
    department_id = request.GET.get('department_id')
    courses = Course.objects.filter(department_id=department_id).order_by('name')
    return JsonResponse(list(courses.values('id', 'name')), safe=False)

@staff_member_required(login_url='/admin-login/')
def get_semesters(request):
    course_id = request.GET.get('course_id')
    semesters = Semester.objects.filter(course_id=course_id).order_by('name')
    return JsonResponse(list(semesters.values('id', 'name')), safe=False)

@staff_member_required(login_url='/admin-login/')
def get_subjects(request):
    semester_id = request.GET.get('semester_id')
    subjects = Subject.objects.filter(semester_id=semester_id).order_by('name')
    return JsonResponse(list(subjects.values('id', 'name')), safe=False)
