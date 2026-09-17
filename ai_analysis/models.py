from django.db import models
from papers.models import QuestionPaper
from subjects.models import Subject

class ExtractionStatus(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )
    METHOD_CHOICES = (
        ('NATIVE', 'Native Text (PyMuPDF)'),
        ('OCR', 'OCR (PaddleOCR)'),
        ('MIXED', 'Mixed (Native + OCR)'),
        ('UNKNOWN', 'Unknown'),
    )
    
    question_paper = models.OneToOneField(QuestionPaper, on_delete=models.CASCADE, related_name='extraction_status')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    extraction_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='UNKNOWN')
    pages_processed = models.IntegerField(default=0)
    total_pages = models.IntegerField(default=0)
    questions_extracted = models.IntegerField(default=0)
    character_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.question_paper} - {self.get_status_display()}"


class ExtractedQuestion(models.Model):
    question_paper = models.ForeignKey(QuestionPaper, on_delete=models.CASCADE, related_name='extracted_questions')
    page_number = models.IntegerField(help_text="Page number where this question starts (1-indexed)")
    question_number = models.CharField(max_length=20, help_text="e.g., '1', '13', 'Part A'")
    part = models.CharField(max_length=10, blank=True, null=True, help_text="e.g., 'a', 'b', 'i'")
    question_text = models.TextField()
    raw_text_block = models.TextField(help_text="The exact raw text chunk containing this question")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['page_number', 'id']

    def __str__(self):
        prefix = f"Q{self.question_number}"
        if self.part:
            prefix += f" ({self.part})"
        return f"{self.question_paper} - {prefix}"


class SubjectAnalysisCache(models.Model):
    subject = models.OneToOneField(Subject, on_delete=models.CASCADE, related_name='ai_analysis')
    results_json = models.JSONField(blank=True, null=True, help_text="Stored semantic analysis results")
    last_computed = models.DateTimeField(auto_now=True)
    is_stale = models.BooleanField(default=False, help_text="True if new questions were added since last analysis")

    def __str__(self):
        return f"Analysis Cache: {self.subject.name}"
