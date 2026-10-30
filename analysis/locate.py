"""Phase 1 - Locate: index every Table/Figure in the RDHS 2025 Final Report,
find the real PDF page of each, and tag the ones our story needs.

Usage: python3 -I analysis/locate.py
Output: data/table_index.csv, data/story_sources.csv
"""
import csv, re, subprocess, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "NISR_Downloads/DHS_2025/01_Final_Report/2025 RDHS Final Report.pdf"
OUT = ROOT / "data"

# Story section -> regex on item title (see plan, Phase 1).
STORY = [
    ("1 Hook / mortality trend", r"early childhood mortality rates|trends in early childhood mortality"),
    ("2 Maternal mortality trend", r"maternal mortality"),
    ("2 Fertility trend", r"(trends in .*fertility|current fertility|fertility by background)"),
    ("3 Family planning", r"trends in (current use of )?contracept|contraceptive use|demand for family planning"),
    ("3 Antenatal care", r"antenatal care"),
    ("3 Delivery", r"place of (delivery|birth)|skilled attendance|assistance during delivery"),
    ("3 Vaccination", r"vaccination"),
    ("4 Stunting / nutrition", r"nutritional status of children|child growth|stunting"),
    ("5 Gaps (mortality by group)", r"mortality rates according to|mortality by (province|mother|wealth)"),
    ("6 First 1000 days", r"breastfeeding|dietary|meal frequency|anemia|anaemia"),
    ("Margins of error", r"sampling errors: (total|urban|rural|city|southern|western|northern|eastern)|maternal mortality rates, rwanda"),
    ("Mortality trend (consistent series)", r"pregnancy-related mortality trends"),
    ("District map", r"^district|by district|district-level|districts?\b"),
]

def pages(pdf):
    txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    return txt.split("\f")

def toc_items(pg):
    """TOC lines look like: 'Table 8.1   Early childhood ... ..... 141'."""
    rx = re.compile(r"^\s*(Table|Figure)\s+((?:[A-Z]\.)?\d+(?:\.\d+)*)\s+(.+?)\s*\.{2,}\s*(\d+)\s*$")
    items, seen = [], set()
    for i, p in enumerate(pg[:40]):  # TOC lives in the first pages
        # Long titles wrap: glue an entry line that lacks '.... page' to the next line.
        p = re.sub(r"(^\s*(?:Table|Figure)\s+\S+\s+[^\n.]+[^.\n\d]\s*)\n\s+", r"\1 ", p, flags=re.M)
        for line in p.splitlines():
            m = rx.match(line)
            if m and (m[1], m[2]) not in seen:
                seen.add((m[1], m[2]))
                items.append(dict(kind=m[1], id=m[2], title=re.sub(r"\s+", " ", m[3]).strip(" ."), printed_page=int(m[4])))
    return items

def footer_offset(pg):
    """pdf_page - printed_page, voted from page numbers printed in headers/footers."""
    votes = Counter()
    for i, p in enumerate(pg):
        ls = [l.strip() for l in p.strip().splitlines() if l.strip()]
        for l in ls[:1] + ls[-2:]:
            m = re.search(r"(?:^|\s)(\d{1,3})$", l) or re.match(r"^(\d{1,3})\s", l)
            if m:
                votes[i + 1 - int(m[1])] += 1
    return votes.most_common(1)[0][0]

def caption_on(page_text, it):
    """Table captions START a line; figure captions sit beside body text (two-column layout)."""
    rx = re.compile((r"^\s*" if it["kind"] == "Table" else "") + re.escape(f"{it['kind']} {it['id']}") + r"\s+" + re.escape(it["title"][:15]), re.I | re.M)
    return bool(rx.search(re.sub(r"[ \t]+", " ", page_text)))

def numeric_density(page_text):
    return len(re.findall(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])", page_text))

def main():
    if not PDF.exists():
        sys.exit(f"missing {PDF}")
    pg = pages(PDF)
    items = toc_items(pg)
    assert len(items) > 100, f"TOC parse looks wrong: {len(items)} items"
    off = footer_offset(pg)
    for it in items:
        guess = it["printed_page"] + off
        # Captions sit on the printed page; allow +-1 for tables spilling over.
        hit = next((q for q in (guess, guess + 1, guess - 1) if 0 < q <= len(pg) and caption_on(pg[q - 1], it)), None)
        it["located"] = "verified" if hit else "UNVERIFIED"
        it["pdf_page"] = hit or guess
        it["numbers_on_page"] = numeric_density(pg[it["pdf_page"] - 1])
        it["story_section"] = "; ".join(s for s, r in STORY if re.search(r, it["title"], re.I))

    OUT.mkdir(exist_ok=True)
    cols = ["kind", "id", "title", "printed_page", "pdf_page", "located", "numbers_on_page", "story_section"]
    with open(OUT / "table_index.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(items)
    story = [it for it in items if it["story_section"]]
    with open(OUT / "story_sources.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols); w.writeheader()
        w.writerows(sorted(story, key=lambda x: x["story_section"]))

    n_t = sum(i["kind"] == "Table" for i in items)
    print(f"{len(items)} items ({n_t} tables, {len(items)-n_t} figures); page offset={off}; "
          f"verified={sum(i['located']=='verified' for i in items)}; story items={len(story)}")

if __name__ == "__main__":
    main()
