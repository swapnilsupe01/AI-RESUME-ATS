"""
PDF parsing module using PyMuPDF (fitz) for AI Resume ATS.
"""
import os
import pymupdf as fitz  # PyMuPDF

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract raw text from single or multi-page PDF files using PyMuPDF.
    
    Args:
        file_path (str): Absolute or relative path to PDF file.
        
    Returns:
        str: Extracted textual content.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found at path: {file_path}")
        
    text_content = []
    try:
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text")
            if page_text:
                text_content.append(page_text.strip())
        doc.close()
    except Exception as e:
        raise RuntimeError(f"Error parsing PDF file '{file_path}': {str(e)}")
        
    full_text = "\n\n".join(text_content)
    return full_text

def extract_text_from_bytes(file_bytes: bytes) -> str:
    """
    Extract text directly from PDF file bytes (e.g. from FastAPI file upload).
    
    Args:
        file_bytes (bytes): Binary PDF data.
        
    Returns:
        str: Extracted text content.
    """
    text_content = []
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text")
            if page_text:
                text_content.append(page_text.strip())
        doc.close()
    except Exception as e:
        raise RuntimeError(f"Error parsing PDF stream: {str(e)}")
        
    return "\n\n".join(text_content)
