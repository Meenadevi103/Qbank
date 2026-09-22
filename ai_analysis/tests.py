from django.test import TestCase
from ai_analysis.models import ExtractedQuestion, SubjectAnalysisCache
from ai_analysis.parser import parse_questions_from_text
from papers.models import QuestionPaper, Subject, Semester
from ai_analysis.analyzer import perform_semantic_analysis
from departments.models import Course, Department

class AIAnalysisPipelineTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(name='Test Department')
        self.course = Course.objects.create(name='Test Course', department=self.department)
        self.semester = Semester.objects.create(number=1, course=self.course)
        self.subject = Subject.objects.create(name='Test Subject', code='TS101', semester=self.semester, course=self.course)
        self.paper1 = QuestionPaper.objects.create(
            subject=self.subject,
            course=self.course,
            semester=self.semester,
            academic_year='2024',
            exam_type='End Semester'
        )
        self.paper2 = QuestionPaper.objects.create(
            subject=self.subject,
            course=self.course,
            semester=self.semester,
            academic_year='2025',
            exam_type='End Semester'
        )

    def test_parser_splits_or_alternatives_and_assigns_marks(self):
        sample_text = '''
SECTION A
Answer all questions. Each question carries 2 marks.
1. What is Python?
2. Explain inheritance.

SECTION B
Answer any two questions. Each question carries 10 marks.
3. (a) Write a program to sort an array.
[OR]
(b) Explain quicksort algorithm.
        '''
        questions = parse_questions_from_text(sample_text, self.paper1)
        
        self.assertEqual(len(questions), 4)
        self.assertEqual(questions[0]['marks'], '2')
        self.assertEqual(questions[1]['marks'], '2')
        self.assertEqual(questions[2]['marks'], '10')
        self.assertEqual(questions[3]['marks'], '10')
        
        self.assertIn('Write a program to sort an array.', questions[2]['question_text'])
        self.assertIn('Explain quicksort algorithm.', questions[3]['question_text'])

    def test_semantic_analyzer_metrics(self):
        ExtractedQuestion.objects.create(
            question_paper=self.paper1,
            question_number='1',
            question_text='Explain the concept of inheritance in OOP.',
            marks='5',
            page_number=1
        )
        ExtractedQuestion.objects.create(
            question_paper=self.paper2,
            question_number='3',
            question_text='What do you mean by inheritance in OOP?',
            marks='5',
            page_number=1
        )
        ExtractedQuestion.objects.create(
            question_paper=self.paper2,
            question_number='4',
            question_text='Write a python program to add two numbers.',
            marks='2',
            page_number=1
        )
        
        res = perform_semantic_analysis(self.subject.id)
        
        groups = res['groups']
        self.assertEqual(len(groups), 2)
        
        inheritance_group = next(g for g in groups if g['frequency'] == 2)
        unique_group = next(g for g in groups if g['frequency'] == 1)
        
        self.assertEqual(inheritance_group['distinct_papers'], 2)
        self.assertEqual(inheritance_group['distinct_years'], 2)
        self.assertEqual(inheritance_group['frequency'], 2)
        
        self.assertEqual(unique_group['distinct_papers'], 1)
        self.assertEqual(unique_group['distinct_years'], 1)
        self.assertEqual(unique_group['frequency'], 1)
