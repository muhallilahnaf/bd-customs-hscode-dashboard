"""
Bangladesh Customs Import Data - ETL Script
============================================
Run this script every month after generating new CSVs to data/raw/
Output: data/processed/dashboard_data.json

CSV filename format: {type}_{year}_{month}.csv
  Examples: im4_2026_01.csv, im7_2025_12.csv

CSV columns: hscode, description, net_wt_kg, assess_value_bdt, invoice_value_bdt
"""

import os
import re
import json
import pandas as pd
from pathlib import Path
from collections import defaultdict

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
RAW_DIR    = BASE_DIR / "data" / "raw"
OUT_DIR    = BASE_DIR / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── HS Code Chapter / Section mapping (first 2 digits → chapter name) ─────────
HS_CHAPTERS = {
    "01": "Live Animals", 
    "02": "Meat & Offal", 
    "03": "Fish & Seafood",
    "04": "Dairy & Eggs", 
    "05": "Other Animal Products", 
    "06": "Live Plants",
    "07": "Vegetables", 
    "08": "Fruits & Nuts", 
    "09": "Coffee, Tea & Spices",
    "10": "Cereals", 
    "11": "Milling Products", 
    "12": "Oil Seeds",
    "13": "Lac & Gums", 
    "14": "Vegetable Plaiting", 
    "15": "Animal/Veg Fats",
    "16": "Meat/Fish Preparations", 
    "17": "Sugars", 
    "18": "Cocoa",
    "19": "Cereal Preparations", 
    "20": "Veg Preparations", 
    "21": "Misc Food",
    "22": "Beverages", 
    "23": "Food Industry Residues", 
    "24": "Tobacco",
    "25": "Salt & Minerals", 
    "26": "Ores & Slag", 
    "27": "Mineral Fuels",
    "28": "Inorganic Chemicals", 
    "29": "Organic Chemicals", 
    "30": "Pharmaceuticals",
    "31": "Fertilisers", 
    "32": "Dyes & Pigments", 
    "33": "Perfumes & Cosmetics",
    "34": "Soaps & Waxes", 
    "35": "Albumins & Enzymes", 
    "36": "Explosives",
    "37": "Photographic Goods", 
    "38": "Misc Chemicals", 
    "39": "Plastics",
    "40": "Rubber", 
    "41": "Hides & Skins", 
    "42": "Leather Goods",
    "43": "Furskins", 
    "44": "Wood", 
    "45": "Cork", 
    "46": "Basketware",
    "47": "Pulp & Paper Waste", 
    "48": "Paper & Paperboard", 
    "49": "Printed Matter",
    "50": "Silk", 
    "51": "Wool", 
    "52": "Cotton", 
    "53": "Veg Textile Fibres",
    "54": "Man-Made Filaments", 
    "55": "Man-Made Staple Fibres",
    "56": "Wadding & Felt", 
    "57": "Carpets", 
    "58": "Special Woven Fabrics",
    "59": "Impregnated Textiles", 
    "60": "Knitted Fabrics", 
    "61": "Knitted Apparel",
    "62": "Woven Apparel", 
    "63": "Other Textile Articles", 
    "64": "Footwear",
    "65": "Headgear", 
    "66": "Umbrellas", 
    "67": "Feathers & Artificial Flowers",
    "68": "Stone & Plaster Articles", 
    "69": "Ceramic Products", 
    "70": "Glass",
    "71": "Precious Metals & Jewellery", 
    "72": "Iron & Steel",
    "73": "Iron & Steel Articles", 
    "74": "Copper", 
    "75": "Nickel",
    "76": "Aluminium", 
    "78": "Lead", 
    "79": "Zinc", 
    "80": "Tin",
    "81": "Other Base Metals", 
    "82": "Tools & Cutlery", 
    "83": "Misc Metal Articles",
    "84": "Machinery & Mechanical", 
    "85": "Electrical Equipment",
    "86": "Railway Equipment", 
    "87": "Vehicles", 
    "88": "Aircraft",
    "89": "Ships & Boats", 
    "90": "Optical & Medical Instruments",
    "91": "Clocks & Watches", 
    "92": "Musical Instruments", 
    "93": "Arms & Ammo",
    "94": "Furniture", 
    "95": "Toys & Games", 
    "96": "Misc Manufactures",
    "97": "Art & Antiques",
}

def get_chapter(hscode):
    s = str(hscode).strip().zfill(8)
    return s[:2]

def get_chapter_name(hscode):
    ch = get_chapter(hscode)
    return HS_CHAPTERS.get(ch, f"Chapter {ch}")

