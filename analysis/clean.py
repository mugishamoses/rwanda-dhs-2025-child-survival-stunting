"""Phase 4 - Clean: turn data/raw into ONE long, traceable dataset.

Usage: python3 -I analysis/clean.py
Output: data/rdhs2025_clean.csv   (one value per row, every row cites table + page)
        data/DATA_DICTIONARY.md   (indicator definitions, generated from INDICATORS below)
"""
import csv, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "data/raw", ROOT / "data"
OFFSET = 38  # Final Report: pdf page - printed page (Phase 1)
FR = "RDHS 2025 Final Report"

INDICATORS = {  # id: (label, unit, definition as worded by DHS)
    "u5mr": ("Under-5 mortality", "deaths per 1,000 live births", "Probability of dying between birth and the fifth birthday"),
    "imr": ("Infant mortality", "deaths per 1,000 live births", "Probability of dying between birth and the first birthday"),
    "nmr": ("Neonatal mortality", "deaths per 1,000 live births", "Probability of dying within the first month of life"),
    "mmr": ("Maternal mortality ratio", "deaths per 100,000 live births", "Maternal deaths (7-year period before survey) per 100,000 live births"),
    "prmr": ("Pregnancy-related mortality ratio", "deaths per 100,000 live births", "Deaths during pregnancy, delivery or 2 months after, any cause, per 100,000 live births"),
    "tfr": ("Total fertility rate", "children per woman", "Births a woman would have at current age-specific rates (3 years before survey)"),
    "mcpr": ("Modern contraceptive use", "% of currently married women 15–49", "Currently using any modern method"),
    "anc_skilled": ("Antenatal care from a skilled provider", "% of women with a live birth in 2 years", "Doctor, nurse/midwife or auxiliary midwife; most recent birth"),
    "anc_4plus": ("4+ antenatal care visits", "% of women with a live birth in 2 years", "Most recent live birth"),
    "anc_trim1": ("First antenatal visit in first trimester", "% of women with a live birth in 2 years", "First ANC visit before 4 months of pregnancy"),
    "facility_birth": ("Delivered in a health facility", "% of live births in 2 years", "Public or private health facility"),
    "home_birth": ("Delivered at home", "% of live births in 2 years", ""),
    "csection": ("Caesarean section", "% of live births in 2 years", ""),
    "skilled_birth": ("Delivered by a skilled provider", "% of live births in 2 years", "Doctor, nurse/midwife or auxiliary midwife"),
    "vacc_basic": ("Fully vaccinated (basic antigens)", "% of children 12–23 months", "BCG, 3 DPT-HepB-Hib, 3 polio, 1 measles"),
    "vacc_none": ("No vaccinations", "% of children 12–23 months", ""),
    "stunted": ("Stunted", "% of children under 5", "Height-for-age below −2 SD of WHO 2006 standard"),
    "stunted_severe": ("Severely stunted", "% of children under 5", "Height-for-age below −3 SD"),
    "wasted": ("Wasted", "% of children under 5", "Weight-for-height below −2 SD"),
    "overweight": ("Overweight", "% of children under 5", "Weight-for-height above +2 SD"),
    "underweight": ("Underweight", "% of children under 5", "Weight-for-age below −2 SD"),
    "bf_early": ("Breastfed within 1 hour of birth", "% of children born in last 2 years", ""),
    "bf_exclusive": ("Exclusive breastfeeding", "% of youngest children 0–5 months living with mother", ""),
    "diet_mdd": ("Minimum dietary diversity", "% of youngest children 6–23 months living with mother", "Foods from at least 5 of 8 groups"),
    "diet_mmf": ("Minimum meal frequency", "% of youngest children 6–23 months living with mother", ""),
    "diet_mad": ("Minimum acceptable diet", "% of youngest children 6–23 months living with mother", "Both minimum diversity and minimum meal frequency"),
}

