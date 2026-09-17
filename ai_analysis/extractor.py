import os
import fitz
import tempfile
import logging
from pathlib import Path
from django.conf import settings
from ai_analysis.models import ExtractionStatus, ExtractedQuestion
from ai_analysis.parser import parse_questions_from_text

logger = logging.getLogger(__name__)

# Global lazy-loaded PaddleOCR instance
_ocr_instance = None

def get_ocr_instance():
    global _ocr_instance
    if _ocr_instance is None:
        # Set required environment variables for PaddleOCR as requested
        os.environ["FLAGS_enable_pir_api"] = "0"
        os.environ["FLAGS_use_mkldnn"] = "0"
        
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            raise ImportError("PaddleOCR is required for scanned PDFs but is not installed.")

        # Initialize OCR once
        _ocr_instance = PaddleOCR(
            lang="en",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            enable_mkldnn=False
        )
    return _ocr_instance

def is_text_usable(text):
    """
    Check if the native text extracted from PyMuPDF is actually usable.
    Returns True if valid text, False if it's likely a scanned image.
    """
    text = text.strip()
    if len(text) < 50:
        return False
    # If the text has too many unprintable characters, it might be junk OCR
    printable = sum(1 for c in text if c.isprintable())
    if printable / max(1, len(text)) < 0.8:
        return False
    return True

def extract_from_paper(question_paper):
    """
    Main entry point for extracting text from a QuestionPaper.
    Updates the ExtractionStatus and creates ExtractedQuestion records.
    """
    status, created = ExtractionStatus.objects.get_or_create(question_paper=question_paper)
    
    # Don't re-process if already completed successfully
    if status.status == 'COMPLETED':
        logger.info(f"Paper {question_paper.id} already processed. Skipping.")
        return
        
    status.status = 'PROCESSING'
    status.save()
    
    # Clean up previous extraction attempts for this paper
    ExtractedQuestion.objects.filter(question_paper=question_paper).delete()
    
    pdf_path = question_paper.pdf_file.path
    if not os.path.exists(pdf_path):
        status.status = 'FAILED'
        status.error_message = f"File not found: {pdf_path}"
        status.save()
        return

    total_questions = 0
    total_chars = 0
    
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        status.total_pages = total_pages
        status.save()
        
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            page_text = page.get_text("text").strip()
            
            method = 'NATIVE'
            
            # If native text is unusable, fallback to OCR
            if not is_text_usable(page_text):
                method = 'OCR'
                logger.info(f"Page {page_num + 1} of {question_paper.id} has no native text. Falling back to OCR.")
                page_text = extract_via_paddleocr(page, page_num + 1)
            
            if status.extraction_method == 'UNKNOWN':
                status.extraction_method = method
            elif status.extraction_method != method:
                status.extraction_method = 'MIXED'
                
            # Parse questions
            if page_text:
                total_chars += len(page_text)
                questions_data = parse_questions_from_text(page_text, page_number=page_num + 1)
                
                for q_data in questions_data:
                    ExtractedQuestion.objects.create(
                        question_paper=question_paper,
                        page_number=q_data['page_number'],
                        question_number=q_data['question_number'],
                        part=q_data['part'],
                        question_text=q_data['question_text'],
                        raw_text_block=q_data['raw_text_block']
                    )
                    total_questions += 1
            
            status.pages_processed = page_num + 1
            status.save()
            
        # Completion
        status.status = 'COMPLETED'
        status.questions_extracted = total_questions
        status.character_count = total_chars
        status.error_message = ''
        status.save()
        logger.info(f"Successfully processed {question_paper.id}: {total_questions} questions extracted.")
        
    except Exception as e:
        status.status = 'FAILED'
        status.error_message = str(e)
        status.save()
        logger.error(f"Error processing {question_paper.id}: {e}")

def extract_via_paddleocr(page, page_num):
    """
    Renders a PyMuPDF page to PNG and runs PaddleOCR on it.
    """
    ocr = get_ocr_instance()
    
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_img:
        temp_img_path = temp_img.name
        
    try:
        # Render to PNG
        matrix = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        pix.save(temp_img_path)
        
        # Run OCR
        result = ocr.predict(temp_img_path)
        
        # Parse PaddleOCR result
        res_list = list(result) if result else []
        extracted_text = []
        if res_list and len(res_list) > 0:
            first_res = res_list[0]
            if hasattr(first_res, 'keys') and 'rec_texts' in first_res:
                extracted_text = first_res['rec_texts']
            elif hasattr(first_res, 'keys') and 'rec_text' in first_res:
                extracted_text = first_res['rec_text']
            else:
                # Old v2 format
                for line in first_res:
                    if isinstance(line, (list, tuple)) and len(line) == 2:
                        text = line[1][0]
                        extracted_text.append(text)
                        
        return "\n".join(extracted_text)
    finally:
        # Clean up temporary PNG
        if os.path.exists(temp_img_path):
            os.remove(temp_img_path)
