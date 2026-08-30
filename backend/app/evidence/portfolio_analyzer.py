"""
Public Portfolio Analyzer.
Extracts public portfolio information, listed projects, about descriptions, and technology mentions.
"""
from typing import Dict, Any, List
import httpx
from bs4 import BeautifulSoup
from app.utils.skills import extract_skills
from app.utils.text_utils import clean_markdown_and_html

async def fetch_portfolio_evidence(url: str) -> Dict[str, Any]:
    """
    Fetch public portfolio website text and extract skills/projects.
    """
    headers = {
        "User-Agent": "AI-Resume-ATS-Portfolio-Evidence-Verifier",
        "Accept": "text/html,application/xhtml+xml"
    }

    try:
        async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")

                # Remove scripts and style tags
                for script_or_style in soup(["script", "style", "nav", "footer"]):
                    script_or_style.extract()

                raw_text = soup.get_text(separator=' ')
                cleaned_text = clean_markdown_and_html(raw_text)
                
                technologies = sorted(list(extract_skills(cleaned_text)))
                snippets = [s.strip() for s in cleaned_text.split('.') if len(s.strip()) > 20][:6]

                return {
                    "url": url,
                    "title": soup.title.string.strip() if soup.title and soup.title.string else url,
                    "technologies": technologies,
                    "evidence_snippets": snippets,
                    "preview": cleaned_text[:300] + "..." if len(cleaned_text) > 300 else cleaned_text,
                    "is_accessible": True,
                    "source": "Public Portfolio Site"
                }

    except Exception as e:
        print(f"[Portfolio Fetch Notice]: Live fetch for {url} encountered: {e}. Fallback to simulated evidence.")

    return {
        "url": url,
        "title": url,
        "technologies": [],
        "evidence_snippets": [f"Public portfolio reference at {url}"],
        "preview": f"Portfolio URL: {url}",
        "is_accessible": False,
        "source": "Portfolio Reference"
    }

async def analyze_all_portfolio_evidence(portfolio_list: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Analyze all detected portfolio websites."""
    results = []
    for p in portfolio_list:
        url = p.get("url", "")
        if url:
            ev = await fetch_portfolio_evidence(url)
            results.append(ev)
    return results
