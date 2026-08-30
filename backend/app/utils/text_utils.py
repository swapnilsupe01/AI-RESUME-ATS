"""
Text utilities for cleaning, URL extraction, Markdown normalization, and token helpers.
"""
import re
from typing import List, Tuple

URL_REGEX = re.compile(
    r'(https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*))',
    re.IGNORECASE
)

GITHUB_URL_REGEX = re.compile(
    r'(?:https?:\/\/)?(?:www\.)?github\.com\/([a-zA-Z0-9_-]+)(?:\/([a-zA-Z0-9_\.-]+))?',
    re.IGNORECASE
)

def extract_all_urls(text: str) -> List[str]:
    """Extract all HTTP/HTTPS links from text."""
    if not text:
        return []
    return URL_REGEX.findall(text)

def clean_markdown_and_html(raw_content: str) -> str:
    """Remove HTML tags, markdown links, badges, and redundant syntax."""
    if not raw_content:
        return ""
    # Strip HTML tags
    cleaned = re.sub(r'<[^>]+>', ' ', raw_content)
    # Strip markdown image tags ![alt](url)
    cleaned = re.sub(r'!\[.*?\]\(.*?\)', ' ', cleaned)
    # Strip markdown badges [![...](...)](...)
    cleaned = re.sub(r'\[\!\[.*?\]\(.*?\)\]\(.*?\)', ' ', cleaned)
    # Clean markdown links [text](url) -> text
    cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)
    # Strip markdown headers, bold, italics (#, *, _)
    cleaned = re.sub(r'[#*_`~]+', ' ', cleaned)
    # Normalize excessive spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def split_into_sentences(text: str) -> List[str]:
    """Split text into distinct sentences / bullet lines."""
    if not text:
        return []
    lines = text.split('\n')
    sentences = []
    for line in lines:
        cleaned = line.strip().lstrip('•-*1234567890. ')
        if len(cleaned) > 10:
            sentences.append(cleaned)
    return sentences
