"""Phase 6 - Score every insight and pick the ones the infographic will carry.

Score 1-3 on: Big (size of change/gap), Reliable (significance, sample size),
Easy (one sentence for a non-technical reader), Actionable (points to something changeable).
Reliable is capped automatically: NOT significant or low-n caveat -> 1; own projection -> 2.

Usage: python3 -I analysis/select.py
Output: data/insight_scores.csv, data/selected_insights.csv
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INS = {r["id"]: r for r in csv.DictReader(open(ROOT / "data/insights.csv"))}

# id: Big Reliable Easy Actionable  (team judgement; edit and re-run to change the story)
SCORES = """
u5mr_drop_2000 3 3 3 2 | u5mr_aarr_2000 2 3 1 1 | u5mr_per1000 3 3 3 2 | u5mr_1992_2000 2 3 2 1 | u5mr_period_test 2 3 1 1
imr_drop_2000 2 3 2 1 | imr_aarr_2000 1 3 1 1 | nmr_drop_2000 2 3 2 2 | nmr_aarr_2000 1 3 1 1
prmr_drop_2000 3 3 2 2 | prmr_aarr_2000 2 3 1 1 | prmr_change_test 2 3 1 1 | mmr_change_test 1 3 1 1
tfr_drop_2000 2 3 2 1 | tfr_aarr_2000 1 3 1 1
facility_birth_rise 3 3 3 2 | vacc_basic_rise 2 3 3 2 | mcpr_rise 3 3 2 2 | anc_4plus_rise 3 3 3 2
stunted_drop_2005 3 3 3 2 | stunted_aarr_2005 2 3 1 1 | stunted_drop_2019-20 2 3 2 2 | stunted_aarr_2019-20 2 3 1 2
stunted_ols 2 3 1 1 | stunted_projection_2029 3 3 3 3 | stunted_needed_rate 3 3 2 3 | stunted_children_in_4 3 3 3 3
district_range 3 3 3 3 | districts_above_national 3 3 2 3 | districts_below_national 2 3 2 2 | top5_districts 3 3 3 3
stunted_gap_Mother’s_No_edu 3 3 3 3 | stunted_gap_Wealth_q_Lowest 3 3 3 3 | stunted_gap_Residenc_Rural 2 3 3 2
stunted_gap_Province_Northe 3 3 3 3 | stunted_gap_Province_Wester 3 3 3 3 | stunted_gap_Sex_Male 1 3 2 1 | stunted_gap_Size_at__Very_s 2 3 2 2
u5mr_gap_Wealth_q 2 3 3 2 | u5mr_gap_Mother’s 3 3 3 2 | u5mr_gap_Province 2 3 3 2
corr_district_bf_stunting 1 3 1 1 | bf_early_2025 2 3 3 2 | bf_exclusive_2025 2 3 3 2 | diet_mdd_2025 2 3 2 3
diet_mmf_2025 2 3 2 3 | diet_mad_2025 3 3 2 3 | diet_mad_gap 3 3 3 3 | stunting_by_age 3 3 3 3
cohort_survivors 3 3 3 2 | cohort_stunted 3 2 3 3 | cohort_lowest 3 2 3 3 | cohort_second 2 2 2 2 | cohort_middle 2 2 2 2
cohort_fourth 2 2 2 2 | cohort_highest 3 2 3 3
"""

# Poster section -> (lead insight ids in display order). Chosen from the top scorers below.
STORY = {
    "1 Hook": ["u5mr_drop_2000", "u5mr_per1000"],
    "2 Progress": ["prmr_drop_2000"],
    "3 What changed": ["facility_birth_rise", "anc_4plus_rise", "mcpr_rise", "vacc_basic_rise"],
    "3b Cohort": ["cohort_survivors", "cohort_stunted", "cohort_lowest", "cohort_highest"],
    "4 Problem": ["stunted_drop_2005", "stunted_children_in_4", "district_range", "top5_districts"],
    "5 Gaps": ["stunted_gap_Mother’s_No_edu", "stunted_gap_Wealth_q_Lowest", "stunted_gap_Province_Northe"],
    "6 First 1,000 days": ["stunting_by_age", "diet_mad_gap"],
    "7 Call to action": ["stunted_projection_2029", "stunted_needed_rate"],
}

def key(i):
    return i.replace(" ", "_")

def main():
    ids = {key(i): i for i in INS}
    scores = {}
    for part in SCORES.replace("\n", "|").split("|"):
        if part.strip():
            k, *s = part.split()
            assert k in ids, f"unknown insight id {k}"
            scores[ids[k]] = list(map(int, s))
    missing = set(INS) - set(scores)
    assert not missing, f"unscored insights: {missing}"

    rows = []
    for i, (b, r, e, a) in scores.items():
        ins = INS[i]
        if "NOT" in ins["significance"] or "low confidence" in ins["caveat"]:
            r = 1
        elif "projection" in ins["unit"] or "Our projection" in ins["caveat"]:
            r = min(r, 2)
        rows.append(dict(id=i, section=ins["section"], big=b, reliable=r, easy=e, actionable=a,
                         total=b + r + e + a, statement=ins["statement"]))
    rows.sort(key=lambda x: (x["section"], -x["total"]))

    chosen = {i for lst in STORY.values() for i in lst}
    for r in rows:
        r["selected"] = "yes" if key(r["id"]) in chosen else ""
    with open(ROOT / "data/insight_scores.csv", "w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)

    sel = []
    for sec, lst in STORY.items():
        for order, k in enumerate(lst, 1):
            i = ids[k]
            sc = next(r for r in rows if r["id"] == i)
            assert sc["reliable"] >= 2, f"{i} is not reliable enough for the poster"
            sel.append(dict(poster_section=sec, order=order, score=sc["total"], **{c: INS[i][c] for c in INS[i]}))
    with open(ROOT / "data/selected_insights.csv", "w", newline="") as f:
        w = csv.DictWriter(f, list(sel[0])); w.writeheader(); w.writerows(sel)

    for sec, lst in STORY.items():
        print(f"\n{sec}")
        for k in lst:
            r = next(r for r in rows if r["id"] == ids[k])
            print(f"  [{r['total']:>2}] {r['statement'][:120]}")
    print(f"\n{len(sel)} insights selected from {len(rows)}; all reliable >= 2")

if __name__ == "__main__":
    main()
