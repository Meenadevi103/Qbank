from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ExtractedQuestion, SubjectAnalysisCache

@receiver(post_save, sender=ExtractedQuestion)
@receiver(post_delete, sender=ExtractedQuestion)
def invalidate_analysis_cache(sender, instance, **kwargs):
    """
    Invalidates the SubjectAnalysisCache when an ExtractedQuestion is added or deleted.
    """
    subject = instance.question_paper.subject
    try:
        cache = SubjectAnalysisCache.objects.get(subject=subject)
        cache.is_stale = True
        cache.save()
    except SubjectAnalysisCache.DoesNotExist:
        pass
