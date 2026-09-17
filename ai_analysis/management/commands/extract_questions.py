import logging
from django.core.management.base import BaseCommand
from papers.models import QuestionPaper
from ai_analysis.extractor import extract_from_paper

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run extraction on QuestionPapers to parse out questions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--subject', 
            type=str, 
            help='Filter papers by Subject Name (exact match)'
        )
        parser.add_argument(
            '--paper_id', 
            type=int, 
            help='Process a specific QuestionPaper ID'
        )
        parser.add_argument(
            '--force', 
            action='store_true', 
            help='Force re-extraction even if already COMPLETED'
        )

    def handle(self, *args, **options):
        subject_name = options.get('subject')
        paper_id = options.get('paper_id')
        force = options.get('force')

        papers = QuestionPaper.objects.all()
        
        if subject_name:
            papers = papers.filter(subject__name=subject_name)
            self.stdout.write(self.style.SUCCESS(f"Filtering by subject: {subject_name}"))
            
        if paper_id:
            papers = papers.filter(id=paper_id)
            self.stdout.write(self.style.SUCCESS(f"Filtering by paper_id: {paper_id}"))

        if not papers.exists():
            self.stdout.write(self.style.WARNING("No papers found matching the criteria."))
            return

        for paper in papers:
            self.stdout.write(self.style.NOTICE(f"Processing: {paper}..."))
            
            # Check existing status
            if not force and hasattr(paper, 'extraction_status') and paper.extraction_status.status == 'COMPLETED':
                self.stdout.write(self.style.SUCCESS(f"Skipped {paper.id} - Already COMPLETED. Use --force to override."))
                continue
                
            # If force is true, we delete existing status so it starts fresh
            if force and hasattr(paper, 'extraction_status'):
                paper.extraction_status.delete()

            extract_from_paper(paper)
            
            # Fetch status to report
            paper.refresh_from_db()
            status = paper.extraction_status
            if status.status == 'COMPLETED':
                self.stdout.write(self.style.SUCCESS(f"Success! {status.questions_extracted} questions extracted via {status.extraction_method}."))
            else:
                self.stdout.write(self.style.ERROR(f"Failed: {status.error_message}"))
