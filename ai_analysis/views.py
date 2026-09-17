from django.shortcuts import render
from django.http import JsonResponse
from .analyzer import get_or_compute_analysis
from papers.models import QuestionPaper
from ai_analysis.models import ExtractionStatus
from .extractor import extract_from_paper
import threading

def _run_extraction_background(papers_to_extract):
    for paper in papers_to_extract:
        # Since the view already determined this paper needs extraction 
        # (including stale PROCESSING states), we just run it.
        extract_from_paper(paper)

def analyze_subject(request, subject_id):
    """
    AJAX endpoint to trigger or fetch semantic analysis for a subject.
    Returns rendered HTML snippet to be injected into the page.
    """
    try:
        force = request.GET.get('force', 'false').lower() == 'true'
        new_extraction = False
        papers_to_extract = []
        
        # 1. Get ALL QuestionPapers for this subject
        papers = QuestionPaper.objects.filter(subject_id=subject_id)
        
        import datetime
        from django.utils import timezone
        
        # 2. Check if any paper needs extraction
        for paper in papers:
            status = ExtractionStatus.objects.filter(question_paper=paper).first()
            
            is_stale = False
            if status and status.status == 'PROCESSING':
                if (timezone.now() - status.updated_at) > datetime.timedelta(minutes=5):
                    is_stale = True

            if not status or status.status in ['PENDING', 'FAILED'] or is_stale:
                papers_to_extract.append(paper)
                new_extraction = True
            elif status and status.status == 'PROCESSING':
                new_extraction = True
                
        # 3. If extraction is needed or running, return processing status UI
        if new_extraction:
            if papers_to_extract:
                thread = threading.Thread(target=_run_extraction_background, args=(papers_to_extract,))
                thread.daemon = True
                thread.start()
            return render(request, 'ai_analysis/partials/processing_status.html')
            
        analysis_data = get_or_compute_analysis(subject_id, force=force)
        
        return render(request, 'ai_analysis/partials/analysis_results.html', {
            'data': analysis_data
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)
