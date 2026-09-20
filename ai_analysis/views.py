from django.shortcuts import render
from django.http import JsonResponse
from .analyzer import get_cached_analysis
from papers.models import QuestionPaper
from ai_analysis.models import ExtractionStatus, SubjectAnalysisCache

def analyze_subject(request, subject_id):
    """
    AJAX endpoint to fetch precomputed semantic analysis for a subject.
    Returns rendered HTML snippet to be injected into the page.
    """
    try:
        force = request.GET.get('force', 'false').lower() == 'true'

        # 1. Get ALL QuestionPapers for this subject
        papers = QuestionPaper.objects.filter(subject_id=subject_id)

        # 2. Create any missing statuses and optionally requeue failures.
        for paper in papers:
            status, created = ExtractionStatus.objects.get_or_create(
                question_paper=paper,
                defaults={'status': 'PENDING'}
            )
            
            # Allow retry of FAILED jobs via force reload
            if force and status.status == 'FAILED':
                status.status = 'PENDING'
                status.save()

        # 3. Ensure every subject has a cache job.  This also repairs older
        # subjects that were uploaded before the automatic queue existed.
        cache, _ = SubjectAnalysisCache.objects.get_or_create(subject_id=subject_id)
        if not cache.results_json and not cache.is_stale:
            cache.is_stale = True
            cache.save(update_fields=['is_stale'])
        # 4. Fetch the currently cached data (if any)
        analysis_data = get_cached_analysis(subject_id)

        # A pending paper must not prevent students from viewing analysis of
        # papers which have already completed.  Deleted-paper signals clear
        # the cache, so stale data cannot be returned for removed papers.
        if not analysis_data:
            return render(request, 'ai_analysis/partials/processing_status.html')

        # Do not show a processing banner to students for a separate queued
        # paper; the cached report remains useful until the worker refreshes it.
        return render(request, 'ai_analysis/partials/analysis_results.html', {
            'data': analysis_data,
            'update_in_progress': False,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)
