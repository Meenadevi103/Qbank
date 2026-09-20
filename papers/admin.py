from django.contrib import admin
from django.utils.html import format_html
from .models import QuestionPaper

@admin.register(QuestionPaper)
class QuestionPaperAdmin(admin.ModelAdmin):
    list_display = (
        'subject', 'academic_year', 'exam_type', 'analysis_status',
        'extraction_progress',
    )
    list_filter = ('exam_type', 'academic_year', 'course', 'semester')
    search_fields = ('subject__name', 'academic_year')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'extraction_status', 'subject__ai_analysis'
        )

    @admin.display(description='AI analysis status')
    def analysis_status(self, obj):
        status = getattr(obj, 'extraction_status', None)
        if status is None:
            return 'Queued for extraction'

        if status.status == 'PENDING':
            return 'Queued for extraction'
        if status.status == 'PROCESSING':
            return f'Extracting ({status.pages_processed}/{status.total_pages} pages)'
        if status.status == 'FAILED':
            return 'Extraction failed'

        cache = getattr(obj.subject, 'ai_analysis', None)
        if cache is None:
            return 'Queued for analysis'

        return 'Queued for analysis' if cache.is_stale else 'Analysis ready'

    @admin.display(description='Extraction progress')
    def extraction_progress(self, obj):
        """Show a compact, accessible extraction progress bar in Django admin."""
        status = getattr(obj, 'extraction_status', None)

        if status is None or status.status == 'PENDING':
            percent, label, color = 0, 'Queued', '#6b7280'
        elif status.status == 'PROCESSING':
            total_pages = max(status.total_pages, 1)
            percent = min(100, round(status.pages_processed * 100 / total_pages))
            label = f'Running: {status.pages_processed}/{status.total_pages} pages'
            color = '#2563eb'
        elif status.status == 'FAILED':
            percent, label, color = 100, 'Failed', '#b91c1c'
        else:
            percent, label, color = 100, 'Extraction completed', '#15803d'

        return format_html(
            '<div style="min-width: 180px">'
            '<div style="height: 10px; overflow: hidden; border-radius: 999px; '
            'background: #e5e7eb">'
            '<div role="progressbar" aria-label="{}" aria-valuenow="{}" '
            'aria-valuemin="0" aria-valuemax="100" '
            'style="width: {}%; height: 100%; background: {}"></div>'
            '</div><div style="margin-top: 4px; color: {}; font-size: 12px">'
            '{} ({}%)</div></div>',
            label, percent, percent, color, color, label, percent,
        )
