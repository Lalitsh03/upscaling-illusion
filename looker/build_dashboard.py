"""
Generates looker/dashboard.html — interactive Plotly dashboard for The Upscaling Illusion.
Run with: python build_dashboard.py   (from the looker/ directory)

Light theme  |  Brand colours: Nvidia #76b900 · AMD #ED1C24 · Intel #0071c5
"""

import sqlite3, json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT   = Path(__file__).parent.parent
DB     = ROOT / "data" / "gpu_analysis.db"
OUT    = Path(__file__).parent / "dashboard.html"

# ── Brand colours ─────────────────────────────────────────────────────────────
NVIDIA  = "#76b900"
AMD     = "#ED1C24"
INTEL   = "#0071c5"
AMBER   = "#f5a623"   # upscaling-only line
CHARCOAL= "#444444"   # native raster line
GREY    = "#999999"

VENDOR_COLOR = {"Nvidia": NVIDIA, "AMD": AMD, "Intel": INTEL}

# ── Light layout defaults ─────────────────────────────────────────────────────
BG      = "#f8f9fa"   # figure background
PANEL   = "#ffffff"   # plot area
GRID    = "#e5e5e5"
BORDER  = "#cccccc"
TEXT    = "#1a1a1a"
SUBTEXT = "#666666"

BASE_LAYOUT = dict(
    paper_bgcolor = BG,
    plot_bgcolor  = PANEL,
    font          = dict(family="Segoe UI, system-ui, sans-serif", color=TEXT, size=12),
    margin        = dict(l=50, r=20, t=60, b=50),
)
LEGEND_DEFAULT = dict(bgcolor="#ffffff", bordercolor=BORDER, borderwidth=1, font=dict(size=11, color=TEXT))

def apply_base(fig, rows=1, cols=1):
    """Apply light-theme layout to a figure."""
    fig.update_layout(**BASE_LAYOUT)
    for i in range(1, rows * cols + 1):
        fig.update_xaxes(gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=SUBTEXT), row=(i-1)//cols+1 if rows>1 else None, col=(i-1)%cols+1 if cols>1 else None)
        fig.update_yaxes(gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=SUBTEXT), row=(i-1)//cols+1 if rows>1 else None, col=(i-1)%cols+1 if cols>1 else None)
    return fig

# ── Load data ─────────────────────────────────────────────────────────────────
conn    = sqlite3.connect(DB)
gpus    = pd.read_sql("SELECT * FROM gpu_analysis",           conn)
gen_agg = pd.read_sql("SELECT * FROM gpu_generation_summary", conn)
cpus    = pd.read_sql("SELECT * FROM cpu_benchmarks",         conn)
mshare  = pd.read_sql("SELECT * FROM gpu_market_share",       conn)
cpu_sh  = pd.read_sql("SELECT * FROM amd_cpu_market_share",   conn)
conn.close()

mshare  = mshare.rename(columns={"amd_pct":"amd_gpu_share","nvidia_pct":"nvidia_gpu_share","intel_pct":"intel_gpu_share"})
cpu_sh  = cpu_sh.rename(columns={"amd_cpu_pct":"amd_cpu_share","intel_cpu_pct":"intel_cpu_share"})
mshare  = mshare.groupby("year")[["amd_gpu_share","nvidia_gpu_share","intel_gpu_share"]].mean().reset_index()
cpu_sh  = cpu_sh.groupby("year")[["amd_cpu_share","intel_cpu_share"]].mean().reset_index()

gen_agg["fg_ratio"] = (gen_agg["avg_ppd_with_fg"] / gen_agg["avg_ppd_native"]).round(2)

# ── Chart 1: Divergence ───────────────────────────────────────────────────────
# No subplot_titles here — we place vendor labels as annotations INSIDE each panel
fig1 = make_subplots(
    rows=1, cols=3,
    shared_yaxes=False,
    horizontal_spacing=0.08,
)

