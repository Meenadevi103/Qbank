import os
import django
from django.core.files.base import ContentFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qbank.settings')
django.setup()

from departments.models import Department, Course, Semester
from subjects.models import Subject
from papers.models import QuestionPaper

def seed():
    # Departments
    cs, _ = Department.objects.get_or_create(name='Department of Computer Science')
    it, _ = Department.objects.get_or_create(name='Department of Information Technology')
    
    # Courses
    cs_course, _ = Course.objects.get_or_create(department=cs, name='BCA')
    it_course, _ = Course.objects.get_or_create(department=it, name='B.Tech IT')
    
    # Semesters
    sem1, _ = Semester.objects.get_or_create(course=cs_course, number=1, name='Semester 1')
    sem2, _ = Semester.objects.get_or_create(course=cs_course, number=2, name='Semester 2')
    sem3, _ = Semester.objects.get_or_create(course=cs_course, number=3, name='Semester 3')
    
    # Subjects
    os_subj, _ = Subject.objects.get_or_create(course=cs_course, semester=sem3, name='Operating Systems', code='CS301')
    cn_subj, _ = Subject.objects.get_or_create(course=cs_course, semester=sem3, name='Computer Networks', code='CS302')
    db_subj, _ = Subject.objects.get_or_create(course=cs_course, semester=sem2, name='Database Management System', code='CS201')

    # Dummy PDF
    dummy_pdf_content = b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n4 0 obj\n<< /Length 53 >>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(Operating Systems Exam Paper) Tj\nET\nendstream\nendobj\n5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000252 00000 n \n0000000356 00000 n \ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n444\n%%EOF'

    # Papers
    if QuestionPaper.objects.count() == 0:
        p1 = QuestionPaper(course=cs_course, semester=sem3, subject=os_subj, academic_year='2022-2023', exam_type='End Semester')
        p1.pdf_file.save('os_2022.pdf', ContentFile(dummy_pdf_content))
        p1.save()
        
        