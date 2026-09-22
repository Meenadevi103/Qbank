
import os
import tempfile
import logging
import shutil
import subprocess

import fitz

from ai_analysis.models import (
    ExtractionStatus,
    ExtractedQuestion,
    SubjectAnalysisCache,
)
from ai_analysis.parser import parse_questions_from_text

logger = logging.getLogger(__name__)

# Prefer the lightweight local Tesseract executable for scanned papers.  The
# configured path supports the standard Windows installer while shutil.which
# supports PATH-based deployments.
TESSERACT_WINDOWS_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Global lazy-loaded PaddleOCR instance
_ocr_instance = None


def get_ocr_instance():
    """
    Initialize PaddleOCR once and reuse it.
    """
    global _ocr_instance

    if _ocr_instance is None:
        os.environ["FLAGS_enable_pir_api"] = "0"
        os.environ["FLAGS_use_mkldnn"] = "0"

        try:
            from paddleocr import PaddleOCR
        except ImportError as e:
            raise ImportError(
                f"PaddleOCR import failed: {e}"
            ) from e

        _ocr_instance = PaddleOCR(
            lang="en",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            enable_mkldnn=False,
        )

    return _ocr_instance


def is_text_usable(text):
    """
    Check whether native PDF text is usable.
    Return False if the page likely needs OCR.
    """
    text = text.strip()

    if len(text) < 50:
        return False

    printable = sum(1 for char in text if char.isprintable())

    if printable / max(1, len(text)) < 0.8:
        return False

    return True


def extract_from_paper(question_paper):
    """
    Extract questions from a QuestionPaper PDF.

    Uses native PDF text when usable.
    Uses Tesseract for scanned or unusable pages, with PaddleOCR as a fallback.
    Updates ExtractionStatus and saves ExtractedQuestion records.
    """

    status, created = ExtractionStatus.objects.get_or_create(
        question_paper=question_paper,
        defaults={"status": "PENDING"},
    )

    # Do not process papers that are already completed.
    if status.status == "COMPLETED":
        logger.info(
            "Paper %s already processed. Skipping.",
            question_paper.id,
        )
        return

    status.status = "PROCESSING"
    status.error_message = ""
    status.pages_processed = 0
    status.questions_extracted = 0
    status.character_count = 0
    status.extraction_method = "UNKNOWN"
    status.save()

    try:
        pdf_path = question_paper.pdf_file.path

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(
                f"PDF file not found: {pdf_path}"
            )

        total_questions = 0
        total_chars = 0
        methods_used = set()

        # Open PDF safely and close it after processing.
        with fitz.open(pdf_path) as doc:
            total_pages = len(doc)

            status.total_pages = total_pages
            status.save(update_fields=["total_pages"])
            
            context = None

            for page_num in range(total_pages):
                page = doc.load_page(page_num)

                page_text = page.get_text("text").strip()
                method = "NATIVE"

                # Use OCR only when native text is unusable.
                if not is_text_usable(page_text):
                    method = "OCR"

                    logger.info(
                        "Page %s of paper %s needs OCR.",
                        page_num + 1,
                        question_paper.id,
                    )

                    page_text = extract_via_tesseract(
                        page,
                        page_num + 1,
                    )

                methods_used.add(method)

                if page_text:
                    total_chars += len(page_text)

                    questions_data, context = parse_questions_from_text(
                        page_text,
                        page_number=page_num + 1,
                        context=context,
                        is_last_page=(page_num == total_pages - 1)
                    )

                    for q_data in questions_data:
                        ExtractedQuestion.objects.create(
                            question_paper=question_paper,
                            page_number=q_data["page_number"],
                            question_number=q_data["question_number"],
                            part=q_data["part"],
                            section=q_data.get("section"),
                            question_text=q_data["question_text"],
                            raw_text_block=q_data["raw_text_block"],
                            marks=q_data.get("marks")
                        )

                        total_questions += 1

                status.pages_processed = page_num + 1
                status.save(
                    update_fields=["pages_processed"]
                )

        # Set the extraction method based on pages processed.
        if len(methods_used) > 1:
            status.extraction_method = "MIXED"
        elif "OCR" in methods_used:
            status.extraction_method = "OCR"
        elif "NATIVE" in methods_used:
            status.extraction_method = "NATIVE"
        else:
            status.extraction_method = "UNKNOWN"

        status.status = "COMPLETED"
        status.questions_extracted = total_questions
        status.character_count = total_chars
        status.error_message = ""
        status.save()

        # Mark cached analysis stale so it is recomputed.
        SubjectAnalysisCache.objects.update_or_create(
            subject=question_paper.subject,
            defaults={"is_stale": True},
        )

        logger.info(
            "Successfully processed paper %s: %s questions extracted.",
            question_paper.id,
            total_questions,
        )

    except Exception as e:
        status.status = "FAILED"
        status.error_message = str(e)
        status.save()

        logger.exception(
            "Error processing paper %s",
            question_paper.id,
        )

        # Re-raise so the worker can detect the failure.
        raise


