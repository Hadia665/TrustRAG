from pypdf import PdfReader
def process_pdf(pdf_path, chunk_size=1000, overlap=200):
    reader = PdfReader(pdf_path)
    chunks = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if not text:
            continue
        text = text.strip()
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "page": page_number
                })

            start += chunk_size - overlap

    return chunks