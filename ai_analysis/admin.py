from django.contrib import admin
from .models import ExtractionStatus, ExtractedQuestion

@admin.register(ExtractionStatus)
class ExtractionStatusAdmin(admin.ModelAdmin):
    list_display = ('question_paper', 'status', 'extraction_method', 'pages_processed', 'questions_extracted', 'updated_at')
    list_filter = ('status', 'extraction_method')
    search_fields = ('question_paper__subject__name',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ExtractedQuestion)
class ExtractedQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_paper', 'page_number', 'question_number', 'part', 'short_text')
    list_filter = ('question_paper__subject__name', 'page_number')
    search_fields = ('question_text', 'question_number')

    def short_text(self, obj):
        return obj.question_text[:100] + '...' if len(obj.question_text) > 100 else obj.question_text
    short_text.short_description = 'Question Text'