# Rwanda's 30 districts by province, in Table D.4 order.
PROVINCE = {d: p for p, ds in {
    "City of Kigali": "Nyarugenge Gasabo Kicukiro",
    "Southern Province": "Nyanza Gisagara Nyaruguru Huye Nyamagabe Ruhango Muhanga Kamonyi",
    "Western Province": "Karongi Rutsiro Rubavu Nyabihu Ngororero Rusizi Nyamasheke",
    "Northern Province": "Rulindo Gakenke Musanze Burera Gicumbi",
    "Eastern Province": "Rwamagana Nyagatare Gatsibo Kayonza Kirehe Ngoma Bugesera"}.items() for d in ds.split()}

YEAR = {"1992": 1992, "2000": 2000, "2005": 2005, "2010": 2010, "2014-15": 2015, "2019-20": 2020, "2025": 2025}
SURVEYS = list(YEAR)

out = []

def add(ind, group_type, group, period, value, table, pdf_page, source=FR, ci=(None, None), n=None, flag="", parent=""):
    raw = (value or "").strip()
    flag = flag or ("low_n_25_49" if raw.startswith("(") else "suppressed_lt25" if raw == "*" else "printed_lt1" if raw.startswith("<") else "")
    out.append(dict(indicator=ind, label=INDICATORS[ind][0], unit=INDICATORS[ind][1], group_type=group_type, group=group,
                    parent=parent, period=period, year=YEAR.get(period, ""), value=num(raw), value_as_printed=raw,
                    ci_low=ci[0], ci_high=ci[1], n=n, flag=flag, table=table, pdf_page=pdf_page,
                    printed_page=(int(pdf_page) - OFFSET) if source == FR and pdf_page else "", source=source))

def num(v):
    v = (v or "").strip().strip("()[]").replace(",", "").replace("−", "-")
    if v.startswith("<"):
        return 0.5  # shortcut: '<1' plotted as 0.5 and flagged printed_lt1; fine for a near-zero line
    try:
        return round(float(v), 3)
    except ValueError:
        return None

def rows(name):
    with open(RAW / f"{name}.csv") as f:
        return list(csv.DictReader(f))

# Same breakdown, different wording across chapters.
ALIAS = {"Education": "Mother’s education", "Age at birth": "Mother’s age at birth", "Child’s sex": "Sex"}

def clean_group(g):
    g = re.sub(r"[\d,]+$", "", g).strip().strip('"')
    return ALIAS.get(g, g)

def section(name):
    """Rows up to the first Total (tables 9.x repeat a STILLBIRTHS block after it). Total -> national."""
    res = []
    for r in rows(name):
        if r["label"] == "Total":
            res.append(dict(r, group="national", label="Rwanda"))
            break
        res.append(dict(r, group=clean_group(r["group"])))
    return res

# A. Trends 1992-2025 (labelled figures, hand transcribed and text-checked in Phase 3).
def trends():
    with open(RAW / "figures_transcribed.csv") as f:
        for r in csv.DictReader(f):
            tbl = r["source"].replace("Final Report ", "")
            for s in SURVEYS:
                if r[s]:
                    add(r["indicator"], "trend", "Rwanda", s, r[s], tbl, r["pdf_page"] or "22", source=FR if "Final" in r["source"] else "RDHS 2025 Booklet (EN) p.22")
    tfr = next(r for r in rows("t5_3_2") if r["label"].startswith("TFR"))
    mcpr = next(r for r in rows("t7_4_1") if r["label"] == "Any modern method")
    for i, s in enumerate(SURVEYS):
        add("tfr", "trend", "Rwanda", s, tfr[f"c{i+1}"], "Table 5.3.2", tfr["pdf_page"])
        add("mcpr", "trend", "Rwanda", s, mcpr[f"c{i+1}"], "Table 7.4.1", mcpr["pdf_page"])
    # C.18 columns run newest -> oldest; 1996-2000 period = 2000 survey, etc.
    c18 = {r["label"]: r for r in rows("tC_18")}
    pr, ci = c18["Pregnancy-related mortality ratio (PRMR)4"], c18["Confidence interval"]
    for i, s in enumerate(["2025", "2019-20", "2014-15", "2010", "2005", "2000"]):
        lo, hi = ci[f"c{i+1}"].strip("[]").split(";")
        add("prmr", "trend", "Rwanda", s, pr[f"c{i+1}"], "Table C.18", pr["pdf_page"], ci=(num(lo), num(hi)))
    for r in rows("tB_11"):
        m = re.match(r"Maternal mortality ratio \(MMR\) (2025|2019–20)", r["label"])
        if m:
            add("mmr", "trend", "Rwanda", m[1].replace("–", "-"), r["c1"], "Table B.11", r["pdf_page"], ci=(num(r["c7"]), num(r["c8"])))

