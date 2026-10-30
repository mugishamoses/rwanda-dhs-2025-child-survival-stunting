"""Phase 3 - Verify data/raw against itself, the other NISR documents, and logic.

Usage: python3 -I analysis/checks.py
Output: data/verification_report.md, data/hand_check.csv (10 random values for people to tick)
Exit code 1 if any check FAILS.
"""
import csv, random, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, DHS = ROOT / "data/raw", ROOT / "NISR_Downloads/DHS_2025"
results = []  # (section, check, status, detail)

def ok(sec, name, cond, detail=""):
    results.append((sec, name, "PASS" if cond else "FAIL", detail))

def warn(sec, name, detail):
    results.append((sec, name, "WARN", detail))

def num(v):
    """'(12.3)' -> 12.3, '1,071' -> 1071, '−0.6' -> -0.6, '*'/'na' -> None."""
    v = v.strip().strip("()[]").replace(",", "").replace("−", "-")
    try:
        return float(v)
    except ValueError:
        return None

def rows(name):
    with open(RAW / f"{name}.csv") as f:
        return list(csv.DictReader(f))

def first(name, label, group=None):
    return next(r for r in rows(name) if r["label"] == label and (group is None or r["group"].startswith(group)))

def figures():
    with open(RAW / "figures_transcribed.csv") as f:
        return {r["indicator"]: r for r in csv.DictReader(f)}

def pdf_text(path):
    return subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True).stdout

# 1. Figures (2025 point) vs Final Report tables: two independent spots in the same report.
def check_figures_vs_tables():
    fig = figures()
    t = lambda name, col, label="Total": num(first(name, label)[col])
    pairs = [  # indicator, table value, label
        ("u5mr", num(first("t8_1", "0–4 2021–2025")["c13"]), "Table 8.1 under-5"),
        ("imr", num(first("t8_1", "0–4 2021–2025")["c7"]), "Table 8.1 infant"),
        ("nmr", num(first("t8_1", "0–4 2021–2025")["c1"]), "Table 8.1 neonatal"),
        ("anc_skilled", t("t9_1", "c9"), "Table 9.1 skilled ANC"),
        ("anc_4plus", t("t9_2", "c8"), "Table 9.2 4+ visits"),
        ("anc_trim1", t("t9_2", "c10"), "Table 9.2 first visit <4 months"),
        ("facility_birth", t("t9_7_1", "c6"), "Table 9.7.1 health facility"),
        ("home_birth", t("t9_7_1", "c3"), "Table 9.7.1 home"),
        ("skilled_birth", t("t9_9", "c9"), "Table 9.9 skilled provider"),
        ("vacc_basic", t("t10_4", "c16"), "Table 10.4 basic antigens"),
        ("vacc_none", t("t10_4", "c18"), "Table 10.4 no vaccinations"),
        ("stunted", t("t11_1", "c2"), "Table 11.1 HAZ<-2SD"),
        ("wasted", t("t11_1", "c6"), "Table 11.1 WHZ<-2SD"),
        ("overweight", t("t11_1", "c7"), "Table 11.1 WHZ>+2SD"),
    ]
    for ind, tv, src in pairs:
        fv = num(fig[ind]["2025"])
        ok("1 Figures vs tables", f"{ind} 2025", fv is not None and tv is not None and abs(fv - tv) <= 0.5,
           f"figure {fig[ind]['2025']} vs {src} {tv}")
    # Trend tables vs figure-derived series where both exist.
    tfr = first("t5_3_2", "TFR (15–49)")
    ok("1 Figures vs tables", "TFR 2025 (5.3.2 vs 12.5)", num(tfr["c7"]) == num(first("t12_5", "Total fertility rate (TFR)")["c1"]),
       f"5.3.2={tfr['c7']} 12.5={first('t12_5', 'Total fertility rate (TFR)')['c1']}")
    prmr = first("tC_18", "Pregnancy-related mortality ratio (PRMR)4")
    b11 = first("tB_11", "Pregnancy-related mortal- ity ratio (PRMR) 2025")
    ok("1 Figures vs tables", "PRMR 2025 (C.18 vs B.11)", num(prmr["c1"]) == num(b11["c1"]), f"C.18={prmr['c1']} B.11={b11['c1']}")
    mmr = first("tB_11", "Maternal mortality ratio (MMR) 2025")
    ok("1 Figures vs tables", "MMR 2025 (12.5 vs B.11)", num(first("t12_5", "Maternal mortality ratio (MMR)2")["c1"]) == num(mmr["c1"]),
       f"12.5=149 B.11={mmr['c1']}")
    # Each trend series endpoint vs the sentence printed beside the figure.
    for ind, r in fig.items():
        nums = re.findall(r"(\d+)%?(?: \([^)]*\))? -> ", r["text_check"])
        if not nums:
            continue
        first_val = next(v for v in [r[y] for y in ["1992", "2000", "2005"]] if v)
        claimed_start = nums[0]
        ok("1 Figures vs tables", f"{ind} series vs report text", first_val == claimed_start or claimed_start in [r[y] for y in ["1992", "2000", "2005"]],
           f"series starts {first_val}, text says {r['text_check']}")

