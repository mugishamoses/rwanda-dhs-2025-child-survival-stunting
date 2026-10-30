# data/raw: Phase 2 extraction (values exactly as printed)

Source: RDHS 2025 Final Report, except where a row says Booklet.
Regenerate the tables with `python3 -I analysis/extract.py` (includes a self-check).

| File | What it is |
|---|---|
| `t<id>.csv` | One table. `c1..cN` follow the column order in the PDF; the column names are in `t<id>.txt` (HEADER section) |
| `t<id>.txt` | Caption, PDF pages, column header block, footnotes |
| `figures_transcribed.csv` | Trend series (1992–2025) read by hand from labelled figures 8.1, 9.1, 9.2, 9.3, 9.5, 10.2 and the Booklet nutrition page; each row has a text check |
| `figures_province_2025.csv` | Province values from Maps 9.1 and 10.1 |
| `figures_other.csv` | Under-5 mortality by mother's education (Figure 8.2) |

Markers:
- `(x)` = based on 25–49 unweighted cases (use with caution)
- `*` = suppressed (fewer than 25 cases)
- `[x]` = rate partly truncated (5.3.2)
- `[a;b]` = confidence interval (C.18)
- `na` = not applicable
- `CI` triples (8.1, 12.5) = estimate, lower, upper

Tables: 5.3.2 TFR trend · 7.4.1 contraception trend · 8.1–8.3 child mortality · 9.1/9.2 antenatal care · 9.7.1 place of delivery · 9.9 delivery assistance · 10.4 vaccination by group · 11.1 nutrition by group · 11.3/11.4 breastfeeding · 11.8 minimum diet · 12.5 maternal mortality ratio · B.2/B.11 sampling errors · C.18 pregnancy-related mortality trend · D.4 stunting by district · D.5 breastfeeding by district
