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