for col_idx, vendor in enumerate(["Nvidia", "AMD", "Intel"], start=1):
    df        = gen_agg[gen_agg["vendor"] == vendor].sort_values("gen_launch_year")
    brand_col = VENDOR_COLOR[vendor]
    show_leg  = (col_idx == 1)

    fig1.add_trace(go.Scatter(
        x=df["generation"], y=df["avg_ppd_native"],
        mode="lines+markers",
        name="Raw (native)",
        line=dict(color=CHARCOAL, width=2.5),
        marker=dict(size=8, symbol="circle"),
        legendgroup="native", showlegend=show_leg,
        hovertemplate="<b>%{x}</b><br>Native PPD: %{y:.3f}<extra></extra>",
    ), row=1, col=col_idx)

    fig1.add_trace(go.Scatter(
        x=df["generation"], y=df["avg_ppd_no_fg"],
        mode="lines+markers",
        name="Upscaling only",
        line=dict(color=AMBER, width=2.5),
        marker=dict(size=8, symbol="square"),
        legendgroup="no_fg", showlegend=show_leg,
        hovertemplate="<b>%{x}</b><br>Upscaling PPD: %{y:.3f}<extra></extra>",
    ), row=1, col=col_idx)

    fig1.add_trace(go.Scatter(
        x=df["generation"], y=df["avg_ppd_with_fg"],
        mode="lines+markers",
        name=f"+ Frame Gen ({vendor})",
        line=dict(color=brand_col, width=3),
        marker=dict(size=10, symbol="triangle-up"),
        legendgroup=f"fg_{vendor}", showlegend=True,
        hovertemplate=f"<b>%{{x}}</b><br>FG PPD: %{{y:.3f}}<extra></extra>",
    ), row=1, col=col_idx)

    # FG ratio annotation on final gen
    last = df.iloc[-1]
    fig1.add_annotation(
        x=last["generation"], y=last["avg_ppd_with_fg"],
        text=f"<b>FG {last['fg_ratio']}×</b>",
        showarrow=True, arrowhead=2, arrowcolor=brand_col, arrowwidth=1.5,
        ax=0, ay=-35,
        font=dict(color=brand_col, size=11),
        row=1, col=col_idx,
    )

    # Vendor label INSIDE the panel — top-left corner using paper coords
    # xref/yref use paper coordinates: col1 ≈ 0.10, col2 ≈ 0.44, col3 ≈ 0.78
    x_paper = [0.10, 0.44, 0.78][col_idx - 1]
    fig1.add_annotation(
        x=x_paper, y=0.97,
        xref="paper", yref="paper",
        text=f"<b>{vendor}</b>",
        showarrow=False,
        font=dict(color=brand_col, size=14),
        xanchor="center", yanchor="top",
    )

fig1.update_layout(
    **BASE_LAYOUT,
    title=dict(
        text="<b>The Divergence: Raw vs Effective Performance Per Dollar</b><br>"
             "<span style='font-size:12px;color:#666'>Frame Generation (RTX 4000+ / RX 7000+) drives most of the gap</span>",
        font=dict(size=16, color=TEXT), x=0.05,
    ),
    height=420,
    legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5,
                bgcolor="#ffffff", bordercolor=BORDER, borderwidth=1, font=dict(size=11, color=TEXT),
                traceorder="normal"),
)
fig1.update_xaxes(tickfont=dict(size=9, color=SUBTEXT), tickangle=-30, gridcolor=GRID, linecolor=BORDER)
fig1.update_yaxes(title_text="Perf / Dollar", title_font=dict(size=10, color=SUBTEXT),
                  gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=SUBTEXT), row=1, col=1)

# ── Chart 2: Flagship Price Trend ─────────────────────────────────────────────
flagship = gpus[gpus["tier"] == "flagship"].copy().sort_values("launch_year")
gen_avg  = (flagship.groupby(["vendor","generation","launch_year"])
            ["launch_price_2024_adj"].mean().reset_index())

fig2 = go.Figure()

for vendor in ["Nvidia", "AMD", "Intel"]:
    color   = VENDOR_COLOR[vendor]
    sub_raw = flagship[flagship["vendor"] == vendor]
    sub_avg = gen_avg[gen_avg["vendor"] == vendor].sort_values("launch_year")

    # Individual GPU dots
    fig2.add_trace(go.Scatter(
        x=sub_raw["launch_year"], y=sub_raw["launch_price_2024_adj"],
        mode="markers",
        name=f"{vendor} GPUs",
        marker=dict(color=color, size=7, opacity=0.40),
        legendgroup=vendor, showlegend=False,
        hovertemplate="<b>%{text}</b><br>$%{y:,.0f}<extra></extra>",
        text=sub_raw["gpu_name"],
    ))

    # Generation average line
    fig2.add_trace(go.Scatter(
        x=sub_avg["launch_year"], y=sub_avg["launch_price_2024_adj"],
        mode="lines+markers",
        name=vendor,
        line=dict(color=color, width=2.5),
        marker=dict(size=9, symbol="diamond"),
        legendgroup=vendor, showlegend=True,
        hovertemplate=f"<b>{vendor}</b><br>%{{x}}<br>Avg: $%{{y:,.0f}}<extra></extra>",
    ))

