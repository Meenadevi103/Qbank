from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ExtractedQuestion, SubjectAnalysisCache, ExtractionStatus
from papers.models import QuestionPaper

@receiver(post_save, sender=QuestionPaper)
def queue_paper_for_extraction(sender, instance, created, **kwargs):
    """
    Automatically queues a newly uploaded QuestionPaper for AI extraction.
    """
    if instance.pdf_file:
        _, status_created = ExtractionStatus.objects.get_or_create(
            question_paper=instance,
            defaults={'status': 'PENDING'}
        )
        # A newly queued paper changes the subject-wide analysis.  Creating
        # the cache row here is important: the worker only computes stale
        # caches, so a subject without an earlier cache would otherwise never
        # receive its first analysis.
        if created or status_created:
            SubjectAnalysisCache.objects.update_or_create(
                subject=instance.subject,
                defaults={'is_stale': True},
            )


@receiver(post_delete, sender=QuestionPaper)
def invalidate_deleted_paper_analysis(sender, instance, **kwargs):
    """Queue a fresh subject report when a question paper is removed."""
    SubjectAnalysisCache.objects.update_or_create(
        subject_id=instance.subject_id,
        defaults={'is_stale': True, 'results_json': None},
    )

@receiver(post_save, sender=ExtractedQuestion)
@receiver(post_delete, sender=ExtractedQuestion)
def invalidate_analysis_cache(sender, instance, **kwargs):
    """
    Invalidates the SubjectAnalysisCache when an ExtractedQuestion is added or deleted.
    """
    subject = instance.question_paper.subject
    SubjectAnalysisCache.objects.update_or_create(
        subject=subject,
        defaults={'is_stale': True},
    )
