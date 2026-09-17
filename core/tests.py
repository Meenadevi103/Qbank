from django.test import TestCase, Client
from django.urls import reverse
from departments.models import Department, Course, Semester
from subjects.models import Subject
from papers.models import QuestionPaper

class CoreViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name='Computer Science')
        self.course = Course.objects.create(department=self.dept, name='BCA')
        self.sem = Semester.objects.create(course=self.course, number=1, name='Semester 1')
        self.subject = Subject.objects.create(course=self.course, semester=self.sem, name='Data Structures', code='CS101')
        self.paper = QuestionPaper.objects.create(
            course=self.course,
            semester=self.sem,
            subject=self.subject,
            academic_year='2023-2024',
            exam_type='End Semester'
        )

    def test_home_view(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Computer Science')

    def test_search_view_with_results(self):
        response = self.client.get(reverse('core:search') + '?q=Data')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Data Structures')

    def test_search_view_empty_query(self):
        response = self.client.get(reverse('core:search'))
        self.assertEqual(response.status_code, 200)