def get_tesseract_executable():
    """Return the local Tesseract command, or None when it is unavailable."""
    configured_path = os.environ.get("TESSERACT_CMD", TESSERACT_WINDOWS_PATH)
    return shutil.which("tesseract") or (
        configured_path if os.path.isfile(configured_path) else None
    )


def extract_via_tesseract(page, page_num):
    """Render a page and extract text with Tesseract, falling back to PaddleOCR."""
    temp_img_path = None

    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_img:
            temp_img_path = temp_img.name

        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        pix.save(temp_img_path)

        tesseract = get_tesseract_executable()
        if tesseract:
            result = subprocess.run(
                [tesseract, temp_img_path, "stdout", "-l", "eng", "--psm", "6"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=90,
                check=False,
            )
            extracted_text = result.stdout.strip()
            if result.returncode == 0 and extracted_text:
                logger.info(
                    "Page %s extracted with Tesseract.",
                    page_num,
                )
                return extracted_text

            logger.warning(
                "Tesseract returned no usable text for page %s; using PaddleOCR fallback. %s",
                page_num,
                result.stderr.strip(),
            )
        else:
            logger.warning(
                "Tesseract is unavailable for page %s; using PaddleOCR fallback.",
                page_num,
            )

        return extract_via_paddleocr_image(temp_img_path)
    except (subprocess.TimeoutExpired, OSError) as exc:
        logger.warning(
            "Tesseract failed for page %s; using PaddleOCR fallback: %s",
            page_num,
            exc,
        )
        return extract_via_paddleocr_image(temp_img_path)
    finally:
        if temp_img_path and os.path.exists(temp_img_path):
            os.remove(temp_img_path)


def extract_via_paddleocr_image(image_path):
    """Extract text from a rendered image with the retained PaddleOCR fallback."""
    ocr = get_ocr_instance()
    result = ocr.predict(image_path)
    res_list = list(result) if result else []
    extracted_text = []

    if res_list:
        first_res = res_list[0]

        # PaddleOCR 3.x result format.
        if hasattr(first_res, "keys"):
            if "rec_texts" in first_res:
                extracted_text = first_res["rec_texts"]
            elif "rec_text" in first_res:
                extracted_text = first_res["rec_text"]
        # Compatibility fallback for older result formats.
        else:
            for line in first_res:
                if isinstance(line, (list, tuple)) and len(line) == 2:
                    extracted_text.append(line[1][0])

    return "\n".join(str(text) for text in extracted_text if text)


def extract_via_paddleocr(page, page_num):
    """
    Render a PDF page to PNG and extract text using PaddleOCR.
    """
    ocr = get_ocr_instance()

    temp_img_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False,
        ) as temp_img:
            temp_img_path = temp_img.name

        # Render PDF page to an image.
        matrix = fitz.Matrix(2, 2)

        pix = page.get_pixmap(
            matrix=matrix,
            alpha=False,
        )

        pix.save(temp_img_path)

        # Run PaddleOCR.
        result = ocr.predict(temp_img_path)

        res_list = list(result) if result else []

        extracted_text = []

        if res_list:
            first_res = res_list[0]

            # PaddleOCR 3.x result format.
            if hasattr(first_res, "keys"):
                if "rec_texts" in first_res:
                    extracted_text = first_res["rec_texts"]

                elif "rec_text" in first_res:
                    extracted_text = first_res["rec_text"]

            # Compatibility fallback for older result formats.
            else:
                for line in first_res:
                    if (
                        isinstance(line, (list, tuple))
                        and len(line) == 2
                    ):
                        text = line[1][0]
                        extracted_text.append(text)

        return "\n".join(
            str(text)
            for text in extracted_text
            if text
        )

    finally:
        # Remove temporary image even if OCR fails.
        if (
            temp_img_path
            and os.path.exists(temp_img_path)
        ):
            os.remove(temp_img_path)