# $999 reference line
fig2.add_hline(y=999, line_dash="dash", line_color=GREY, line_width=1.2, opacity=0.7,
               annotation_text="$999 reference", annotation_position="top right",
               annotation_font=dict(color=GREY, size=10))

fig2.update_layout(
    **BASE_LAYOUT,
    legend=LEGEND_DEFAULT,
    title=dict(text="<b>Flagship GPU Launch Prices — 2024-Adjusted USD</b>",
               font=dict(size=14, color=TEXT), x=0.05),
    xaxis=dict(title="Launch Year", gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=SUBTEXT)),
    yaxis=dict(title="Price (2024 USD)", tickprefix="$", tickformat=",",
               gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=SUBTEXT)),
    height=400,
)

# ── Chart 3: CPU vs GPU Growth ────────────────────────────────────────────────
cpu_flag = cpus[cpus["tier"] == "flagship"].copy()
gpu_flag = gpus[gpus["tier"] == "flagship"].copy()
gpu_yr   = gpu_flag.groupby(["vendor","launch_year"])["perf_score_native_1440p"].mean().reset_index()

def reindex(df, yr_col, val_col, base=2019):
    df = df.sort_values(yr_col).copy()
    rows = df[df[yr_col] == base]
    bval = rows.iloc[0][val_col] if not rows.empty else df.iloc[0][val_col]
    df["idx"] = (df[val_col] / bval * 100).round(1)
    return df

nv_gpu = reindex(gpu_yr[gpu_yr["vendor"]=="Nvidia"], "launch_year", "perf_score_native_1440p")
am_gpu = reindex(gpu_yr[gpu_yr["vendor"]=="AMD"],    "launch_year", "perf_score_native_1440p")
in_cpu = reindex(cpu_flag[cpu_flag["vendor"]=="Intel"].sort_values("launch_year"), "launch_year", "perf_score_st")
am_cpu = reindex(cpu_flag[cpu_flag["vendor"]=="AMD"].sort_values("launch_year"),   "launch_year", "perf_score_st")

fig3 = go.Figure()

# GPU lines — solid, full brand colour
for df, vendor, color in [(nv_gpu,"Nvidia",NVIDIA), (am_gpu,"AMD",AMD)]:
    fig3.add_trace(go.Scatter(
        x=df["launch_year"], y=df["idx"],
        mode="lines+markers", name=f"GPU: {vendor} (raster)",
        line=dict(color=color, width=2.8),
        marker=dict(size=9, symbol="circle"),
        hovertemplate=f"<b>GPU {vendor}</b><br>%{{x}}: %{{y:.1f}}<extra></extra>",
    ))

# CPU lines — dashed, slightly muted
for df, vendor, color in [(in_cpu,"Intel",INTEL), (am_cpu,"AMD","#c0392b")]:
    fig3.add_trace(go.Scatter(
        x=df["launch_year"], y=df["idx"],
        mode="lines+markers", name=f"CPU: {vendor} (single-thread)",
        line=dict(color=color, width=1.8, dash="dash"),
        marker=dict(size=7, symbol="diamond"),
        opacity=0.80,
        hovertemplate=f"<b>CPU {vendor}</b><br>%{{x}}: %{{y:.1f}}<extra></extra>",
    ))

fig3.add_hline(y=100, line_dash="dot", line_color=GREY, line_width=1, opacity=0.6)
fig3.add_vline(x=2022, line_dash="dot", line_color=GREY, line_width=1, opacity=0.5,
               annotation_text="Frame Gen era →", annotation_position="top right",
               annotation_font=dict(color=GREY, size=10))

fig3.update_layout(
    **BASE_LAYOUT,
    legend=LEGEND_DEFAULT,
    title=dict(
        text="<b>CPU vs GPU Performance Growth — Flagship Tier</b><br>"
             "<span style='font-size:11px;color:#666'>Solid = GPU (raster) · Dashed = CPU (single-thread) · Each re-indexed to own 2019 = 100</span>",
        font=dict(size=14, color=TEXT), x=0.05,
    ),
    xaxis=dict(title="Year", gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=SUBTEXT)),
    yaxis=dict(title="Index (2019 = 100)", gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=SUBTEXT)),
    height=400,
)

# ── Chart 4: AMD Brand Halo ───────────────────────────────────────────────────
halo = mshare[["year","amd_gpu_share"]].merge(
    cpu_sh[["year","amd_cpu_share"]], on="year", how="inner"
).sort_values("year")

fig4 = go.Figure()

