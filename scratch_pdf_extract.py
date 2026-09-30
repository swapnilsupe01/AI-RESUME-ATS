import fitz
from pathlib import Path

paths = [
    Path(r"C:\Users\DELL\Pictures\Seema Exam Forms and gate form\Swapnil Supe Perfect Resume.pdf"),
    Path(r"C:\DevTools\AI-Resume-ATS\dataset\resumes\swapnil_resume.pdf"),
]

out_path = Path(r"C:\DevTools\AI-Resume-ATS\scratch_pdf_extract_out.txt")
lines = []


def log(s=""):
    lines.append(s)
    print(s)


for pdf_path in paths:
    log("=" * 100)
    log(f"FILE: {pdf_path}")
    log(f"EXISTS: {pdf_path.exists()}")
    if not pdf_path.exists():
        continue
    doc = fitz.open(pdf_path)
    log(f"PAGES: {len(doc)}")
    log(f"METADATA: {doc.metadata}")
    for i, page in enumerate(doc):
        log("\n" + "#" * 80)
        log(f"PAGE {i+1} size={page.rect}")
        log("#" * 80)

        text = page.get_text("text")
        log("\n--- FULL TEXT ---")
        log(text)

        d = page.get_text("dict")
        log("\n--- SPAN METADATA (font/size/color/bbox/flags) ---")
        for bi, block in enumerate(d["blocks"]):
            if block.get("type") != 0:
                log(f"\n[BLOCK {bi} NON-TEXT type={block.get('type')} bbox={block.get('bbox')}]")
                continue
            log(f"\n[BLOCK {bi} bbox={[round(x,1) for x in block['bbox']]}]")
            for li, line in enumerate(block["lines"]):
                spans_info = []
                line_text = ""
                for span in line["spans"]:
                    color = span.get("color", 0)
                    r = (color >> 16) & 255
                    g = (color >> 8) & 255
                    b = color & 255
                    flags = span.get("flags", 0)
                    bold = bool(flags & 2**4)
                    italic = bool(flags & 2**1)
                    line_text += span["text"]
                    spans_info.append({
                        "text": span["text"],
                        "font": span.get("font"),
                        "size": round(span.get("size", 0), 2),
                        "color_rgb": (r, g, b),
                        "flags": flags,
                        "bold": bold,
                        "italic": italic,
                        "origin": [round(x, 1) for x in span.get("origin", (0, 0))],
                        "bbox": [round(x, 1) for x in span.get("bbox", (0, 0, 0, 0))],
                    })
                log(f"  LINE {li} y0={round(line['bbox'][1],1)} text={line_text!r}")
                for s in spans_info:
                    log(
                        f"    SPAN: size={s['size']} font={s['font']} rgb={s['color_rgb']} "
                        f"bold={s['bold']} italic={s['italic']} bbox={s['bbox']} text={s['text']!r}"
                    )

        drawings = page.get_drawings()
        log(f"\n--- DRAWINGS count={len(drawings)} ---")
        for di, dr in enumerate(drawings[:80]):
            log(
                f"  draw[{di}] type={dr.get('type')} color={dr.get('color')} "
                f"fill={dr.get('fill')} width={dr.get('width')} rect={dr.get('rect')}"
            )
            for it in dr.get("items", [])[:12]:
                log(f"    item={it}")

        links = page.get_links()
        if links:
            log("\n--- LINKS ---")
            for lk in links:
                log(str(lk))
    doc.close()

out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"\nWrote {out_path}")
