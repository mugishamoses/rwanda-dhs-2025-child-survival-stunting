# Phase 6 — Storyboard (the poster's words, in order)

The numbers come from `data/selected_insights.csv`; every figure below is traceable there.
Scores for all 49 insights are in `data/insight_scores.csv`. To change the story, edit `STORY` in `analysis/select.py` and re-run it.

**Title:** From 196 to 36: Rwanda saved its children. Now it must help them grow.
**Subtitle:** What the 2025 Rwanda Demographic and Health Survey tells us about the first five years of life.

---

### 1 Hook: "We kept them alive"
- **Lead number:** 196 → 36
- **Headline:** In 2000, about 196 of every 1,000 babies died before age 5. Today it is 36.
- **Support:** 160 more children in every 1,000 now reach their 5th birthday (−82%).
- **Footnote:** Deaths per 1,000 live births in the 5 years before each survey. Source: RDHS 2025, Figure 8.1, p.138.

### 2 Progress: "Mothers too"
- **Lead number:** 1,071 → 172
- **Headline:** Deaths linked to pregnancy fell by 84% since 2000.
- **Footnote:** Pregnancy-related mortality ratio per 100,000 live births. Source: Table C.18, p.442.
- **Do not use** "maternal mortality 203 → 149". That change is not statistically significant (p = 0.29).

### 3 What changed: "Care reached every mother"
Show four small charts side by side, same scale, 0–100%:

| Indicator | Then | 2025 |
|---|---|---|
| Births in a health facility | 25% (1992) | 98% |
| Mothers with 4+ antenatal visits | 12% (1992) | 78% |
| Married women using modern contraception | 13% (1992) | 64% |
| Children with all basic vaccines | 76% (2000) | 94% |

**Footnote:** Figures 9.2 (p.149), 9.1 (p.146), Table 7.4.1 (p.121), Figure 10.2 (p.184).

### 4 The problem: "But 1 in 4 still don't grow"
- **Lead number:** 27%. Show it as an icon grid of 100 children with 27 highlighted.
- **Headline:** Stunting fell from 51% (2005) to 27%, but about 1 in 4 children under 5 is still too short for their age.
- **Map:** 30 districts, from 8.7% in Nyarugenge to 38.8% in Gicumbi (4.5 times higher).
- **Worst five:** Gicumbi 38.8, Burera 37.6, Ngororero 35.8, Rutsiro 33.8, Karongi 33.5 (North and West).
- **Footnote:** Height-for-age below −2 SD, WHO 2006 standards. Sources: Booklet p.22 (trend), Table 11.1 p.219, Table D.4 p.446.

### 5 Who is left behind
Dot plot with one row per comparison:

| Comparison | Stunting | Times higher |
|---|---|---|
| Mother has no education vs more than secondary | 37.8% vs 5.8% | 6.5× |
| Poorest 20% vs richest 20% of families | 39.8% vs 9.2% | 4.3× |
| Northern Province vs City of Kigali | 32.7% vs 14.2% | 2.3× |

**Footnote:** All three gaps are statistically significant (p < 0.001). Source: Table 11.1, p.219.

### 6 First 1,000 days: "The damage happens early"
- **Lead:** Stunting climbs from 17% (under 6 months) to 33% (12–23 months).
- **Support:** Only about 3 in 10 children aged 6–23 months get a minimum acceptable diet (26.9%).
- **Message:** Breastfeeding protects children early, then the diet after 6 months falls short.
- **Footnote:** Tables 11.1 (p.219) and 11.8 (p.227).

### 7 Call to action: "Faster, or we miss 2029"
- **Lead:** About 23% in 2029 at today's pace, against the 15% target.
- **Support:** Reaching 15% needs stunting to fall about 14% every year, roughly 3.5 times faster than now.
- **Actions:** Feed varied food after 6 months · keep growth checks · keep girls in school · focus on the North and West.
- **Footnote:** Projection by the authors (compound rate, 2019-20 → 2025, carried forward). Target from NST2 2024–2029 (MINECOFIN).

---

**Source line (footer):** Data: National Institute of Statistics of Rwanda (NISR), Rwanda Demographic and Health Survey 2025 (RDHS7), Final Report and Booklet. Target: NST2 2024–2029. Calculations by the authors.

**Wording rules**
- Say "about 1 in 4", not "26.8%", in headlines.
- Mortality rates refer to the 5 years before each survey.
- Label the 2029 figure as an estimate, not an NISR number.
- Show "<1" exactly as printed.