# B. 2025 breakdowns: (indicator, table, value col, n col, group types kept or None = all)
SPECS = [
    ("stunted", "t11_1", 2, 4), ("stunted_severe", "t11_1", 1, 4), ("wasted", "t11_1", 6, 9),
    ("overweight", "t11_1", 7, 9), ("underweight", "t11_1", 11, 13),
    ("anc_skilled", "t9_1", 9, 10), ("anc_4plus", "t9_2", 8, 15), ("anc_trim1", "t9_2", 10, 15),
    ("facility_birth", "t9_7_1", 6, 7), ("skilled_birth", "t9_9", 9, 10),
    ("vacc_basic", "t10_4", 16, 19), ("vacc_none", "t10_4", 18, 19),
    ("bf_early", "t11_3", 2, 4), ("bf_exclusive", "t11_4", 1, 3),
    ("diet_mdd", "t11_8", 10, 13), ("diet_mmf", "t11_8", 11, 13), ("diet_mad", "t11_8", 12, 13),
]
SKIP_GROUPS = {"Mother’s interview status"}

def breakdowns():
    for ind, name, vc, nc in SPECS:
        tid = "Table " + name[1:].replace("_", ".")
        for r in section(name):
            if r["group"] in SKIP_GROUPS or not r["group"]:
                continue
            add(ind, r["group"] if r["group"] != "national" else "national", r["label"], "2025",
                r[f"c{vc}"], tid, r["pdf_page"], n=num(r[f"c{nc}"]))
    # Mortality: 5-year (8.2: sex, residence) and 10-year (8.3: education, wealth, province ...)
    for name, per in [("t8_2", "2021-2025 (5y)"), ("t8_3", "2016-2025 (10y)")]:
        for r in section(name):
            for ind, c in [("nmr", 1), ("imr", 3), ("u5mr", 5)]:
                add(ind, r["group"] or "Sex", r["label"], per, r[f"c{c}"], "Table " + name[1:].replace("_", "."), r["pdf_page"])
    for r in rows("t8_1"):
        per = r["label"].split()[1]
        for ind, c in [("nmr", 1), ("imr", 7), ("u5mr", 13)]:
            add(ind, "period", "Rwanda", per, r[f"c{c}"], "Table 8.1", r["pdf_page"], ci=(num(r[f"c{c+1}"]), num(r[f"c{c+2}"])))
    for name, specs in [("tD_4", [("stunted", 2, 4), ("stunted_severe", 1, 4), ("wasted", 6, 9), ("underweight", 11, 13)]),
                        ("tD_5", [("bf_exclusive", 1, 3)])]:
        for r in rows(name):
            if r["label"] == "Total":
                continue
            assert r["label"] in PROVINCE, f"unknown district {r['label']}"
            for ind, vc, nc in specs:
                add(ind, "District", r["label"], "2025", r[f"c{vc}"], "Table " + name[1:].replace("_", "."), r["pdf_page"],
                    n=num(r[f"c{nc}"]), parent=PROVINCE[r["label"]])

# C. Confidence intervals from sampling-error tables (B.2 national, B.3-B.9 residence/province).
CI_LABELS = {"stunted": "Height-for-age (−2 SD)", "stunted_severe": "Height-for-age (−3 SD)", "wasted": "Weight-for-height (−2 SD)",
             "underweight": "Weight-for-age (−2 SD)", "anc_skilled": "Received ANC from a skilled provider", "anc_4plus": "4+ ANC visits",
             "facility_birth": "Delivered in a health facility (live births)", "skilled_birth": "Delivered by a skilled provider (live births)",
             "mcpr": "Currently using any modern method", "tfr": "Total fertility rate (3 years)"}
CI_TABLE = {"tB_2": ("national", "Rwanda"), "tB_3": ("Residence", "Urban"), "tB_4": ("Residence", "Rural"),
            "tB_5": ("Province", "City of Kigali"), "tB_6": ("Province", "Southern Province"), "tB_7": ("Province", "Western Province"),
            "tB_8": ("Province", "Northern Province"), "tB_9": ("Province", "Eastern Province")}

