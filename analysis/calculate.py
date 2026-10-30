"""Phase 5 - Calculate the insights the infographic will state.

Every insight keeps: plain-English statement, value, formula, the input rows it used
(value + table + page), a significance verdict, and caveats.

Usage: python3 -I analysis/calculate.py
Output: data/insights.csv
"""
import csv, math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = list(csv.DictReader(open(ROOT / "data/rdhs2025_clean.csv")))
NST2_TARGET = (15.0, 2029, "NST2 2024–2029: stunting 33% → 15% by 2029 (MINECOFIN NST2 abridged)")
DEFT_HAZ = 1.234  # design effect for height-for-age, Table B.2; used to approximate district SEs

insights = []

def get(ind, group_type, group, period="2025"):
    rs = [r for r in D if (r["indicator"], r["group_type"], r["group"], r["period"]) == (ind, group_type, group, period)]
    assert len(rs) == 1, f"expected 1 row for {ind}/{group_type}/{group}/{period}, got {len(rs)}"
    r = rs[0]
    r["v"] = float(r["value"])
    return r

def cite(*rs):
    return "; ".join(f"{r['indicator']} {r['group']} {r['period']} = {r['value_as_printed']} ({r['table']}, p.{r['printed_page'] or r['pdf_page']})" for r in rs)

def se(r):
    """SE from the 95% CI printed as R±2SE."""
    return (float(r["ci_high"]) - float(r["ci_low"])) / 4 if r["ci_low"] else None

def ztest(a, b, se_a, se_b):
    z = (a - b) / math.sqrt(se_a ** 2 + se_b ** 2)
    p = math.erfc(abs(z) / math.sqrt(2))
    return z, p

def verdict(z, p):
    return f"z = {z:.2f}, p = {p:.3g}: " + ("statistically significant (p < 0.05)" if p < 0.05 else "NOT statistically significant")

def add(id_, section, statement, value, unit, formula, inputs, significance="", caveat=""):
    insights.append(dict(id=id_, section=section, statement=statement, value=round(value, 2), unit=unit,
                         formula=formula, inputs=inputs, significance=significance, caveat=caveat))

def aarr(v0, v1, years):
    """Average annual rate of reduction (UNICEF/WHO): 1 - (v1/v0)^(1/years)."""
    return 1 - (v1 / v0) ** (1 / years)

def ols(xs, ys):
    n = len(xs); mx, my = sum(xs) / n, sum(ys) / n
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    r = b * math.sqrt(sum((x - mx) ** 2 for x in xs) / sum((y - my) ** 2 for y in ys))
    return b, my - b * mx, r

