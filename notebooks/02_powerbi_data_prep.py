"""
Power BI Data Prep
Generates pre-shaped CSVs for each of the 5 dashboard visuals.
Run from the project root: python notebooks/02_powerbi_data_prep.py
"""

import sqlite3
import pandas as pd
from pathlib import Path

DB   = Path('data/gpu_analysis.db')
OUT  = Path('data/powerbi')
OUT.mkdir(exist_ok=True)

conn = sqlite3.connect(DB)

# ─────────────────────────────────────────────────────────────────
# VISUAL 1: The Divergence
# Unpivoted generation summary so Power BI line chart gets
# one row per (vendor, generation, metric) instead of wide columns.
# ─────────────────────────────────────────────────────────────────
gen = pd.read_sql("""
    SELECT vendor, generation, MIN(launch_year) AS gen_launch_year,
           ROUND(AVG(perf_per_dollar_native),4)                AS Raw_Rasterization,
           ROUND(AVG(perf_per_dollar_effective_no_fg),4)       AS Upscaling_No_FrameGen,
           ROUND(AVG(perf_per_dollar_effective_with_fg),4)     AS Upscaling_With_FrameGen
    FROM gpu_analysis
    GROUP BY vendor, generation
    ORDER BY vendor, gen_launch_year
""", conn)

div = gen.melt(
    id_vars=['vendor','generation','gen_launch_year'],
    value_vars=['Raw_Rasterization','Upscaling_No_FrameGen','Upscaling_With_FrameGen'],
    var_name='metric', value_name='perf_per_dollar'
)
# Friendly display names for Power BI legend
div['metric_label'] = div['metric'].map({
    'Raw_Rasterization':      'Raw rasterization (native)',
    'Upscaling_No_FrameGen':  'Upscaling — no Frame Gen',
    'Upscaling_With_FrameGen':'Upscaling + Frame Gen',
})
# Sort order for legend
div['metric_order'] = div['metric'].map({
    'Raw_Rasterization': 1,
    'Upscaling_No_FrameGen': 2,
    'Upscaling_With_FrameGen': 3,
})
div.to_csv(OUT / 'v1_divergence.csv', index=False)
print(f"v1_divergence.csv: {len(div)} rows")


# ─────────────────────────────────────────────────────────────────
# VISUAL 2: Flagship Price Trend (nominal vs real)
# One row per GPU in flagship tier, plus generation average line
# ─────────────────────────────────────────────────────────────────
price = pd.read_sql("""
    SELECT vendor, generation, gpu_name, launch_year,
           launch_price_usd        AS nominal_price,
           launch_price_2024_adj   AS real_price_2024
    FROM gpu_analysis
    WHERE tier = 'flagship'
    ORDER BY vendor, launch_year
""", conn)

# Add gen average for the trend line
gen_avg = price.groupby(['vendor','generation','launch_year'])[['nominal_price','real_price_2024']].mean().reset_index()
gen_avg['gpu_name'] = 'GEN_AVG'
price_full = pd.concat([price, gen_avg], ignore_index=True).sort_values(['vendor','launch_year'])
price_full.to_csv(OUT / 'v2_price_trend.csv', index=False)
print(f"v2_price_trend.csv: {len(price_full)} rows")


# ─────────────────────────────────────────────────────────────────
# VISUAL 3: Frame Gen Contribution Breakdown
# Stacked bar: raw gain → upscaling gain → frame gen gain
# Shows what share of total effective PPD each layer contributed
# ─────────────────────────────────────────────────────────────────
fg = pd.read_sql("""
    SELECT vendor, generation, MIN(launch_year) AS gen_launch_year,
           ROUND(AVG(perf_per_dollar_native), 4)                   AS ppd_base,
           ROUND(AVG(perf_per_dollar_effective_no_fg)
               - AVG(perf_per_dollar_native), 4)                   AS ppd_gain_upscaling,
           ROUND(AVG(perf_per_dollar_effective_with_fg)
               - AVG(perf_per_dollar_effective_no_fg), 4)          AS ppd_gain_framegen,
           ROUND(AVG(perf_per_dollar_effective_with_fg), 4)        AS ppd_total
    FROM gpu_analysis
    GROUP BY vendor, generation
    ORDER BY vendor, gen_launch_year
""", conn)

