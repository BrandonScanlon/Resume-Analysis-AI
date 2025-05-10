from pdfminer.high_level import extract_text

def parse_pdf(file_path):
    return extract_text(file_path)