# Shaded gap
fig4.add_trace(go.Scatter(
    x=list(halo["year"]) + list(halo["year"])[::-1],
    y=list(halo["amd_gpu_share"]) + list(halo["amd_cpu_share"])[::-1],
    fill="toself", fillcolor=f"rgba(237,28,36,0.07)",
    line=dict(color="rgba(0,0,0,0)"),
    showlegend=False, hoverinfo="skip",
))

fig4.add_trace(go.Scatter(
    x=halo["year"], y=halo["amd_gpu_share"],
    mode="lines+markers", name="AMD GPU share %",
    line=dict(color=AMD, width=2.8),
    marker=dict(size=9, symbol="circle"),
    hovertemplate="<b>AMD GPU</b><br>%{x}: %{y:.1f}%<extra></extra>",
))

fig4.add_trace(go.Scatter(
    x=halo["year"], y=halo["amd_cpu_share"],
    mode="lines+markers", name="AMD CPU share %",
    line=dict(color="#e67e22", width=2.2, dash="dash"),
    marker=dict(size=8, symbol="diamond"),
    hovertemplate="<b>AMD CPU</b><br>%{x}: %{y:.1f}%<extra></extra>",
))

# Annotate the 2021 contradiction
peak_cpu = halo.loc[halo["amd_cpu_share"].idxmax()]
gpu_at_peak = halo.loc[halo["year"] == peak_cpu["year"], "amd_gpu_share"].values[0]
fig4.add_annotation(
    x=peak_cpu["year"], y=gpu_at_peak,
    text=f"AMD CPU peaked ~{peak_cpu['amd_cpu_share']:.0f}%<br>but GPU share hit lowest ({gpu_at_peak:.1f}%)<br>— brand halo did not appear",
    showarrow=True, arrowhead=2, arrowcolor="#888888", arrowwidth=1.5,
    ax=-120, ay=-50,
    font=dict(size=10, color="#444444"),
    bgcolor="#ffffff", bordercolor=BORDER, borderpad=5,
)

fig4.update_layout(
    **BASE_LAYOUT,
    legend=LEGEND_DEFAULT,
    title=dict(text="<b>AMD Brand Halo — Did Ryzen Pull GPU Share Up?</b>",
               font=dict(size=14, color=TEXT), x=0.05),
    xaxis=dict(title="Year", gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=SUBTEXT)),
    yaxis=dict(title="Market Share %", ticksuffix="%", range=[0, 70],
               gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=SUBTEXT)),
    height=400,
)

# ── Chart 5: Price Bracket Showdown ──────────────────────────────────────────
import numpy as np

cuts   = [0, 450, 700, 1100, 1500, float("inf")]
blabels = ["Budget<br>(<$450)", "Mid<br>($450–700)", "High<br>($700–1100)",
           "Premium<br>($1100–1500)", "Extreme<br>($1500+)"]

gpus["price_bracket"] = pd.cut(
    gpus["launch_price_2024_adj"], bins=cuts,
    labels=blabels, right=False
)

bracket_agg = (
    gpus.groupby(["price_bracket","vendor"], observed=True)
    [["perf_per_dollar_native","perf_per_dollar_effective_with_fg"]]
    .mean().reset_index()
)
bracket_counts = (
    gpus.groupby(["price_bracket","vendor"], observed=True)
    .size().reset_index(name="n_gpus")
)
bracket_agg = bracket_agg.merge(bracket_counts, on=["price_bracket","vendor"])

fig5 = make_subplots(
    rows=1, cols=2,
    subplot_titles=[
        "<b>Native rasterisation only — no AI</b>",
        "<b>Effective PPD with upscaling + frame gen</b>",
    ],
    horizontal_spacing=0.10,
)

for col_idx, ppd_col in enumerate(
    ["perf_per_dollar_native", "perf_per_dollar_effective_with_fg"], start=1
):
    for vi, vendor in enumerate(["Nvidia", "AMD", "Intel"]):
        sub = bracket_agg[bracket_agg["vendor"] == vendor]
        heights, texts, customdata = [], [], []
        for lbl in blabels:
            row = sub[sub["price_bracket"] == lbl]
            if len(row):
                h = row[ppd_col].values[0]
                n = row["n_gpus"].values[0]
            else:
                h = None
                n = 0
            heights.append(h)
            texts.append(f"n={n}" if n else "")
            customdata.append(n)

        fig5.add_trace(go.Bar(
            x=blabels, y=heights,
            name=vendor,
            marker_color=VENDOR_COLOR[vendor],
            opacity=0.88,
            text=texts,
            textposition="outside",
            textfont=dict(size=9, color="#666666"),
            legendgroup=vendor,
            showlegend=(col_idx == 1),
            hovertemplate=f"<b>{vendor}</b><br>%{{x}}<br>PPD: %{{y:.3f}}<extra></extra>",
        ), row=1, col=col_idx)

    # "Nvidia only" note on extreme bracket
    fig5.add_annotation(
        x="Extreme<br>($1500+)", y=0.005,
        text="Nvidia only",
        showarrow=False,
        font=dict(size=9, color="#999999", style="italic"),
        xref=f"x{col_idx}", yref=f"y{col_idx}",
    )

