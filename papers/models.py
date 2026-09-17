import os
from django.db import models
from departments.models import Course, Semester
from subjects.models import Subject

def paper_upload_path(instance, filename):
    return f'papers/{instance.course.id}/{instance.semester.id}/{instance.subject.id}/{filename}'

class QuestionPaper(models.Model):
    EXAM_TYPE_CHOICES = (
        ('Internal', 'Internal'),
        ('Mid Semester', 'Mid Semester'),
        ('End Semester', 'End Semester'),
        ('Supplementary', 'Supplementary'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='papers')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='papers')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='papers')
    
    academic_year = models.CharField(max_length=20) # e.g., "2023-2024"
    exam_type = models.CharField(max_length=50, choices=EXAM_TYPE_CHOICES, default='End Semester')
    
    pdf_file = models.FileField(upload_to=paper_upload_path)
    upload_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-academic_year']
        
    def __str__(self):
        return f"{self.subject.name} - {self.academic_year} ({self.exam_type})"
