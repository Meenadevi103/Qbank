from django import forms
from departments.models import Department, Course, Semester
from subjects.models import Subject
from papers.models import QuestionPaper

class DashboardBaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'

class DepartmentForm(DashboardBaseForm):
    class Meta:
        model = Department
        fields = ['name']

class CourseForm(DashboardBaseForm):
    class Meta:
        model = Course
        fields = ['department', 'name']

class SemesterForm(DashboardBaseForm):
    class Meta:
        model = Semester
        fields = ['course', 'number', 'name']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].queryset = Course.objects.none()
        # Wait, semesters depend on courses. A course belongs to a department. But the SemesterForm only has 'course' as a ForeignKey.
        # So we can just let 'course' be all courses. Or we could add 'department' as a non-model field to filter courses, but for now we just show all courses.
        self.fields['course'].queryset = Course.objects.all().order_by('name')

class SubjectForm(DashboardBaseForm):
    class Meta:
        model = Subject
        fields = ['course', 'semester', 'name', 'code']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['semester'].queryset = Semester.objects.none()
        
        if 'course' in self.data:
            try:
                course_id = int(self.data.get('course'))
                self.fields['semester'].queryset = Semester.objects.filter(course_id=course_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.course:
            self.fields['semester'].queryset = self.instance.course.semesters.order_by('name')

class QuestionPaperForm(DashboardBaseForm):
    class Meta:
        model = QuestionPaper
        fields = ['course', 'semester', 'subject', 'academic_year', 'exam_type', 'pdf_file']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['semester'].queryset = Semester.objects.none()
        self.fields['subject'].queryset = Subject.objects.none()
        
        if 'course' in self.data:
            try:
                course_id = int(self.data.get('course'))
                self.fields['semester'].queryset = Semester.objects.filter(course_id=course_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.course:
            self.fields['semester'].queryset = self.instance.course.semesters.order_by('name')
            
        if 'semester' in self.data:
            try:
                semester_id = int(self.data.get('semester'))
                self.fields['subject'].queryset = Subject.objects.filter(semester_id=semester_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.semester:
            self.fields['subject'].queryset = self.instance.semester.subjects.order_by('name')
