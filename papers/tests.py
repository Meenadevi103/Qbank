from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from departments.models import Department, Course, Semester
from subjects.models import Subject
from papers.models import QuestionPaper

class PapersViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name='Chemistry')
        self.course = Course.objects.create(department=self.dept, name='B.Sc Chem')
        self.sem = Semester.objects.create(course=self.course, number=1, name='Semester 1')
        self.subject = Subject.objects.create(course=self.course, semester=self.sem, name='Organic Chemistry', code='CHEM101')
        
        pdf_content = b'%PDF-1.4 sample content'
        pdf_file = SimpleUploadedFile('test.pdf', pdf_content, content_type='application/pdf')
        
        self.paper = QuestionPaper.objects.create(
            course=self.course,
            semester=self.sem,
            subject=self.subject,
            academic_year='2023-2024',
            exam_type='End Semester',
            pdf_file=pdf_file
        )

    def test_subject_detail(self):
        response = self.client.get(reverse('papers:subject_detail', args=[self.subject.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '2023-2024')

    def test_view_paper(self):
        response = self.client.get(reverse('papers:view_paper', args=[self.paper.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_download_paper(self):
        response = self.client.get(reverse('papers:download_paper', args=[self.paper.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
