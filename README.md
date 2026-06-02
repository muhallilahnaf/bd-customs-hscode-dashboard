# Bangladesh Customs Import Analytics Dashboard

A lightweight, fully static analytics dashboard for NBR customs import data.
No server, no database, no paid tools required.

---

## Project Structure

```
customs_dashboard/
├── index.html              ← Open this in your browser
├── extract_pdf.ipynb       ← Run this every month after adding new PDFs
├── generate_data.py        ← Run this every month after generating new CSVs
├── data/
│   ├── pdf/                ← Drop your monthly PDF files here
│   ├── raw/                ← Monthly CSV files are generated here
│   │   ├── im4_2026_01.csv
│   │   ├── im7_2026_01.csv
│   │   └── ...
│   └── processed/
│       └── dashboard_data.json   ← Auto-generated, do not edit
└── README.md
```

---

## PDF File Naming Convention

Your PDF files must follow this naming pattern:

```
{type}_{year}_{month}.pdf
```

Examples:
- `im4_2026_01.pdf`  — IM4 data, January 2026
- `im7_2025_12.pdf`  — IM7 data, December 2025
- `im4_2026_03.pdf`  — IM4 data, March 2026

**Required CSV columns:**
```
hscode, description, net_wt_kg, assess_value_bdt, invoice_value_bdt
```

---

## Monthly Workflow

**Step 1:** Download the new month's PDFs from the [NBR website](https://nbr.gov.bd/publications/all-publication/eng) and place them in the `data/pdf/` folder with appropriate naming convention `{type}_{year}_{month}.pdf`.

**Step 2:** Run your PDF extraction script `extract_pdf.ipynb` to generate CSVs into `data/raw/`.

**Step 3:** Run the data generator:
```bash
python generate_data.py
```

**Step 4:** Open (or refresh) `index.html` in your browser.

That's it. The dashboard auto-updates from the new JSON.

---

## First-Time Setup

**Requirements:** Python 3.7+ and pandas

Install pandas if you don't have it:
```bash
pip install pandas pdfplumber tqdm
```

**To open the dashboard:**

Option A — Double-click `index.html` (works in most browsers)

Option B — Serve locally (recommended, avoids browser security restrictions):
```bash
# Python built-in server
cd customs_dashboard
python -m http.server 8000
# Then open: http://localhost:8000
```

---

## Dashboard Pages

| Page | What's shown |
|------|-------------|
| **Overview** | KPI cards, monthly trend, IM4/IM7 pie, top HS codes, chapter bar, growth chart |
| **Trends** | IM4 vs IM7 stacked bar, value vs weight dual-axis, assessed vs invoice gap, top 5 chapters line chart |
| **Chapters** | Treemap by value, chapter weight bar, full chapter table |
| **HS Code Explorer** | Searchable/filterable/sortable table of all HS codes, click any row for detail panel with monthly breakdown + mini chart, export filtered results to CSV |

---

## Analytics Computed

- Total and monthly assessed value, invoice value, net weight
- Month-over-month growth %
- IM4 vs IM7 breakdown by period
- Top 25 HS codes by value and weight (with monthly sparkline data)
- Fastest growing HS codes (MoM)
- HS chapter aggregation (2-digit rollup with standard names)
- Top 5 chapters monthly trend
- Per-HS-code monthly detail (value, weight, tax type per period)

---

## Notes

- All monetary values are in **BDT (Bangladeshi Taka)**
- The dashboard reads `data/processed/dashboard_data.json` — this file is regenerated every time you run `generate_data.py`
- Old months are preserved automatically — just keep all CSVs in `data/raw/`
- The search page supports partial matching on both HS code number and description text
