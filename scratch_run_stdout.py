from pathlib import Path
import pymupdf as fitz
from app.parser.canonical_parser import parse_pdf_bytes_to_canonical
from app.parser.pdf_generator import generate_pdf

p = Path(r'C:\Users\DELL\Pictures\Seema Exam Forms and gate form\Swapnil Supe Perfect Resume.pdf')
data, md, meta = parse_pdf_bytes_to_canonical(p.read_bytes())
d = data.model_dump()
print('EDU COUNT', len(d.get('education') or []))
for e in d.get('education') or []:
    print(' EDU', e.get('institution'), '|', e.get('degree'), '|', e.get('gpa'), '|', e.get('start_date'), '-', e.get('end_date'))
print('CERT COUNT', len(d.get('certifications') or []))
for c in d.get('certifications') or []:
    print(' CERT', c)
print('HOBBIES', d.get('hobbies') or d.get('custom_sections'))
pdf = generate_pdf(d)
doc = fitz.open(stream=pdf, filetype='pdf')
text = ''.join(x.get_text() for x in doc)
print('---PDF---')
print(text)
print('---')
for s in ['Vidyalankar','2024-2027','8.5','Bharati','83.83','2022-2024','HSC','SSC','Role - Company','CERTIFICATIONS:','HOBBIES:','Programming in Java']:
    print(s, '->', s in text or s.replace('-','–') in text)
print('pages', len(doc))
# ensure no cert/hobby as education lines inside EDUCATION block order
edu_idx = text.find('EDUCATION')
cert_idx = text.find('CERTIFICATIONS')
hobb_idx = text.find('HOBBIES')
hsc_idx = text.find('HSC')
print('order edu,cert,hobb,hsc', edu_idx, cert_idx, hobb_idx, hsc_idx)
print('hsc before cert?', hsc_idx < cert_idx if hsc_idx>=0 and cert_idx>=0 else 'n/a')