# 2. Other NISR documents (independent publications of the same survey).
def check_other_docs():
    ki = re.sub(r"\s+", " ", pdf_text(DHS / "02_Key_Indicators/RDH7_Key_Indicators_.pdf"))
    bk = re.sub(r"\s+", " ", pdf_text(DHS / "03_Booklets/DHS7_booklet_V2.pdf"))
    claims = [  # what we will print, regex that must appear in Key Indicators
        ("under-5 mortality 36", r"under-5 mortality[^.]{0,80}\b36\b"),
        ("stunting 27%", r"stunt[^.]{0,120}\b27\s?%"),
        ("stunting 2019-20 33%", r"\b33\s?%[^.]{0,40}2019"),
        ("stunting 2005 51%", r"\b51\s?%[^.]{0,20}2005"),
        ("TFR 3.7", r"\b3\.7\b"),
        ("modern contraception 64%", r"modern[^.]{0,80}\b64\s?%"),
        ("basic vaccination 94%", r"\b94\s?%"),
        ("facility delivery 98%", r"\b98\s?%"),
    ]
    for name, rx in claims:
        m = re.search(rx, ki, re.I)
        ok("2 Key Indicators report", name, bool(m), (m.group(0)[:110] + "…") if m else "not found; check manually")
    for name, rx in [("Booklet stunting 27", r"\b27\b"), ("Booklet rural stunting 30%", r"30\s?%"), ("Booklet urban stunting 19%", r"19\s?%")]:
        ok("2 Booklet", name, bool(re.search(rx, bk)), "")

    # District stunting: Final Report D.4 vs province profile Table 10 (all 30 districts reprinted).
    prof = pdf_text(DHS / "05_Eastern_Province_Profile/RDHS 2025 DISTRICTS PROFILE_ EASTERN PROVINCE_ Final.pdf")
    block = prof[prof.rfind("Table 10: Nutrition status of children under five"):][:6000]
    prof_vals = {m[1]: (m[2], m[3], m[4]) for m in re.finditer(r"^\s*([A-Z][a-z]+(?: [A-Z][a-z]+)?)\s{3,}([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$", block, re.M)}
    d4 = [r for r in rows("tD_4") if r["label"] != "Total"]
    for r in d4:
        p = prof_vals.get(r["label"])
        if r["label"] in KNOWN:
            warn("2 Districts: D.4 vs Eastern profile", r["label"], KNOWN[r["label"]] + f" (profile={p})")
            continue
        ok("2 Districts: D.4 vs Eastern profile", r["label"],
           p is not None and (num(p[0]), num(p[1]), num(p[2])) == (num(r["c2"]), num(r["c6"]), num(r["c11"])),
           f"D.4 stunted/wasted/underweight={r['c2']}/{r['c6']}/{r['c11']} profile={p}")

# Real differences between NISR publications, checked by eye; the Final Report wins.
KNOWN = {"Nyanza": "underweight: Final Report D.4 p.484 = 7.3, both province profiles = 6.8 "
                   "(= Southern Province average, likely a profile typo). Stunting/wasting agree. Not used in story."}