# 1 Hook + 2 progress: change over time ------------------------------------------------------
def trends():
    for ind, p0, p1, sec in [("u5mr", "2000", "2025", "1 Hook"), ("imr", "2000", "2025", "2 Progress"),
                             ("nmr", "2000", "2025", "2 Progress"), ("prmr", "2000", "2025", "2 Progress"),
                             ("tfr", "2000", "2025", "2 Progress"), ("stunted", "2005", "2025", "4 Problem"),
                             ("stunted", "2019-20", "2025", "4 Problem")]:
        a, b = get(ind, "trend", "Rwanda", p0), get(ind, "trend", "Rwanda", p1)
        yrs = int(b["year"]) - int(a["year"])
        drop = (a["v"] - b["v"]) / a["v"] * 100
        add(f"{ind}_drop_{p0}", sec, f"{a['label']} fell {drop:.0f}% from {a['value_as_printed']} ({p0}) to {b['value_as_printed']} ({p1})",
            drop, "% decrease", "(old − new) / old × 100", cite(a, b))
        add(f"{ind}_aarr_{p0}", sec, f"{a['label']} fell on average {aarr(a['v'], b['v'], yrs)*100:.1f}% per year, {p0}–{p1}",
            aarr(a["v"], b["v"], yrs) * 100, "% per year", f"1 − (new/old)^(1/{yrs})", cite(a, b),
            caveat="Survey rounds 2014-15 and 2019-20 treated as 2015 and 2020")
    a, b = get("u5mr", "trend", "Rwanda", "2000"), get("u5mr", "trend", "Rwanda", "2025")
    add("u5mr_per1000", "1 Hook", f"Of every 1,000 babies born, {a['v']-b['v']:.0f} more now live to their 5th birthday than in 2000",
        a["v"] - b["v"], "children per 1,000 live births", "old − new", cite(a, b),
        caveat="Rates refer to the 5 years before each survey")
    a92 = get("u5mr", "trend", "Rwanda", "1992")
    add("u5mr_1992_2000", "1 Hook", f"Under-5 mortality rose from {a92['value_as_printed']} (1992 survey) to {a['value_as_printed']} (2000 survey) before falling",
        a["v"] - a92["v"], "deaths per 1,000 increase", "2000 − 1992", cite(a92, a),
        caveat="2000 survey covers 1996–2000, the post-1994 period; handle with care in wording")
    for ind, p0 in [("facility_birth", "1992"), ("vacc_basic", "2000"), ("mcpr", "1992"), ("anc_4plus", "1992")]:
        a, b = get(ind, "trend", "Rwanda", p0), get(ind, "trend", "Rwanda", "2025")
        add(f"{ind}_rise", "3 What changed", f"{a['label']}: {a['value_as_printed']}% ({p0}) → {b['value_as_printed']}% (2025)",
            b["v"] - a["v"], "percentage points", "new − old", cite(a, b))
    # Significance of period-to-period changes that have CIs.
    m0, m1 = get("mmr", "trend", "Rwanda", "2019-20"), get("mmr", "trend", "Rwanda", "2025")
    z, p = ztest(m0["v"], m1["v"], se(m0), se(m1))
    add("mmr_change_test", "2 Progress", f"Maternal mortality ratio {m0['value_as_printed']} → {m1['value_as_printed']}: the change is NOT statistically significant",
        m0["v"] - m1["v"], "deaths per 100,000", "z = (a − b) / √(SEa² + SEb²), SE = (CI high − CI low)/4", cite(m0, m1), verdict(z, p),
        "Do not headline the MMR drop; use PRMR 1,071 → 172 for the long view")
    p0, p1 = get("prmr", "trend", "Rwanda", "2000"), get("prmr", "trend", "Rwanda", "2025")
    z, p = ztest(p0["v"], p1["v"], se(p0), se(p1))
    add("prmr_change_test", "2 Progress", "Pregnancy-related mortality fall since 2000 is statistically significant",
        p0["v"] - p1["v"], "deaths per 100,000", "two-sample z-test on CIs", cite(p0, p1), verdict(z, p))
    u0, u1 = get("u5mr", "period", "Rwanda", "2010–2015"), get("u5mr", "period", "Rwanda", "2021–2025")
    z, p = ztest(u0["v"], u1["v"], se(u0), se(u1))
    add("u5mr_period_test", "1 Hook", f"Within this survey, under-5 mortality fell from {u0['value_as_printed']} (2010–15) to {u1['value_as_printed']} (2021–25)",
        u0["v"] - u1["v"], "deaths per 1,000", "two-sample z-test on CIs", cite(u0, u1), verdict(z, p),
        "Periods from one birth history are not fully independent; z-test is approximate")
    # Linear trend in stunting, 2005-2025 (maths for the module: least squares).
    pts = [get("stunted", "trend", "Rwanda", s) for s in ["2005", "2010", "2014-15", "2019-20", "2025"]]
    b, a, r = ols([int(x["year"]) for x in pts], [x["v"] for x in pts])
    add("stunted_ols", "4 Problem", f"Since 2005 stunting has fallen about {-b:.1f} percentage points per year (straight-line fit, r = {r:.3f})",
        -b, "percentage points per year", "least-squares slope of stunting on survey year, 2005–2025", cite(*pts))

# 4 Problem: target gap and projection -------------------------------------------------------
def target():
    s0, s1 = get("stunted", "trend", "Rwanda", "2019-20"), get("stunted", "trend", "Rwanda", "2025")
    tgt, tyear, tsrc = NST2_TARGET
    rate = aarr(s0["v"], s1["v"], 5)
    proj = s1["v"] * (1 - rate) ** (tyear - 2025)
    need = aarr(s1["v"], tgt, tyear - 2025)
    add("stunted_projection_2029", "4 Problem", f"At the 2020–2025 pace ({rate*100:.1f}%/yr), stunting would be about {proj:.0f}% in {tyear}, not the {tgt:.0f}% target",
        proj, "% (projection)", f"27 × (1 − {rate:.3f})^{tyear-2025}", cite(s0, s1) + f"; target: {tsrc}",
        caveat="Our projection, not an NISR figure; label clearly as an estimate")
    add("stunted_needed_rate", "4 Problem", f"Reaching {tgt:.0f}% by {tyear} needs a {need*100:.0f}% fall every year, about {need/rate:.1f}× the recent pace",
        need * 100, "% per year needed", f"1 − ({tgt}/27)^(1/{tyear-2025})", cite(s1) + f"; target: {tsrc}")
    add("stunted_children_in_4", "4 Problem", f"About 1 in {100/s1['v']:.1f} children under 5 is stunted (roughly 1 in 4)",
        100 / s1["v"], "children", "100 / 27", cite(s1))

