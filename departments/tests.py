from django.test import TestCase, Client
from django.urls import reverse
from departments.models import Department, Course, Semester

class DepartmentsViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name='Physics')
        self.course = Course.objects.create(department=self.dept, name='B.Sc Physics')
        self.sem = Semester.objects.create(course=self.course, number=1, name='Semester 1')

    def test_department_list(self):
        response = self.client.get(reverse('departments:department_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Physics')

    def test_department_detail(self):
        response = self.client.get(reverse('departments:department_detail', args=[self.dept.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'B.Sc Physics')

    def test_course_detail(self):
        response = self.client.get(reverse('departments:course_detail', args=[self.course.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Semester 1')
