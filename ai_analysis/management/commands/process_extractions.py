import time
import datetime
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from ai_analysis.models import ExtractionStatus
from ai_analysis.extractor import extract_from_paper
from papers.models import QuestionPaper

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Runs the durable background worker to process AI analysis extractions.'

    def handle(self, *args, **options):
        import sys
        import os
        
        # Strictly enforce virtual environment usage to prevent dependency issues (e.g. PaddleOCR)
        if 'venv' not in sys.executable.lower() and 'virtual_env' not in os.environ.get('VIRTUAL_ENV', '').lower():
            self.stdout.write(self.style.ERROR(
                "FATAL: The extraction worker MUST be run inside the virtual environment.\n"
                f"Current executable: {sys.executable}\n"
                "Please run: .\\venv\\Scripts\\python.exe manage.py process_extractions"
            ))
            sys.exit(1)
            
        self.stdout.write(self.style.SUCCESS("Starting AI Analysis Extraction Worker..."))
        
        while True:
            try:
                # Find all papers that are PENDING, FAILED, or stuck in PROCESSING
                # We do this one by one to avoid locking large amounts of rows
                stale_threshold = timezone.now() - datetime.timedelta(minutes=5)
                
                # Fetch candidate extraction jobs
                candidates = ExtractionStatus.objects.filter(
                    status='PENDING'
                ) | ExtractionStatus.objects.filter(
                    status='PROCESSING', updated_at__lt=stale_threshold
                )
                
                candidate = candidates.order_by('created_at').first()
                
                if candidate:
                    # Atomically claim the extraction job using optimistic concurrency control
                    updated = ExtractionStatus.objects.filter(
                        id=candidate.id,
                        updated_at=candidate.updated_at
                    ).update(status='PROCESSING', updated_at=timezone.now())
                    
                    if updated:
                        self.stdout.write(self.style.WARNING(f"Processing paper ID: {candidate.question_paper_id}"))
                        # Refetch to get the latest state and related objects properly
                        paper = QuestionPaper.objects.get(id=candidate.question_paper_id)
                        
                        try:
                            extract_from_paper(paper)
                            self.stdout.write(self.style.SUCCESS(f"Finished processing paper ID: {paper.id}"))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"Error processing paper {paper.id}: {e}"))
                            ExtractionStatus.objects.filter(id=candidate.id).update(
                                status='FAILED', 
                                error_message=str(e),
                                updated_at=timezone.now()
                            )
                    else:
                        # Another worker claimed it, loop immediately
                        continue
                else:
                    # No extraction jobs found. Check for stale subject analysis caches.
                    from ai_analysis.models import SubjectAnalysisCache
                    from ai_analysis.analyzer import perform_semantic_analysis
                    
                    stale_caches = SubjectAnalysisCache.objects.filter(is_stale=True)
                    processed_cache = False
                    
                    for cache in stale_caches:
                        # Ensure this subject has NO pending/processing extractions before we compute
                        # This prevents duplicate analysis runs when multiple papers are uploaded together
                        has_pending = ExtractionStatus.objects.filter(
                            question_paper__subject=cache.subject,
                            status__in=['PENDING', 'PROCESSING']
                        ).exists()
                        
                        if not has_pending:
                            self.stdout.write(self.style.WARNING(f"Computing semantic analysis for subject: {cache.subject.name}"))
                            try:
                                perform_semantic_analysis(cache.subject.id)
                                self.stdout.write(self.style.SUCCESS(f"Finished semantic analysis for subject: {cache.subject.name}"))
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f"Error computing analysis for subject {cache.subject.name}: {e}"))
                                # Prevent infinite loop on failure
                                cache.is_stale = False
                                cache.save(update_fields=['is_stale'])
                            
                            processed_cache = True
                            break # Only do one at a time, then loop
                            
                    if not processed_cache:
                        # No jobs found at all, sleep
                        time.sleep(5)
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Worker encountered an unexpected error: {e}"))
                time.sleep(10)