# 5 Gaps: who is left behind ------------------------------------------------------------------
def gaps():
    pairs = [("Mother’s education", "No education", "More than secondary"), ("Wealth quintile", "Lowest", "Highest"),
             ("Residence", "Rural", "Urban"), ("Province", "Northern Province", "City of Kigali"),
             ("Province", "Western Province", "City of Kigali"), ("Sex", "Male", "Female"),
             ("Size at birth", "Very small", "Average or larger")]
    for gt, hi, lo in pairs:
        a, b = get("stunted", gt, hi), get("stunted", gt, lo)
        sig = ""
        if se(a) and se(b):
            sig = verdict(*ztest(a["v"], b["v"], se(a), se(b)))
        else:
            # Binomial SE × design effect when the report gives no CI for the group.
            sa = DEFT_HAZ * math.sqrt(a["v"] * (100 - a["v"]) / float(a["n"]))
            sb = DEFT_HAZ * math.sqrt(b["v"] * (100 - b["v"]) / float(b["n"]))
            sig = verdict(*ztest(a["v"], b["v"], sa, sb)) + " (approx. SE = DEFT × binomial)"
        add(f"stunted_gap_{gt[:8]}_{hi[:6]}", "5 Gaps",
            f"Stunting: {hi} {a['value_as_printed']}% vs {lo} {b['value_as_printed']}% — {a['v']/b['v']:.1f}× higher, {a['v']-b['v']:.1f} points",
            a["v"] / b["v"], "ratio", "high ÷ low (and high − low in points)", cite(a, b), sig)
    # Under-5 mortality gaps (10-year rates).
    for gt, hi, lo in [("Wealth quintile", "Lowest", "Highest"), ("Mother’s education", "No education", "More than secondary"),
                       ("Province", "Eastern Province", "Northern Province")]:
        a, b = get("u5mr", gt, hi, "2016-2025 (10y)"), get("u5mr", gt, lo, "2016-2025 (10y)")
        cav = "Uses a value in ( ): 25–49 cases, low confidence" if "low_n" in a["flag"] + b["flag"] else ""
        add(f"u5mr_gap_{gt[:8]}", "5 Gaps", f"Under-5 deaths: {hi} {a['value_as_printed']} vs {lo} {b['value_as_printed']} per 1,000 ({a['v']/b['v']:.1f}×)",
            a["v"] / b["v"], "ratio", "high ÷ low", cite(a, b), caveat=cav + ("; " if cav else "") + "No CIs by group in the report; no significance test")

# District map -------------------------------------------------------------------------------
def districts():
    ds = sorted((get("stunted", "District", g["group"]) for g in D if g["indicator"] == "stunted" and g["group_type"] == "District"),
                key=lambda r: r["v"])
    nat = get("stunted", "national", "Rwanda")
    lo, hi = ds[0], ds[-1]
    s = lambda r: DEFT_HAZ * math.sqrt(r["v"] * (100 - r["v"]) / float(r["n"]))
    add("district_range", "4 Problem", f"District stunting ranges from {lo['value_as_printed']}% ({lo['group']}) to {hi['value_as_printed']}% ({hi['group']}), {hi['v']/lo['v']:.1f}× apart",
        hi["v"] / lo["v"], "ratio", "max ÷ min of 30 districts", cite(lo, hi), verdict(*ztest(hi["v"], lo["v"], s(hi), s(lo))) + " (approx. SE)")
    above = [r for r in ds if ztest(r["v"], nat["v"], s(r), se(nat))[1] < 0.05 and r["v"] > nat["v"]]
    below = [r for r in ds if ztest(r["v"], nat["v"], s(r), se(nat))[1] < 0.05 and r["v"] < nat["v"]]
    add("districts_above_national", "4 Problem",
        f"{len(above)} of 30 districts are significantly above the national 26.8%: " + ", ".join(f"{r['group']} {r['value_as_printed']}" for r in reversed(above)),
        len(above), "districts", "z-test district vs national, p < 0.05", cite(nat) + "; Table D.4 p.446",
        caveat="District SEs approximated as DEFT(1.234) × binomial; report gives no district CIs. District is part of the national sample, so the test is slightly conservative")
    add("districts_below_national", "4 Problem",
        f"{len(below)} districts are significantly below national: " + ", ".join(f"{r['group']} {r['value_as_printed']}" for r in below),
        len(below), "districts", "same test", cite(nat) + "; Table D.4 p.446", caveat="Same approximation")
    top5 = ds[-5:]
    add("top5_districts", "4 Problem", "Highest stunting: " + ", ".join(f"{r['group']} ({r['parent'].split()[0]}) {r['value_as_printed']}%" for r in reversed(top5)),
        top5[-1]["v"], "%", "rank", cite(*top5))
    # Ecological correlation: district stunting vs exclusive breastfeeding (same 30 districts).
    bf = {r["group"]: float(r["value"]) for r in D if r["indicator"] == "bf_exclusive" and r["group_type"] == "District" and r["value"]}
    xs = [bf[r["group"]] for r in ds if r["group"] in bf]; ys = [r["v"] for r in ds if r["group"] in bf]
    b, a, r = ols(xs, ys)
    add("corr_district_bf_stunting", "6 First 1,000 days", f"Across districts, exclusive breastfeeding and stunting show a weak negative correlation (r = {r:.2f})",
        r, "Pearson r", "OLS / Pearson on 30 district pairs", "Tables D.4 (p.446), D.5 (p.447)",
        caveat="Ecological, small n per district for breastfeeding (0–5 months); do NOT claim causation")

