"""Phase 2 - Extract: copy each needed RDHS 2025 table into data/raw/ exactly as printed.

Each table -> data/raw/t<id>.csv   columns: table, pdf_page, group, label, c1..cN, ncols_flag
              data/raw/t<id>.txt   caption, column header block and footnotes (to name c1..cN in Phase 4)
Values stay as printed strings: '(12.3)' = 25-49 cases, '*' = suppressed (<25 cases), 'na' = not applicable.

Usage: python3 -I analysis/extract.py
"""
import csv, re, subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "NISR_Downloads/DHS_2025/01_Final_Report/2025 RDHS Final Report.pdf"
RAW = ROOT / "data/raw"

# Phase 1 source map (data/PHASE1_SOURCE_MAP.md); anemia is not in this report.
TABLES = ["5.3.2", "7.4.1", "8.1", "8.2", "8.3", "9.1", "9.2", "9.7.1", "9.9", "10.4",
          "11.1", "11.3", "11.4", "11.8", "12.5", "B.2", "B.3", "B.4", "B.5", "B.6", "B.7", "B.8", "B.9", "B.11", "C.18", "D.4", "D.5"]

NUM = r"(?:\[[\d.,]+;[\d.,]+\]|\[\d[\d.,]*\]|\(?[−\-]?\d[\d,]*(?:\.\d+)?\)?|\*|na|<\s?\d+(?:\.\d+)?)"
ROW = re.compile(rf"^(?P<label>\s*\S.*?)(?:\s{{2,}}|\s(?=\(?[−\-]?\d))(?P<vals>{NUM}(?:\s+{NUM})*)\s*$")
CAPTION = re.compile(r"^\s*Table\s+((?:[A-Z]\.)?\d+(?:\.\d+)*)([—–]Continued)?\s", re.M)
CI = re.compile(r"(\d[\d.,]*)\s*\(CI:\s*([\d.,]+),\s*([\d.,]+)\)")
PAIR = re.compile(r"\((\d[\d.,]*),\s*(\d[\d.,]*)\)")
FOOT = re.compile(r"^\s*(\d{1,2}\s+[A-Z]|Note:|\*|na\s*=|\(\)|Figures in parentheses|An asterisk)", re.I)

def load_pages():
    out = subprocess.run(["pdftotext", "-layout", str(PDF), "-"], capture_output=True, text=True, check=True).stdout
    return out.split("\f")

def index_pages():
    with open(ROOT / "data/table_index.csv") as f:
        return {r["id"]: int(r["pdf_page"]) for r in csv.DictReader(f) if r["kind"] == "Table"}

def table_text(pg, tid, start):
    """Text from this table's caption up to the next different caption, following '—Continued' pages."""
    parts, i = [], start - 1
    while i < len(pg):
        txt = pg[i]
        caps = [(m.start(), m[1], bool(m[2])) for m in CAPTION.finditer(txt)]
        mine = [c for c in caps if c[1] == tid]
        if not mine:
            break
        s = mine[0][0]
        nxt = [c[0] for c in caps if c[0] > s and c[1] != tid]
        parts.append((i + 1, txt[s:nxt[0] if nxt else len(txt)]))
        if nxt:  # another table starts on this page, so ours ended
            break
        i += 1
    return parts

