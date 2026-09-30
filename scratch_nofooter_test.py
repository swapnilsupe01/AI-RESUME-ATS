from pathlib import Path
import pymupdf as fitz
from app.parser.canonical_parser import parse_pdf_bytes_to_canonical
from app.parser.pdf_generator import generate_pdf

p = Path(r'C:\Users\DELL\Pictures\Seema Exam Forms and gate form\Swapnil Supe Perfect Resume.pdf')
d = parse_pdf_bytes_to_canonical(p.read_bytes())[0].model_dump()
print('EDU COUNT', len(d.get('education') or []))
for e in d.get('education') or []:
    print(' -', e.get('institution'), '|', e.get('degree'), '|', e.get('gpa'), '|', e.get('start_date'), e.get('end_date'))

pdf = generate_pdf(d)
out = Path('dataset/resumes/swapnil_nofooter_test.pdf')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(pdf)
doc = fitz.open(stream=pdf, filetype='pdf')
text = ''.join(pg.get_text() for pg in doc)
# Count how many times SWAPNIL SUPE appears (should be 1 = header only, not footer)
print('pages', len(doc))
print('SWAPNIL SUPE count', text.count('SWAPNIL SUPE'))
print('Vidyalankar', 'Vidyalankar' in text)
print('2024-2027' in text or '2024–2027' in text or ('2024' in text and '2027' in text))
print('Bharati', 'Bharati' in text)
print('HSC', 'HSC' in text)
print('footer-ish last 200 chars:', repr(text[-200:]))
print('---EDUCATION SECTION---')
i = text.find('EDUCATION')
print(text[i:i+500] if i>=0 else 'NO EDUCATION')