# Melt into stacked bar format
fg_melt = fg.melt(
    id_vars=['vendor','generation','gen_launch_year','ppd_total'],
    value_vars=['ppd_base','ppd_gain_upscaling','ppd_gain_framegen'],
    var_name='layer', value_name='ppd_value'
)
fg_melt['layer_label'] = fg_melt['layer'].map({
    'ppd_base':           '1 Raw performance',
    'ppd_gain_upscaling': '2 Upscaling quality gain',
    'ppd_gain_framegen':  '3 Frame Gen gain (artificial frames)',
})
fg_melt['stack_order'] = fg_melt['layer'].map({
    'ppd_base': 1, 'ppd_gain_upscaling': 2, 'ppd_gain_framegen': 3
})
fg_melt.to_csv(OUT / 'v3_framegen_breakdown.csv', index=False)
print(f"v3_framegen_breakdown.csv: {len(fg_melt)} rows")


# ─────────────────────────────────────────────────────────────────
# VISUAL 4: CPU vs GPU Growth — re-indexed to 2019 = 100
# ─────────────────────────────────────────────────────────────────
gpu_yr = pd.read_sql("""
    SELECT vendor, launch_year,
           AVG(perf_score_native_1440p) AS perf
    FROM gpu_analysis
    WHERE tier = 'flagship'
    GROUP BY vendor, launch_year
""", conn)

cpu_yr = pd.read_sql("""
    SELECT vendor, launch_year,
           AVG(perf_score_st) AS perf
    FROM cpu_benchmarks
    WHERE tier = 'flagship'
    GROUP BY vendor, launch_year
""", conn)

def reindex(df, base_year=2019):
    result = []
    for vendor, grp in df.groupby('vendor'):
        grp = grp.sort_values('launch_year').copy()
        base_rows = grp[grp['launch_year'] == base_year]
        base_val  = base_rows['perf'].values[0] if len(base_rows) else grp.iloc[0]['perf']
        grp['indexed'] = (grp['perf'] / base_val * 100).round(1)
        result.append(grp)
    return pd.concat(result)

gpu_idx = reindex(gpu_yr)
gpu_idx['component'] = 'GPU'
gpu_idx['series_label'] = 'GPU: ' + gpu_idx['vendor'] + ' Flagship (1440p raster)'

cpu_idx = reindex(cpu_yr)
cpu_idx['component'] = 'CPU'
cpu_idx['series_label'] = 'CPU: ' + cpu_idx['vendor'] + ' Flagship (single-thread)'

trajectory = pd.concat([
    gpu_idx[['vendor','component','series_label','launch_year','indexed']],
    cpu_idx[['vendor','component','series_label','launch_year','indexed']],
], ignore_index=True).rename(columns={'launch_year':'year','indexed':'perf_index_2019_100'})

trajectory.to_csv(OUT / 'v4_cpu_gpu_trajectory.csv', index=False)
print(f"v4_cpu_gpu_trajectory.csv: {len(trajectory)} rows")


# ─────────────────────────────────────────────────────────────────
# VISUAL 5: AMD Brand Halo — CPU vs GPU share (annual averages)
# ─────────────────────────────────────────────────────────────────
halo = pd.read_sql("""
    WITH g AS (
        SELECT year,
               ROUND(AVG(amd_pct),2)    AS amd_gpu_share,
               ROUND(AVG(nvidia_pct),2) AS nvidia_gpu_share
        FROM gpu_market_share GROUP BY year
    ),
    c AS (
        SELECT year,
               ROUND(AVG(amd_cpu_pct),2)   AS amd_cpu_share,
               ROUND(AVG(intel_cpu_pct),2) AS intel_cpu_share
        FROM amd_cpu_market_share GROUP BY year
    )
    SELECT g.year,
           g.amd_gpu_share,
           c.amd_cpu_share,
           g.nvidia_gpu_share,
           c.intel_cpu_share,
           ROUND(g.amd_gpu_share - c.amd_cpu_share, 1) AS amd_gpu_minus_cpu_gap
    FROM g JOIN c ON g.year = c.year
    ORDER BY g.year
""", conn)

halo.to_csv(OUT / 'v5_brand_halo.csv', index=False)
print(f"v5_brand_halo.csv: {len(halo)} rows")

conn.close()
print("\nAll Power BI CSVs written to data/powerbi/")
