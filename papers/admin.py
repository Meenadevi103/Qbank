from django.contrib import admin
from .models import QuestionPaper

@admin.register(QuestionPaper)
class QuestionPaperAdmin(admin.ModelAdmin):
    list_display = ('subject', 'academic_year', 'exam_type')
    list_filter = ('exam_type', 'academic_year', 'course', 'semester')
    search_fields = ('subject__name', 'academic_year')

