"""Phase 7 - Chart specifications: one spec per chart, data pulled from the clean dataset.

Usage: python3 -I analysis/specs.py
Output: output/web/data.json   (palette + every chart's spec AND its exact data rows; read by poster and web)
        data/CHART_SPECS.md    (the same, for people)
Fails if any chart's query returns an unexpected number of rows.
"""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = list(csv.DictReader(open(ROOT / "data/rdhs2025_clean.csv")))
INS = {r["id"]: r for r in csv.DictReader(open(ROOT / "data/insights.csv"))}

# Validated with dataviz validate_palette.js: orange/blue --pairs all (light+dark) PASS; ramps --ordinal PASS.
PALETTE = {
    "light": {"surface": "#ffffff", "page": "#f1f1ef", "ink": "#1d1d1b", "ink2": "#55544f", "muted": "#8d8c86",
              "grid": "#e4e3de", "axis": "#c4c3bc", "data": "#2a78d6", "focus": "#eb6834", "context": "#c4c3bc",
              "ramp": ["#f09460", "#e46f36", "#c9561f", "#9e3f12", "#6e2a0a"]},
    "dark": {"surface": "#1e1f21", "page": "#17181a", "ink": "#f0efec", "ink2": "#c3c2b7", "muted": "#8d8c86",
             "grid": "#2e2f31", "axis": "#45464a", "data": "#3987e5", "focus": "#d95926", "context": "#55565a",
             "ramp": ["#94391a", "#b84c1f", "#d95926", "#ee8a57", "#f6b893"]},  # dark: more = lighter
    "roles": "orange = the story's call to attention (stunting, the gap); blue = survival/progress; grays = context",
}
MAP_BREAKS = [15, 20, 26.8, 33]  # <15 meets 2029 target | 15-20 | 20-26.8 below national | 26.8-33 | >=33
MAP_LABELS = ["< 15% (2029 target met)", "15–20%", "20–26.8% (below national)", "26.8–33%", "≥ 33%"]

def q(ind, group_type, periods=None, n=None):
    rs = [r for r in D if r["indicator"] == ind and r["group_type"] == group_type and (periods is None or r["period"] in periods)]
    assert n is None or len(rs) == n, f"{ind}/{group_type}/{periods}: expected {n} rows, got {len(rs)}"
    keep = ["indicator", "label", "unit", "group", "parent", "period", "year", "value", "value_as_printed",
            "ci_low", "ci_high", "n", "flag", "table", "printed_page", "pdf_page", "source"]
    return [{k: r[k] for k in keep} for r in rs]

def pick(ind, group_type, groups, period="2025"):
    rs = [r for g in groups for r in q(ind, group_type, [period]) if r["group"] == g]
    assert len(rs) == len(groups), f"{ind}/{group_type}: missing one of {groups}"
    return rs

S = ["1992", "2000", "2005", "2010", "2014-15", "2019-20", "2025"]

