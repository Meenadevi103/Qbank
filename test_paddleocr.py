import sys
import os
import fitz

os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"

from paddleocr import PaddleOCR

# Load a PDF and run OCR on the first page
pdf_path = sys.argv[1]
doc = fitz.open(pdf_path)
page = doc.load_page(0)

matrix = fitz.Matrix(2, 2)
pix = page.get_pixmap(matrix=matrix, alpha=False)
pix.save("test_page.png")

ocr = PaddleOCR(
    lang="en",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    enable_mkldnn=False
)

res = ocr.predict("test_page.png")
print("===== RAW RESULT TYPE =====", type(res))
print("===== RAW RESULT =====", res)
