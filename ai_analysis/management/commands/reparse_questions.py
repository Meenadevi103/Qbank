from django.core.management.base import BaseCommand
from ai_analysis.models import ExtractedQuestion, SubjectAnalysisCache
from ai_analysis.parser import parse_questions_from_text
from papers.models import QuestionPaper
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Reparses existing ExtractedQuestions using raw_text_block to fix subpart fragmentation'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting safe re-parse of questions...")
        
        # We need to gather all raw text blocks per question paper per page
        papers = QuestionPaper.objects.all()
        
        total_questions_before = ExtractedQuestion.objects.count()
        
        for paper in papers:
            questions = ExtractedQuestion.objects.filter(question_paper=paper).order_by('page_number', 'id')
            if not questions.exists():
                continue
                
            self.stdout.write(f"Processing paper {paper.id}...")
            
            # Group raw_text_block by page_number
            pages_data = defaultdict(list)
            for q in questions:
                pages_data[q.page_number].append(q.raw_text_block)
                
            # Now delete the old questions for this paper
            questions.delete()
            
            # Reparse and recreate
            total_recreated = 0
            for page_number, text_blocks in pages_data.items():
                # Reconstruct the page text by joining the blocks
                page_text = "\n".join(text_blocks)
                
                new_questions_data = parse_questions_from_text(page_text, page_number=page_number)
                
                for q_data in new_questions_data:
                    ExtractedQuestion.objects.create(
                        question_paper=paper,
                        page_number=q_data['page_number'],
                        question_number=q_data['question_number'],
                        part=q_data['part'],
                        question_text=q_data['question_text'],
                        raw_text_block=q_data['raw_text_block']
                    )
                    total_recreated += 1
            
            self.stdout.write(f"Paper {paper.id} processed: recreated {total_recreated} unified questions.")
            
        total_questions_after = ExtractedQuestion.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Re-parse complete! Before: {total_questions_before} | After: {total_questions_after}"))
        
        # Invalidate cache
        SubjectAnalysisCache.objects.update(is_stale=True)
        self.stdout.write(self.style.SUCCESS("Subject Analysis Cache invalidated."))