CHARTS = [
    dict(id="hero", section="Masthead", form="three hero numbers", title="Rwanda's children in three numbers", subtitle="",
         data=pick("u5mr", "trend", ["Rwanda"], "2025") + pick("stunted", "national", ["Rwanda"]),
         target={"year": 2029, "value": 15, "label": "NST2 target", "source": "NST2 2024–2029 (MINECOFIN)"},
         encoding="huge thin numerals, mono caps labels", highlight="26.8%", annotations=[], insights=["stunted_children_in_4"],
         alt="36 deaths per 1,000 births before age 5; 26.8% of children under 5 stunted; target 15% by 2029."),
    dict(id="rings", section="01 Survival", form="isometric stacked rings (hourglass), ring width ∝ under-5 mortality",
         title="Fewer and fewer children lost", subtitle="Under-5 deaths per 1,000 live births, 5 years before each survey",
         data=q("u5mr", "trend", S, 7),
         encoding="one ellipse per survey on a vertical spine; rx linear in rate from a shared zero; value label at each ring",
         highlight="2000 (196) and 2025 (36)", annotations=["196", "36", "−82%"], hover="survey, rate",
         insights=["u5mr_drop_2000", "u5mr_per1000", "u5mr_1992_2000"],
         alt="Seven rings shrinking from top to bottom: 151 (1992), 196 (2000), 152, 76, 50, 45, 36 (2025) deaths per 1,000."),
    dict(id="prmr", section="01 Survival", form="dot + 95% CI whisker per survey",
         title="Mothers too: pregnancy-related deaths −84%", subtitle="Per 100,000 live births",
         data=q("prmr", "trend", None, 6), encoding="dots with hairline CI whiskers", highlight="2000 and 2025",
         annotations=["1,071", "172"], hover="value + CI", insights=["prmr_drop_2000", "prmr_change_test"],
         note="Maternal mortality ratio 203→149 is NOT significant (p = 0.29) and is not shown.",
         alt="Pregnancy-related mortality ratio: 1,071 (2000), 750, 476, 210, 226, 172 (2025), with confidence intervals."),
    dict(id="care", section="02 Care", form="isometric health centre with 4 numbered callouts + sparkline each",
         title="Care reached every mother", subtitle="Share of births, mothers or children, first survey → 2025",
         data=q("facility_birth", "trend", S, 7) + q("anc_4plus", "trend", S, 7) + q("mcpr", "trend", S, 7) + q("vacc_basic", "trend", S, 6),
         encoding="callout = first → last value + 0–100% sparkline (shared scale)", highlight="2025 values",
         annotations=["25→98%", "12→78%", "13→64%", "76→94%"], hover="per-survey value on sparklines",
         insights=["facility_birth_rise", "anc_4plus_rise", "mcpr_rise", "vacc_basic_rise"],
         alt="Births in a health facility rose from 25% to 98%; 4+ antenatal visits 12% to 78%; modern contraception 13% to 64%; full basic vaccination 76% to 94%."),
    dict(id="cohort", section="03 Cohort", form="flow (Sankey) 1,000 births → survive/die → wealth quintile → stunted/not",
         title="Follow 1,000 babies born today", subtitle="Illustrative cohort at 2025 rates",
         data=q("u5mr", "period", ["2021–2025"], 1) + pick("stunted", "Wealth quintile", ["Lowest", "Second", "Middle", "Fourth", "Highest"]),
         cohort={k: {"stunted": round(float(INS[f"cohort_{k}"]["value"])), "kids": int(INS[f"cohort_{k}"]["kids"])}
                 for k in ["lowest", "second", "middle", "fourth", "highest"]},
         encoding="flow width ∝ children; stunted flows fade into orange; big thin numbers at each stage",
         highlight="stunted flows", annotations=["1,000", "36 die before age 5", "964 survive", "258 stunted"], hover="flow: group, children",
         insights=["cohort_survivors", "cohort_stunted", "cohort_lowest", "cohort_highest"],
         note="Mixes the 2021–25 under-5 death rate with the 2025 stunting rate; quintile shares from Table 11.1 child counts.",
         alt="Of 1,000 babies, 36 die before age 5. Of 964 survivors, 258 are stunted: 87 of 218 in the poorest fifth but 16 of 174 in the richest."),
    dict(id="map", section="04 Where", form="isometric extruded choropleth, 30 districts, height ∝ stunting %, orange ordinal ramp",
         title="Where children are stunted", subtitle="% of children under 5, by district, 2025",
         data=q("stunted", "District", ["2025"], 30), geo="assets/geo/rwa_adm2.geojson (geoBoundaries, CC BY 4.0)",
         breaks=MAP_BREAKS, break_labels=MAP_LABELS, highlight="Gicumbi, Burera, Ngororero, Rutsiro, Karongi",
         encoding="district raised by value from a shared base; top face = class colour; side faces darker; numbered callouts on top 5",
         annotations=["Nyarugenge 8.7%", "Gicumbi 38.8%", "4.5× apart"], hover="district, province, %, n",
         insights=["district_range", "top5_districts", "districts_above_national"], table_view=True,
         alt="Map of 30 districts raised by stunting: lowest in Kigali (Nyarugenge 8.7%), highest in the North and West (Gicumbi 38.8%, Burera 37.6%)."),
    dict(id="gaps", section="04 Where", form="dumbbell, 3 rows",
         title="Who is left behind", subtitle="% of children under 5 who are stunted, 2025",
         data=pick("stunted", "Mother’s education", ["No education", "More than secondary"])
              + pick("stunted", "Wealth quintile", ["Lowest", "Highest"])
              + pick("stunted", "Province", ["Northern Province", "City of Kigali"]),
         encoding="better-off dot gray, worse-off dot orange, ratio at right", highlight="worse-off dots",
         annotations=["6.5×", "4.3×", "2.3×"], hover="group, %, n, CI",
         insights=["stunted_gap_Mother’s_No edu", "stunted_gap_Wealth q_Lowest", "stunted_gap_Province_Northe"],
         alt="Stunting 37.8% vs 5.8% by mother's education, 39.8% vs 9.2% poorest vs richest, 32.7% North vs 14.2% Kigali."),
    dict(id="age", section="05 First 1,000 days", form="isometric columns, 6 age bands",
         title="The damage happens early", subtitle="% stunted by child's age in months",
         data=pick("stunted", "Age in months", ["<6", "6–11", "12–23", "24–35", "36–47", "48–59"]),
         encoding="isometric prisms from a shared base; 12–23 in orange", highlight="12–23 months",
         annotations=["17% → 33% between 6 months and 2 years"], hover="age band, %, n", insights=["stunting_by_age"],
         alt="Stunting by age: 16.7% under 6 months, 19.8% at 6–11, 33.2% at 12–23, then 30.6%, 27.2%, 24.6%."),
    dict(id="diet", section="05 First 1,000 days", form="isotype row of 10 + stat tiles",
         title="Only 3 in 10 eat well enough", subtitle="Children 6–23 months with a minimum acceptable diet",
         data=pick("diet_mad", "national", ["Rwanda"]) + pick("diet_mdd", "national", ["Rwanda"]) + pick("diet_mmf", "national", ["Rwanda"])
              + pick("bf_exclusive", "national", ["Rwanda"]),
         encoding="10 icons, 2.7 filled", highlight="filled icons", annotations=["26.9%"], insights=["diet_mad_gap"],
         alt="Of 10 children aged 6–23 months, about 3 get a minimum acceptable diet (26.9%); 82% of babies under 6 months are exclusively breastfed."),
    dict(id="timeline", section="06 Timeline", form="survey timeline 1992 → 2029 with two value rows + target",
         title="Seven surveys, one direction", subtitle="Under-5 deaths per 1,000 and % stunted at each survey; 2029 = estimate vs target",
         data=q("u5mr", "trend", S, 7) + q("stunted", "trend", None, 6),
         projection={"year": 2029, "value": round(float(INS["stunted_projection_2029"]["value"]), 1), "label": "≈23% at today's pace (authors' estimate)"},
         target={"year": 2029, "value": 15, "label": "NST2 target 15%", "source": "NST2 2024–2029 (MINECOFIN)"},
         encoding="dots on a horizontal axis by real year; values stacked above (deaths) and below (stunting); 2029 projection dotted, target ring",
         highlight="2029 gap", annotations=["needs ~14% fall per year (3.5× today's pace)"], hover="survey, both values",
         insights=["stunted_projection_2029", "stunted_needed_rate", "stunted_drop_2005"],
         alt="Timeline of surveys 1992–2025: under-5 deaths fall from 196 to 36; stunting falls from 51% to 27%. At today's pace stunting would be about 23% in 2029, above the 15% target."),
]

