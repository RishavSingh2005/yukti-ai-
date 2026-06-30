from io import BytesIO

import pdfplumber
from pdfplumber.utils.exceptions import PdfminerException

def extract_text(file):
    text = ""

    file.seek(0)
    file_bytes = file.read()

    if not file_bytes:
        raise ValueError("The uploaded file is empty. Please upload a valid PDF resume.")

    if b"%PDF-" not in file_bytes[:1024]:
        raise ValueError("This file has a PDF name, but its contents are not PDF data. Please upload the original PDF resume.")

    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
    except PdfminerException as exc:
        raise ValueError("This PDF appears to be damaged or incomplete. Please download it again and upload the original PDF.") from exc

    if not text.strip():
        raise ValueError("No readable text was found in this PDF. If it is a scanned resume, please upload a text-based PDF.")

    return text.lower()