# ── Load all CSVs ──────────────────────────────────────────────────────────────
def load_all_csvs():
    frames = []
    pattern = re.compile(r'^(im4|im7)_(\d{4})_(\d{2})\.csv$', re.IGNORECASE)

    for f in sorted(RAW_DIR.glob("*.csv")):
        m = pattern.match(f.name)
        if not m:
            print(f"  [SKIP] {f.name} — doesn't match im4/im7_YYYY_MM.csv pattern")
            continue
        tax_type = m.group(1).upper()
        year     = int(m.group(2))
        month    = int(m.group(3))

        df = pd.read_csv(f, dtype={"hscode": str})
        df.columns = [c.strip().lower() for c in df.columns]
        df["tax_type"] = tax_type
        df["year"]     = year
        df["month"]    = month
        df["period"]   = f"{year}-{month:02d}"
        df["chapter"]  = df["hscode"].apply(get_chapter)
        df["chapter_name"] = df["hscode"].apply(get_chapter_name)

        # Clean numeric columns
        for col in ["net_wt_kg", "assess_value_bdt", "invoice_value_bdt"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        frames.append(df)
        print(f"  [OK] {f.name} — {len(df)} rows")

    if not frames:
        raise FileNotFoundError(f"No valid CSV files found in {RAW_DIR}")

    return pd.concat(frames, ignore_index=True)

# ── Helpers ────────────────────────────────────────────────────────────────────
def top_n(df, group_col, value_col, n=20, label_col=None):
    grp = df.groupby(group_col)[value_col].sum().reset_index()
    grp = grp.sort_values(value_col, ascending=False).head(n)
    if label_col:
        labels = df.drop_duplicates(group_col)[[group_col, label_col]]
        grp = grp.merge(labels, on=group_col, how="left")
    return grp.to_dict(orient="records")

def mom_growth(df, value_col="assess_value_bdt"):
    """Month-over-month growth % per period."""
    ts = df.groupby("period")[value_col].sum().reset_index().sort_values("period")
    ts["mom_pct"] = ts[value_col].pct_change() * 100
    return ts.to_dict(orient="records")

def serialize(obj):
    """JSON serializer for numpy/pandas types."""
    import numpy as np
    if isinstance(obj, (np.integer,)):  return int(obj)
    if isinstance(obj, (np.floating,)): return float(obj) if not (obj != obj) else None
    if isinstance(obj, (np.ndarray,)):  return obj.tolist()
    raise TypeError(f"Not serializable: {type(obj)}")

# ── Main analytics builder ─────────────────────────────────────────────────────
def build_dashboard_data(df):
    data = {}
    periods = sorted(df["period"].unique().tolist())
    latest  = periods[-1]
    prev    = periods[-2] if len(periods) > 1 else None

    # ── 1. KPI summary ───────────────────────────────────────────────────────
    def kpi_for(subset):
        return {
            "total_assess_value": float(subset["assess_value_bdt"].sum()),
            "total_invoice_value": float(subset["invoice_value_bdt"].sum()),
            "total_net_wt_kg":    float(subset["net_wt_kg"].sum()),
            "unique_hscodes":     int(subset["hscode"].nunique()),
            "unique_chapters":    int(subset["chapter"].nunique()),
        }

    latest_data = df[df["period"] == latest]
    data["kpi"] = {
        "overall":      kpi_for(df),
        "latest_month": kpi_for(latest_data),
        "latest_period": latest,
        "all_periods":   periods,
    }

    if prev:
        prev_data = df[df["period"] == prev]
        cur_val   = latest_data["assess_value_bdt"].sum()
        prv_val   = prev_data["assess_value_bdt"].sum()
        data["kpi"]["mom_growth_pct"] = round(((cur_val - prv_val) / prv_val * 100) if prv_val else 0, 2)

    # ── 2. Monthly trend (all combined) ──────────────────────────────────────
    monthly = df.groupby("period").agg(
        assess_value=("assess_value_bdt", "sum"),
        invoice_value=("invoice_value_bdt", "sum"),
        net_wt_kg=("net_wt_kg", "sum"),
        unique_hscodes=("hscode", "nunique"),
    ).reset_index().sort_values("period")
    monthly["mom_pct"] = monthly["assess_value"].pct_change() * 100
    data["monthly_trend"] = monthly.to_dict(orient="records")

    # ── 3. IM4 vs IM7 monthly breakdown ──────────────────────────────────────
    by_type = df.groupby(["period", "tax_type"]).agg(
        assess_value=("assess_value_bdt", "sum"),
        net_wt_kg=("net_wt_kg", "sum"),
    ).reset_index().sort_values(["period", "tax_type"])
    data["by_tax_type"] = by_type.to_dict(orient="records")

    # ── 4. Top HS codes ───────────────────────────────────────────────────────
    hs_agg = df.groupby(["hscode", "description"]).agg(
        assess_value=("assess_value_bdt", "sum"),
        invoice_value=("invoice_value_bdt", "sum"),
        net_wt_kg=("net_wt_kg", "sum"),
        months_active=("period", "nunique"),
    ).reset_index()

    # Monthly data per hs code (for sparklines)
    hs_monthly = df.groupby(["hscode", "period"])["assess_value_bdt"].sum().reset_index()
    hs_monthly_dict = defaultdict(dict)
    for _, row in hs_monthly.iterrows():
        hs_monthly_dict[row["hscode"]][row["period"]] = float(row["assess_value_bdt"])

    top_hs = hs_agg.sort_values("assess_value", ascending=False).head(25)
    top_hs_list = top_hs.to_dict(orient="records")
    for item in top_hs_list:
        item["monthly_trend"] = [hs_monthly_dict[item["hscode"]].get(p, 0) for p in periods]

    data["top_hscodes_by_value"]  = top_hs_list
    data["top_hscodes_by_weight"] = hs_agg.sort_values("net_wt_kg", ascending=False).head(25).to_dict(orient="records")

    # MoM growth (latest vs prev)
    if prev:
        latest_hs = df[df["period"] == latest].groupby("hscode")["assess_value_bdt"].sum()
        prev_hs   = df[df["period"] == prev  ].groupby("hscode")["assess_value_bdt"].sum()
        growth_df = pd.DataFrame({"cur": latest_hs, "prv": prev_hs}).dropna()
        growth_df = growth_df[growth_df["prv"] > 0]
        growth_df["growth_pct"] = (growth_df["cur"] - growth_df["prv"]) / growth_df["prv"] * 100
        top_growing = growth_df.sort_values("growth_pct", ascending=False).head(15).reset_index()
        descs = df.drop_duplicates("hscode").set_index("hscode")["description"]
        top_growing["description"] = top_growing["hscode"].map(descs)
        data["fastest_growing"] = top_growing.to_dict(orient="records")

    # ── 5. Chapter aggregation ────────────────────────────────────────────────
    chapter_agg = df.groupby(["chapter", "chapter_name"]).agg(
        assess_value=("assess_value_bdt", "sum"),
        net_wt_kg=("net_wt_kg", "sum"),
        unique_hscodes=("hscode", "nunique"),
    ).reset_index().sort_values("assess_value", ascending=False)
    data["by_chapter"] = chapter_agg.head(20).to_dict(orient="records")

    # Monthly chapter trend (top 5 chapters)
    top5_chapters = chapter_agg.head(5)["chapter"].tolist()
    ch_trend = df[df["chapter"].isin(top5_chapters)].groupby(["period", "chapter", "chapter_name"]).agg(
        assess_value=("assess_value_bdt", "sum"),
    ).reset_index()
    data["chapter_trend"] = ch_trend.to_dict(orient="records")

    # ── 6. Searchable HS table (all HS codes, all periods) ────────────────────
    all_hs = df.groupby(["hscode", "description", "chapter", "chapter_name"]).agg(
        assess_value=("assess_value_bdt", "sum"),
        invoice_value=("invoice_value_bdt", "sum"),
        net_wt_kg=("net_wt_kg", "sum"),
        months_active=("period", "nunique"),
    ).reset_index().sort_values("assess_value", ascending=False)

    # Add monthly breakdown for each HS code (for detail cards)
    all_hs_list = all_hs.to_dict(orient="records")
    for item in all_hs_list:
        item["monthly"] = []
        for p in periods:
            subset = df[(df["hscode"] == item["hscode"]) & (df["period"] == p)]
            if not subset.empty:
                row = subset.iloc[0]
                item["monthly"].append({
                    "period": p,
                    "assess_value": float(subset["assess_value_bdt"].sum()),
                    "invoice_value": float(subset["invoice_value_bdt"].sum()),
                    "net_wt_kg": float(subset["net_wt_kg"].sum()),
                    "tax_types": subset["tax_type"].unique().tolist(),
                })

    data["all_hscodes"] = all_hs_list

    # ── 7. Meta ───────────────────────────────────────────────────────────────
    data["meta"] = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "total_rows": len(df),
        "periods": periods,
        "tax_types": sorted(df["tax_type"].unique().tolist()),
    }

    return data

# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Bangladesh Customs Dashboard — Data Generator")
    print("=" * 50)
    print(f"Reading CSVs from: {RAW_DIR}")

    df = load_all_csvs()
    print(f"\nTotal rows loaded: {len(df)}")
    print(f"Periods found:     {sorted(df['period'].unique().tolist())}")
    print(f"Tax types:         {sorted(df['tax_type'].unique().tolist())}")

    print("\nBuilding analytics...")
    dashboard_data = build_dashboard_data(df)

    out_path = OUT_DIR / "dashboard_data.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, ensure_ascii=False, default=serialize, indent=2)

    size_kb = out_path.stat().st_size / 1024
    print(f"\n✓ Data written to: {out_path} ({size_kb:.1f} KB)")
    print(f"  Periods:         {len(dashboard_data['meta']['periods'])}")
    print(f"  Unique HS codes: {len(dashboard_data['all_hscodes'])}")
    print(f"  Generated at:    {dashboard_data['meta']['generated_at']}")
    print("\nDone! Open index.html in your browser.")