def main():
    out = ROOT / "output/web"
    out.mkdir(parents=True, exist_ok=True)
    for c in CHARTS:
        for i in c["insights"]:
            assert i in INS, f"{c['id']}: unknown insight {i}"
        c["insight_text"] = [INS[i]["statement"] for i in c["insights"]]
        main = sorted({(t if 'p.' in t else f"{t} p.{r['printed_page'] or r['pdf_page']}") for r in c["data"] for t in [r['table'].split(';')[0]]})
        cis = sorted({p.strip()[3:] for r in c["data"] for p in r["table"].split(";")[1:]})
        src = "RDHS 2025 Booklet" if all("Booklet" in r["source"] for r in c["data"]) else "RDHS 2025 Final Report"
        c["footnote"] = f"Source: NISR, {src}, " + "; ".join(main) + (f" (95% CI: Table {', '.join(cis)})" if cis else "") \
            + (f". Target: {c['target']['source']}. 2029 value is the authors' estimate" if c.get("target") else "")
        assert c["data"] and c.get("alt"), c["id"]
    doc = dict(title="From 196 to 36: Rwanda saved its children. Now it must help them grow.",
               source_line="Data: NISR, Rwanda Demographic and Health Survey 2025 (RDHS7). Target: NST2 2024–2029. Calculations by the authors.",
               palette=PALETTE, charts=CHARTS)
    (out / "data.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))

    md = ["# Phase 7 — Chart specifications\n", "Generated by `analysis/specs.py`. The machine version (with data rows) is `output/web/data.json`.\n",
          "## Palette (validated: all checks PASS, light and dark)\n",
          f"- Blue `{PALETTE['light']['data']}` = data · Orange `{PALETTE['light']['focus']}` = focus (sparingly) · Gray = context",
          f"- Map ramp (light): {' → '.join(PALETTE['light']['ramp'])}; breaks {MAP_BREAKS}",
          "- Marks: 2px lines, ≥8px dots with 2px surface ring, columns ≤24px with 4px rounded tops, hairline solid gridlines, text in ink tokens (never series colour)\n"]
    for c in CHARTS:
        md += [f"## {c['id']} — {c['section']}", f"**{c['title']}**: {c['subtitle']}", "",
               f"- **Form:** {c['form']}", f"- **Encoding:** {c['encoding']}", f"- **Highlight:** {c['highlight']}",
               f"- **Annotations:** {' · '.join(c['annotations'])}", f"- **Hover:** {c.get('hover', 'none (static figure)')}",
               f"- **Data rows:** {len(c['data'])} ({', '.join(sorted({r['indicator'] for r in c['data']}))})",
               f"- **Alt text:** {c['alt']}", f"- **Footnote:** {c['footnote']}"]
        md += [f"- **Note:** {c['note']}"] if c.get("note") else []
        md += [""]
    (ROOT / "data/CHART_SPECS.md").write_text("\n".join(md))
    print(f"{len(CHARTS)} charts specified; {sum(len(c['data']) for c in CHARTS)} data rows exported to output/web/data.json")

if __name__ == "__main__":
    main()