def parse(tid, parts):
    rows, header, notes, group, pending, prev_group = [], [], [], "", None, ""
    for page, txt in parts:
        lines = txt.splitlines()
        body_started = False
        for line in lines[1:]:  # line 0 is the caption
            if not line.strip() or re.match(r"^\s*(Continued…|Table\s)", line):
                continue
            if re.fullmatch(r"\s*\d{1,3}\s*", line) or (body_started and len(line) - len(line.lstrip()) > 40 and not re.search(r"\d", line)):
                continue  # page number / running header
            line = CI.sub(r"\1  \2  \3", line)
            line = PAIR.sub(r"[\1;\2]", line)  # C.18 CI rows: '(103, 242)' -> '[103;242]'
            line = re.sub(r"(\b(?:age|ages|aged))\s+(\d{1,2})(\s{2,})", r"\1_\2\3", line)  # 'before age 15' stays in the label
            line = re.sub(r"(\S) ((?:19|20)\d\d)(\s{2,})", r"\1_\2\3", line)  # B.11 '35q15 2025' too  # '17 (CI: 13, 20)' -> estimate, low, high
            m = ROW.match(line)
            vals = re.findall(NUM, m["vals"]) if m else []
            years_only = vals and all(re.fullmatch(r"(19|20)\d\d", v) for v in vals)
            if vals and not (years_only and not body_started):
                if not body_started and header and len(header[-1].strip()) < 40 and not re.search(r"\S\s{3,}\S|[,;]$", header[-1].strip()):
                    group = pending = re.sub(r"\s+", " ", header.pop()).strip()  # first group heading
                body_started = True
                label = re.sub(r"\s+", " ", m["label"]).strip().replace("_", " ")
                if pending and (label[:1].islower() or label.startswith("(") or label == "Province"):
                    label = f"{pending} {label}"  # wrapped label: 'More than' + 'secondary', 'Southern' + 'Province'
                    group = prev_group  # the first half was not a new group heading
                rows.append(dict(table=tid, pdf_page=page, group=group, label=label,
                                 vals=vals))
                pending = None
            elif FOOT.match(line) and body_started:
                notes.append(line.strip())
            elif not body_started:
                header.append(line.rstrip())
            else:
                text = re.sub(r"\s+", " ", line).strip()
                if pending and text[:1].islower():
                    group = f"{group} {text}"  # wrapped group heading
                else:
                    prev_group, group, pending = group, text, text
    return rows, header, notes

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    pg, idx = load_pages(), index_pages()
    summary = []
    for tid in TABLES:
        parts = table_text(pg, tid, idx[tid])
        assert parts, f"caption for Table {tid} not found near PDF page {idx[tid]}"
        rows, header, notes = parse(tid, parts)
        n = Counter(len(r["vals"]) for r in rows).most_common(1)[0][0] if rows else 0
        name = "t" + tid.replace(".", "_")
        with open(RAW / f"{name}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["table", "pdf_page", "group", "label"] + [f"c{i+1}" for i in range(n)] + ["ncols_flag"])
            for r in rows:
                flag = "" if len(r["vals"]) == n else f"has {len(r['vals'])} values, expected {n}"
                w.writerow([r["table"], r["pdf_page"], r["group"], r["label"]] + (r["vals"] + [""] * n)[:max(n, len(r["vals"]))] + [flag])
        with open(RAW / f"{name}.txt", "w") as f:
            f.write(parts[0][1].splitlines()[0] + f"\nPDF pages: {', '.join(str(p) for p, _ in parts)}\n\n")
            f.write("HEADER\n" + "\n".join(header) + "\n\nFOOTNOTES\n" + "\n".join(notes) + "\n")
        bad = sum(len(r["vals"]) != n for r in rows)
        summary.append((tid, len(parts), len(rows), n, bad))
    print(f"{'table':8}{'pages':>6}{'rows':>6}{'cols':>6}{'odd':>6}")
    for s in summary:
        print(f"{s[0]:8}{s[1]:>6}{s[2]:>6}{s[3]:>6}{s[4]:>6}")

def self_check():
    """Known values read off the PDF by eye; a parser regression fails here."""
    def cell(name, label, col):
        with open(RAW / f"{name}.csv") as f:
            return next(r[col] for r in csv.DictReader(f) if r["label"] == label)
    assert cell("t8_1", "0–4 2021–2025", "c13") == "36"           # under-5 mortality
    assert cell("t8_2", "Rural", "c5") == "38"
    assert cell("t11_1", "City of Kigali", "c2") == "14.2"        # stunting by province
    assert cell("t11_1", "No education", "c2") == "37.8"
    assert cell("tD_4", "Gicumbi", "c2") == "38.8"                 # stunting by district
    assert cell("t5_3_2", "TFR (15–49)", "c7") == "3.7"
    assert cell("t7_4_1", "Any modern method", "c7") == "64.2"
    assert cell("tB_11", "Maternal mortality ratio (MMR) 2025", "c7") == "84"
    with open(RAW / "tD_4.csv") as f:
        assert sum(1 for r in csv.DictReader(f) if r["label"] != "Total") == 30, "D.4 must list 30 districts"
    print("self-check passed")

if __name__ == "__main__":
    main()
    self_check()