# 6 First 1,000 days --------------------------------------------------------------------------
def first1000():
    for ind in ["bf_early", "bf_exclusive", "diet_mdd", "diet_mmf", "diet_mad"]:
        r = get(ind, "national", "Rwanda")
        add(f"{ind}_2025", "6 First 1,000 days", f"{r['label']}: {r['value_as_printed']}% ({r['unit']})", r["v"], "%", "as printed", cite(r))
    mad = get("diet_mad", "national", "Rwanda")
    add("diet_mad_gap", "6 First 1,000 days", f"Only about {round(mad['v']/10)} in 10 children aged 6–23 months get a minimum acceptable diet",
        mad["v"] / 10, "children per 10", "27.9 / 10, rounded", cite(mad))
    age = [get("stunted", "Age in months", g) for g in ["<6", "6–11", "12–23", "24–35"]]
    add("stunting_by_age", "6 First 1,000 days", "Stunting jumps from " + " → ".join(f"{r['value_as_printed']}% ({r['group']} mo)" for r in age) + ": damage builds in the first 2 years",
        age[2]["v"] - age[0]["v"], "percentage points, <6 → 12–23 months", "difference", cite(*age))

# 3 Cohort: 1,000 babies at today's rates (illustrative; mixes a 5-year death rate with a point-in-time stunting rate).
def cohort():
    u5 = get("u5mr", "period", "Rwanda", "2021–2025")
    surv = 1000 - u5["v"]
    qs = [get("stunted", "Wealth quintile", g) for g in ["Lowest", "Second", "Middle", "Fourth", "Highest"]]
    total_n = sum(float(q["n"]) for q in qs)
    stunted_sum = 0
    for q in qs:
        kids = surv * float(q["n"]) / total_n
        st = kids * q["v"] / 100
        stunted_sum += st
        add(f"cohort_{q['group'].lower()}", "3 Cohort", f"{q['group']} 20%: {kids:.0f} children, {st:.0f} stunted",
            st, "children of 1,000 born", "(1000 − U5MR) × share of measured children in quintile × stunting rate", cite(u5, q),
            caveat="Illustrative cohort at 2025 rates; quintile share from Table 11.1 child counts")
        insights[-1]["kids"] = round(kids)
    add("cohort_survivors", "3 Cohort", f"Of 1,000 babies, {u5['v']:.0f} die before age 5 and {surv:.0f} survive", surv, "children",
        "1000 − U5MR", cite(u5))
    add("cohort_stunted", "3 Cohort", f"Of the {surv:.0f} survivors, about {stunted_sum:.0f} are stunted", stunted_sum, "children",
        "sum over quintiles", cite(u5, *qs), caveat="Illustrative cohort at 2025 rates")

def write():
    with open(ROOT / "data/insights.csv", "w", newline="") as f:
        w = csv.DictWriter(f, list(insights[0]) + ["kids"], restval=""); w.writeheader(); w.writerows(insights)

def self_check():
    v = {i["id"]: i["value"] for i in insights}
    assert abs(v["u5mr_drop_2000"] - 81.63) < 0.01          # (196-36)/196
    assert abs(v["u5mr_aarr_2000"] - 6.55) < 0.05           # 1-(36/196)^(1/25)
    assert v["u5mr_per1000"] == 160
    assert abs(v["stunted_needed_rate"] - 13.65) < 0.1      # 1-(15/27)^(1/4)
    assert "NOT" in next(i for i in insights if i["id"] == "mmr_change_test")["significance"]
    assert len({i["id"] for i in insights}) == len(insights), "duplicate insight ids"
    # Quintile cohort must reproduce the national rate: 964 × 26.8% ≈ 258.
    assert abs(v["cohort_stunted"] - v["cohort_survivors"] * 0.268) < 2, v["cohort_stunted"]
    print(f"{len(insights)} insights; self-check passed")

if __name__ == "__main__":
    trends(); target(); gaps(); districts(); first1000(); cohort(); write(); self_check()
    for i in insights:
        print(f"[{i['section']}] {i['statement']}" + (f"  | {i['significance']}" if i["significance"] else ""))
