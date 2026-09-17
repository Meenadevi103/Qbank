from django.test import TestCase, Client
from django.urls import reverse
from departments.models import Department, Course, Semester
from subjects.models import Subject

class SubjectsViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name='Mathematics')
        self.course = Course.objects.create(department=self.dept, name='B.Sc Math')
        self.sem = Semester.objects.create(course=self.course, number=1, name='Semester 1')
        self.subject = Subject.objects.create(course=self.course, semester=self.sem, name='Calculus', code='MATH101')

    def test_semester_detail(self):
        response = self.client.get(reverse('subjects:semester_detail', args=[self.sem.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Calculus')