def attach_cis():
    for name, (gt, g) in CI_TABLE.items():
        b = {r["label"]: r for r in rows(name)}
        for ind, lab in CI_LABELS.items():
            r = b.get(lab)
            if not r:
                continue
            scale = 1 if ind == "tfr" else 100
            lo, hi, val = num(r["c7"]) * scale, num(r["c8"]) * scale, num(r["c1"]) * scale
            for o in out:
                same = o["indicator"] == ind and o["group"] == g and (o["group_type"] == gt or (gt == "national" and o["group_type"] in ("national", "trend")))
                if same and o["period"] == "2025" and o["value"] is not None and abs(o["value"] - val) <= 0.6:
                    o["ci_low"], o["ci_high"] = round(lo, 1), round(hi, 1)
                    o["table"] += f"; CI {name[1:].replace('_', '.')}"

def write():
    cols = list(out[0])
    with open(OUT / "rdhs2025_clean.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(out)
    with open(OUT / "DATA_DICTIONARY.md", "w") as f:
        f.write("# Data dictionary: `data/rdhs2025_clean.csv`\n\nGenerated by `analysis/clean.py`. One row = one value.\n\n")
        f.write("| Column | Meaning |\n|---|---|\n" + "\n".join(f"| `{k}` | {v} |" for k, v in {
            "indicator / label / unit": "what is measured (see table below)",
            "group_type / group": "breakdown, e.g. Province / Western Province; `trend` = national series over surveys; `national` = 2025 total",
            "parent": "province of a district",
            "period / year": "survey round (year = numeric for plotting: 2014-15→2015, 2019-20→2020) or mortality reference period",
            "value / value_as_printed": "number for maths / exact text in the PDF",
            "ci_low / ci_high": "95% confidence interval (R±2SE) from Appendix B or the table itself",
            "n": "unweighted→weighted number of cases the % is based on",
            "flag": "`low_n_25_49` = printed in ( ), use with caution; `suppressed_lt25` = * not shown; `printed_lt1` = '<1', stored as 0.5",
            "table / pdf_page / printed_page / source": "where to find it (printed page = number on the page footer)"}.items()))
        f.write("\n\n| Indicator | Label | Unit | Definition |\n|---|---|---|---|\n")
        f.write("\n".join(f"| `{k}` | {a} | {b} | {c} |" for k, (a, b, c) in INDICATORS.items()) + "\n")

def self_check():
    key = lambda o: (o["indicator"], o["group_type"], o["group"], o["period"])
    dup = [k for k in {key(o) for o in out} if sum(key(o) == k for o in out) > 1]
    assert not dup, f"duplicate rows: {dup[:5]}"
    get = lambda i, gt, g, p="2025": next(o for o in out if key(o) == (i, gt, g, p))
    assert get("stunted", "national", "Rwanda")["value"] == 26.8
    assert get("stunted", "national", "Rwanda")["ci_low"] == 25.4
    assert get("stunted", "District", "Gicumbi")["parent"] == "Northern Province"
    assert get("stunted", "Mother’s education", "No education")["value"] == 37.8
    assert get("u5mr", "trend", "Rwanda", "2000")["value"] == 196
    assert get("prmr", "trend", "Rwanda", "2000")["value"] == 1071
    assert get("mmr", "trend", "Rwanda", "2019-20")["ci_high"] == 281
    assert get("u5mr", "Mother’s education", "More than secondary", "2016-2025 (10y)")["flag"] == "low_n_25_49"
    assert sum(o["group_type"] == "District" and o["indicator"] == "stunted" for o in out) == 30
    assert all(o["pdf_page"] for o in out), "every row must cite a page"
    print(f"{len(out)} rows, {len({o['indicator'] for o in out})} indicators; "
          f"{sum(o['ci_low'] not in (None, '') for o in out)} with CIs; {sum(bool(o['flag']) for o in out)} flagged; self-check passed")

if __name__ == "__main__":
    trends(); breakdowns(); attach_cis(); write(); self_check()
