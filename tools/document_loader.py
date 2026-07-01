import io
from pathlib import Path


def load_document(uploaded_file, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    file_bytes = io.BytesIO(uploaded_file.read())
    if suffix == ".pdf":
        return _load_pdf(file_bytes)
    if suffix == ".txt":
        return file_bytes.read().decode("utf-8", errors="ignore")
    if suffix == ".docx":
        return _load_docx(file_bytes)
    raise ValueError(f"Unsupported file type: {suffix}")


def _load_pdf(file_obj) -> str:
    from pypdf import PdfReader
    reader = PdfReader(file_obj)
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text)
    return "\n\n".join(pages)


def _load_docx(file_obj) -> str:
    from docx import Document
    doc = Document(file_obj)
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