# 3. Logic and ranges.
def check_logic():
    for name in ["t8_1", "t8_2", "t8_3"]:
        for r in rows(name):
            step = 3 if name == "t8_1" else 1
            nn, imr, u5 = (num(r[f"c{1 + i * step}"]) for i in (0, 2, 4))
            if None in (nn, imr, u5):
                continue
            ok("3 Logic", f"{name} {r['label']}: NN <= IMR <= U5MR", nn <= imr <= u5, f"{nn} <= {imr} <= {u5}")
    for name, cols in [("t9_7_1", range(1, 5)), ("t9_9", range(1, 8)), ("t9_1", range(1, 8))]:
        bad = []
        for r in rows(name):
            vals = [num(r[f"c{i}"]) for i in cols]
            if None not in vals and abs(sum(vals) - 100) > 0.6:
                bad.append(f"{r['label']}={sum(vals):.1f}")
        ok("3 Logic", f"{name}: distribution rows sum to 100 (±0.6 rounding)", not bad, ", ".join(bad[:5]))
    pct_cols = {"t11_1": [1, 2, 5, 6, 7, 10, 11], "tD_4": [1, 2, 5, 6, 7, 10, 11], "t10_4": list(range(1, 19)),
                "t11_3": [1, 2, 3], "t11_8": [1, 2, 3, 5, 6, 7, 8, 10, 11, 12]}
    bad = [f"{name} {r['label']} c{c}" for name, cols in pct_cols.items() for r in rows(name) for c in cols
           if num(r[f"c{c}"]) is not None and not 0 <= num(r[f"c{c}"]) <= 100]
    ok("3 Logic", "percentages within 0-100 (nutrition, vaccination, breastfeeding, diet)", not bad, ", ".join(bad[:5]))
    prov = {r["label"]: num(r["c2"]) for r in rows("t11_1") if r["group"] == "Province"}
    nat = num(first("t11_1", "Total")["c2"])
    ok("3 Logic", "national stunting lies between province min and max", min(prov.values()) <= nat <= max(prov.values()), f"{prov} national={nat}")
    # Weighted district average reproduces the national figure.
    d4 = [r for r in rows("tD_4") if r["label"] != "Total"]
    wavg = sum(num(r["c2"]) * num(r["c4"]) for r in d4) / sum(num(r["c4"]) for r in d4)
    ok("3 Logic", "weighted mean of 30 districts = national stunting", abs(wavg - nat) < 0.3, f"weighted={wavg:.2f} national={nat}")
    n = sum(num(r["c4"]) for r in d4)
    ok("3 Logic", "district child counts sum to national count", abs(n - num(first("t11_1", "Total")["c4"])) <= 30, f"sum={n:.0f}")

# 4. Reliability flags our story depends on.
def check_reliability():
    for name in ["t11_1", "tD_4", "t8_2", "t8_3"]:
        flagged = [f"{r['label']}" for r in rows(name) if any(v.startswith("(") or v == "*" for k, v in r.items() if k and k.startswith("c") and v)]
        if flagged:
            warn("4 Reliability", f"{name}: rows with ( ) or * values", ", ".join(flagged))
    b11 = {r["label"]: r for r in rows("tB_11")}
    a, b = b11["Maternal mortality ratio (MMR) 2025"], b11["Maternal mortality ratio (MMR) 2019–20"]
    overlap = num(a["c7"]) <= num(b["c8"]) and num(b["c7"]) <= num(a["c8"])
    warn("4 Reliability", "MMR 2019-20 vs 2025 confidence intervals overlap" if overlap else "MMR change is significant",
         f"2019-20 {b['c1']} [{b['c7']}–{b['c8']}] vs 2025 {a['c1']} [{a['c7']}–{a['c8']}]")
    small = [f"{r['label']} (n={r['c4']})" for r in rows("tD_4") if r["label"] != "Total" and num(r["c4"]) < 150]
    ok("4 Reliability", "every district has >=150 measured children", not small, ", ".join(small))

def hand_check_sample():
    """10 random values for both teammates to verify in the PDF by eye."""
    random.seed(2025)
    pool = []
    for f in sorted(RAW.glob("t*.csv")):
        for r in csv.DictReader(open(f)):
            for k, v in r.items():
                if k and re.fullmatch(r"c\d+", k) and v and num(v) is not None:
                    pool.append((r["table"], r["pdf_page"], r["group"], r["label"], k, v))
    with open(ROOT / "data/hand_check.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["table", "pdf_page", "group", "row_label", "column", "value", "checker_1_ok", "checker_2_ok"])
        w.writerows(random.sample(pool, 10))

def report():
    with open(ROOT / "data/verification_report.md", "w") as f:
        f.write("# Phase 3 — Verification report\n\nGenerated by `python3 -I analysis/checks.py`.\n\n")
        for st in ("PASS", "WARN", "FAIL"):
            f.write(f"- {st}: {sum(r[2] == st for r in results)}\n")
        sec = None
        for s, name, st, d in results:
            if s != sec:
                f.write(f"\n## {s}\n\n| Check | Result | Detail |\n|---|---|---|\n"); sec = s
            f.write(f"| {name} | {st} | {d.replace('|', '/')} |\n")
    fails = [r for r in results if r[2] == "FAIL"]
    print(f"PASS {sum(r[2]=='PASS' for r in results)}  WARN {sum(r[2]=='WARN' for r in results)}  FAIL {len(fails)}")
    for r in fails + [r for r in results if r[2] == "WARN"]:
        print(f"  {r[2]} [{r[0]}] {r[1]}: {r[3][:150]}")
    return not fails

if __name__ == "__main__":
    check_figures_vs_tables(); check_other_docs(); check_logic(); check_reliability(); hand_check_sample()
    sys.exit(0 if report() else 1)
