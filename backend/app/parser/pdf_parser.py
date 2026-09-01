"""
PDF parsing module using PyMuPDF (fitz) for AI Resume ATS.
"""
import os
from typing import Tuple, List
import pymupdf as fitz  # PyMuPDF

def extract_text_and_links_from_bytes(file_bytes: bytes) -> Tuple[str, List[str]]:
    """
    Extract raw text and embedded clickable hyperlinks directly from PDF file bytes.
    
    Args:
        file_bytes (bytes): Binary PDF data.
        
    Returns:
        Tuple[str, List[str]]: (Extracted text content, list of extracted URI links)
    """
    text_content = []
    extracted_links = []
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text")
            if page_text:
                text_content.append(page_text.strip())
            
            # Extract clickable hyperlinks / URI annotations
            try:
                links = page.get_links()
                for link in links:
                    uri = link.get("uri")
                    if uri and isinstance(uri, str):
                        uri_clean = uri.strip().rstrip('.,;:)"\'')
                        if uri_clean and uri_clean.startswith(("http://", "https://", "www.", "github.com", "linkedin.com")):
                            if uri_clean not in extracted_links:
                                extracted_links.append(uri_clean)
            except Exception:
                pass
        doc.close()
    except Exception as e:
        raise RuntimeError(f"Error parsing PDF stream: {str(e)}")
        
    return "\n\n".join(text_content), extracted_links

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
    text, _ = extract_text_and_links_from_bytes(file_bytes)
    return text