for i in range(1, 3):
    fig5.update_xaxes(gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=SUBTEXT, size=10), row=1, col=i)
    fig5.update_yaxes(title_text="Avg Performance Per Dollar" if i==1 else "",
                      gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=SUBTEXT), row=1, col=i)

# Colour subplot titles
for ann in fig5.layout.annotations:
    ann.font = dict(size=12, color="#333333")

fig5_layout = {**BASE_LAYOUT, "margin": dict(l=50, r=20, t=90, b=50)}
fig5.update_layout(
    **fig5_layout,
    legend=dict(orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5,
                bgcolor="#ffffff", bordercolor=BORDER, borderwidth=1,
                font=dict(size=11, color=TEXT)),
    title=dict(
        text="<b>Same-Price Showdown: What Does Each Brand Give You at the Same Budget?</b><br>"
             "<span style='font-size:11px;color:#666'>Flagship-vs-flagship comparisons are incomplete — AMD's most expensive GPU costs half of Nvidia's most expensive</span>",
        font=dict(size=14, color=TEXT), x=0.05,
    ),
    barmode="group",
    height=440,
)

# ── Render to HTML ────────────────────────────────────────────────────────────
def fig_to_div(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})

d1 = fig_to_div(fig1)
d2 = fig_to_div(fig2)
d3 = fig_to_div(fig3)
d4 = fig_to_div(fig4)
d5 = fig_to_div(fig5)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Upscaling Illusion — GPU Value Analysis 2018–2025</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #f8f9fa;
    color: #1a1a1a;
    font-family: 'Segoe UI', system-ui, sans-serif;
    padding: 28px;
  }}
  .header {{
    margin-bottom: 28px;
    border-left: 4px solid #76b900;
    padding-left: 14px;
  }}
  .header h1 {{
    font-size: 22px;
    font-weight: 700;
    color: #1a1a1a;
    margin-bottom: 6px;
  }}
  .header p {{
    font-size: 13px;
    color: #666666;
  }}
  .brand-dot {{
    display: inline-block;
    width: 10px; height: 10px;
    border-radius: 50%;
    margin-right: 4px;
    vertical-align: middle;
  }}
  .legend-row {{
    display: flex;
    gap: 18px;
    font-size: 12px;
    color: #555;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }}
  .grid {{ display: grid; gap: 16px; }}
  .row-full  {{ grid-template-columns: 1fr; }}
  .row-split {{ grid-template-columns: 1fr 1fr; }}
  .card {{
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 14px;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }}
  .card > div {{ width: 100%; }}
  @media (max-width: 900px) {{
    .row-split {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

<div class="header">
  <h1>The Upscaling Illusion: GPU Value Analysis 2018–2025</h1>
  <p>Did AI upscaling genuinely improve value — or did it mask stagnant hardware progress?</p>
</div>

<div class="legend-row">
  <span><span class="brand-dot" style="background:#76b900"></span><strong>Nvidia</strong></span>
  <span><span class="brand-dot" style="background:#ED1C24"></span><strong>AMD</strong></span>
  <span><span class="brand-dot" style="background:#0071c5"></span><strong>Intel</strong></span>
  <span style="color:#aaa">|</span>
  <span><span class="brand-dot" style="background:#444444;border-radius:2px"></span>Raw rasterisation</span>
  <span><span class="brand-dot" style="background:#f5a623;border-radius:2px"></span>Upscaling only</span>
  <span><span class="brand-dot" style="background:#999;border-radius:2px;border:1px dashed #999"></span>CPU lines (dashed)</span>
</div>

<div class="grid row-full" style="margin-bottom:16px">
  <div class="card">{d1}</div>
</div>
<div class="grid row-full" style="margin-bottom:16px">
  <div class="card">{d5}</div>
</div>
<div class="grid row-split" style="margin-bottom:16px">
  <div class="card">{d2}</div>
  <div class="card">{d3}</div>
</div>
<div class="grid row-full">
  <div class="card">{d4}</div>
</div>

</body>
</html>"""

OUT.write_text(html, encoding="utf-8")
print(f"Written: {OUT}  ({OUT.stat().st_size // 1024} KB)")
