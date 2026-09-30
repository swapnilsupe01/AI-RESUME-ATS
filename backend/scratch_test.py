import sys
sys.path.insert(0, 'backend')
from app.parser.markdown_pipeline import pdf_dict_to_markdown, markdown_to_canonical

# Simulate PyMuPDF dict for the education section
# In a typical resume, Degree is bold, Institution is normal weight or bold
page_dict = {
    "blocks": [
        {
            "type": 0,
            "bbox": (50, 50, 500, 70),
            "lines": [{"spans": [{"text": "SWAPNIL SUPE", "size": 16.0, "flags": 2, "font": "Bold"}]}]
        },
        {
            "type": 0,
            "bbox": (50, 100, 500, 120),
            "lines": [{"spans": [{"text": "EDUCATION", "size": 12.0, "flags": 2, "font": "Bold"}]}]
        },
        {
            "type": 0,
            "bbox": (50, 130, 300, 145),
            "lines": [{"spans": [{"text": "B.Tech in Computer Engineering", "size": 10.0, "flags": 2, "font": "Bold"}]}]
        },
        {
            "type": 0,
            "bbox": (50, 150, 400, 165),
            "lines": [{"spans": [{"text": "Vidyalankar Institute of Technology, Mumbai", "size": 9.5, "flags": 0, "font": "Regular"}]}]
        },
        {
            "type": 0,
            "bbox": (50, 170, 200, 185),
            "lines": [{"spans": [{"text": "CGPA: 8.5", "size": 9.0, "flags": 0, "font": "Regular"}]}]
        },
        {
            "type": 0,
            "bbox": (50, 190, 200, 205),
            "lines": [{"spans": [{"text": "2024 - 2027", "size": 9.0, "flags": 0, "font": "Regular"}]}]
        },
        {
            "type": 0,
            "bbox": (50, 220, 300, 235),
            "lines": [{"spans": [{"text": "Diploma in Computer Technology", "size": 10.0, "flags": 2, "font": "Bold"}]}]
        },
        {
            "type": 0,
            "bbox": (50, 240, 400, 255),
            "lines": [{"spans": [{"text": "Bharati Vidyapeeth Institute of Technology, Kharghar", "size": 9.5, "flags": 0, "font": "Regular"}]}]
        },
        {
            "type": 0,
            "bbox": (50, 260, 200, 275),
            "lines": [{"spans": [{"text": "83.83%", "size": 9.0, "flags": 0, "font": "Regular"}]}]
        },
        {
            "type": 0,
            "bbox": (50, 280, 200, 295),
            "lines": [{"spans": [{"text": "2022 - 2024", "size": 9.0, "flags": 0, "font": "Regular"}]}]
        },
        {
            "type": 0,
            "bbox": (50, 310, 500, 330),
            "lines": [{"spans": [{"text": "WORK EXPERIENCE", "size": 12.0, "flags": 2, "font": "Bold"}]}]
        },
        {
            "type": 0,
            "bbox": (50, 340, 400, 355),
            "lines": [{"spans": [{"text": "Team Lead & Full Stack Developer Intern | MokBuzz Solution Pvt. Ltd.", "size": 10.0, "flags": 2, "font": "Bold"}]}]
        },
        {
            "type": 0,
            "bbox": (50, 360, 200, 375),
            "lines": [{"spans": [{"text": "Feb 2026 - Present", "size": 10.0, "flags": 2, "font": "Bold"}]}]
        },
        {
            "type": 0,
            "bbox": (50, 380, 500, 395),
            "lines": [{"spans": [{"text": "• Led end-to-end development of a MERN-stack ERP", "size": 9.5, "flags": 0, "font": "Regular"}]}]
        },
        {
            "type": 0,
            "bbox": (50, 400, 500, 415),
            "lines": [{"spans": [{"text": "• Designed and developed a cloud-based ISO compliance management platform", "size": 9.5, "flags": 0, "font": "Regular"}]}]
        }
    ]
}

md = pdf_dict_to_markdown([page_dict])
print("=== GENERATED MARKDOWN ===")
print(md)

canon = markdown_to_canonical(md)
print("=== PARSED CANONICAL ===")
import json
print(json.dumps(canon.model_dump(), indent=2))
