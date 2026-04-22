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

# ── Street price enrichment ───────────────────────────────────────────────────
import numpy as np
seed_raw = pd.read_csv(ROOT / "data" / "raw" / "gpu_specs_seed.csv")
gpus = gpus.merge(seed_raw[["gpu_name","street_price_usd"]], on="gpu_name", how="left")
gpus["street_price_2024_adj"] = (
    gpus["street_price_usd"] * (gpus["launch_price_2024_adj"] / gpus["launch_price_usd"])
).round(2)
gpus["ppd_street_native"] = (
    gpus["perf_score_native_1440p"] / gpus["street_price_2024_adj"]
).round(5)

# ── Chart 1: Divergence ───────────────────────────────────────────────────────
# No subplot_titles here — we place vendor labels as annotations INSIDE each panel
fig1 = make_subplots(
    rows=1, cols=3,
    shared_yaxes=False,
    horizontal_spacing=0.04,
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

fig1_layout = {**BASE_LAYOUT, "margin": dict(l=50, r=20, t=55, b=90)}
fig1.update_layout(
    **fig1_layout,
    title=dict(
        text="<b>The Divergence: Raw vs Effective Performance Per Dollar</b><br>"
             "<span style='font-size:11px;color:#666'>Frame Generation (RTX 4000+ / RX 7000+) drives most of the gap</span>",
        font=dict(size=14, color=TEXT), x=0.05,
    ),
    height=400,
    legend=dict(orientation="h", yanchor="bottom", y=-0.42, xanchor="center", x=0.5,
                bgcolor="#ffffff", bordercolor=BORDER, borderwidth=1, font=dict(size=10, color=TEXT),
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

fig2_layout = {**BASE_LAYOUT, "margin": dict(l=40, r=20, t=45, b=35)}
fig2.update_layout(
    **fig2_layout,
    legend=dict(bgcolor="#ffffff", bordercolor=BORDER, borderwidth=1, font=dict(size=9, color=TEXT)),
    title=dict(text="<b>Flagship GPU Launch Prices · 2024-Adjusted USD</b>",
               font=dict(size=13, color=TEXT), x=0.05),
    xaxis=dict(title="Launch Year", gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=SUBTEXT)),
    yaxis=dict(title="Price (2024 USD)", tickprefix="$", tickformat=",",
               gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=SUBTEXT)),
    height=250,
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
        text="<b>CPU vs GPU Performance Growth · Flagship Tier</b><br>"
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
        heights = []
        for lbl in blabels:
            row = sub[sub["price_bracket"] == lbl]
            h = row[ppd_col].values[0] if len(row) else None
            heights.append(h)

        fig5.add_trace(go.Bar(
            x=blabels, y=heights,
            name=vendor,
            marker_color=VENDOR_COLOR[vendor],
            opacity=0.88,
            legendgroup=vendor,
            showlegend=(col_idx == 1),
            hovertemplate=f"<b>{vendor}</b><br>%{{x}}<br>PPD: %{{y:.3f}}<extra></extra>",
        ), row=1, col=col_idx)

for i in range(1, 3):
    fig5.update_xaxes(gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=SUBTEXT, size=10), row=1, col=i)
    fig5.update_yaxes(title_text="Avg Performance Per Dollar" if i==1 else "",
                      gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=SUBTEXT), row=1, col=i)

# Colour subplot titles
for ann in fig5.layout.annotations:
    ann.font = dict(size=12, color="#333333")

fig5_layout = {**BASE_LAYOUT, "margin": dict(l=50, r=20, t=100, b=85)}
fig5.update_layout(
    **fig5_layout,
    legend=dict(orientation="h", yanchor="bottom", y=-0.45, xanchor="center", x=0.5,
                bgcolor="#ffffff", bordercolor=BORDER, borderwidth=1,
                font=dict(size=10, color=TEXT)),
    title=dict(
        text="<b>Same-Price Showdown: What Does Each Brand Give You at the Same Budget?</b><br>"
             "<span style='font-size:11px;color:#666'>AMD's most expensive GPU costs half of Nvidia's; flagship vs flagship misses the real comparison</span>",
        font=dict(size=14, color=TEXT), x=0.05,
    ),
    barmode="group",
    height=400,
)

# ── Chart 6: MSRP vs Street Price ────────────────────────────────────────────
gen_street = gpus.groupby(["vendor","generation"]).agg(
    gen_launch_year = ("launch_year", "min"),
    ppd_msrp        = ("perf_per_dollar_native", "mean"),
    ppd_street      = ("ppd_street_native", "mean"),
).reset_index().round(5)

fig6 = make_subplots(rows=1, cols=3, shared_yaxes=False, horizontal_spacing=0.08)

for col_idx, vendor in enumerate(["Nvidia", "AMD", "Intel"], start=1):
    brand_col = VENDOR_COLOR[vendor]
    sub = gen_street[gen_street["vendor"] == vendor].sort_values("gen_launch_year")
    show_leg = (col_idx == 1)

    fig6.add_trace(go.Scatter(
        x=sub["generation"], y=sub["ppd_msrp"],
        mode="lines+markers", name="MSRP price",
        line=dict(color=brand_col, width=2, dash="dash"),
        marker=dict(size=7, symbol="circle"),
        opacity=0.55,
        legendgroup="msrp", showlegend=show_leg,
        hovertemplate="<b>%{x}</b><br>MSRP PPD: %{y:.3f}<extra></extra>",
    ), row=1, col=col_idx)

    fig6.add_trace(go.Scatter(
        x=sub["generation"], y=sub["ppd_street"],
        mode="lines+markers", name="Street price (actual)",
        line=dict(color=brand_col, width=2.8),
        marker=dict(size=9, symbol="square"),
        legendgroup="street", showlegend=show_leg,
        hovertemplate="<b>%{x}</b><br>Street PPD: %{y:.3f}<extra></extra>",
    ), row=1, col=col_idx)

    # Vendor label inside panel
    x_paper = [0.10, 0.44, 0.78][col_idx - 1]
    fig6.add_annotation(
        x=x_paper, y=0.97, xref="paper", yref="paper",
        text=f"<b>{vendor}</b>", showarrow=False,
        font=dict(color=brand_col, size=14), xanchor="center", yanchor="top",
    )

fig6.update_xaxes(tickfont=dict(size=9, color=SUBTEXT), tickangle=-30, gridcolor=GRID, linecolor=BORDER)
fig6.update_yaxes(title_text="Native PPD", title_font=dict(size=10, color=SUBTEXT),
                  gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=SUBTEXT), row=1, col=1)
fig6_layout = {**BASE_LAYOUT, "margin": dict(l=40, r=20, t=45, b=75)}
fig6.update_layout(
    **fig6_layout,
    legend=dict(orientation="h", yanchor="bottom", y=-0.52, xanchor="center", x=0.5,
                bgcolor="#ffffff", bordercolor=BORDER, borderwidth=1, font=dict(size=9, color=TEXT)),
    title=dict(
        text="<b>MSRP vs What People Actually Paid: How the Value Story Changes</b><br>"
             "<span style='font-size:11px;color:#666'>Dashed = MSRP  ·  Solid = estimated average street price  ·  RTX 3000 gap is largest</span>",
        font=dict(size=13, color=TEXT), x=0.05,
    ),
    height=250,
)

# ── Chart 7: VRAM by Price Bracket ───────────────────────────────────────────
cuts_v  = [0, 450, 700, 1100, 1500, float("inf")]
blbls_v = ["Budget<br>(<$450)", "Mid<br>($450–700)", "High<br>($700–1100)",
           "Premium<br>($1100–1500)", "Extreme<br>($1500+)"]

gpus["price_bracket_v"] = pd.cut(gpus["launch_price_2024_adj"], bins=cuts_v,
                                  labels=blbls_v, right=False)

vram_bracket = (
    gpus.groupby(["price_bracket_v","vendor"], observed=True)["vram_gb"]
    .mean().reset_index()
)

fig7 = go.Figure()

for vi, vendor in enumerate(["Nvidia","AMD","Intel"]):
    sub = vram_bracket[vram_bracket["vendor"] == vendor]
    heights, labels_ann = [], []
    for lbl in blbls_v:
        row = sub[sub["price_bracket_v"] == lbl]
        h = round(row["vram_gb"].values[0], 1) if len(row) else None
        heights.append(h)
        labels_ann.append(f"{h:.0f}GB" if h else "")

    fig7.add_trace(go.Bar(
        x=blbls_v, y=heights,
        name=vendor,
        marker_color=VENDOR_COLOR[vendor],
        opacity=0.88,
        text=labels_ann,
        textposition="outside",
        textfont=dict(size=10, color="#444444"),
        hovertemplate=f"<b>{vendor}</b><br>%{{x}}<br>Avg VRAM: %{{y:.1f}}GB<extra></extra>",
    ))

# 8GB threshold line
fig7.add_hline(y=8, line_dash="dot", line_color="#cc3333", line_width=1.3, opacity=0.6,
               annotation_text="8GB threshold", annotation_position="top right",
               annotation_font=dict(color="#cc3333", size=10))

fig7_layout = {**BASE_LAYOUT, "margin": dict(l=50, r=20, t=45, b=35)}
fig7.update_layout(
    **fig7_layout,
    legend=dict(bgcolor="#ffffff", bordercolor=BORDER, borderwidth=1, font=dict(size=9, color=TEXT)),
    title=dict(
        text="<b>VRAM per Price Bracket — What Does Each Brand Actually Give You?</b><br>"
             "<span style='font-size:11px;color:#666'>RTX 4060 Ti (8GB, $399) vs RX 7800 XT (16GB, $499) is the defining mid-range comparison</span>",
        font=dict(size=13, color=TEXT), x=0.05,
    ),
    barmode="group",
    xaxis=dict(gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=SUBTEXT)),
    yaxis=dict(title="Average VRAM (GB)", gridcolor=GRID, linecolor=BORDER,
               tickfont=dict(color=SUBTEXT)),
    height=250,
)

# ── Strip grid lines from every figure ───────────────────────────────────────
for _fig in [fig1, fig2, fig3, fig4, fig5, fig6, fig7]:
    _fig.update_xaxes(showgrid=False, zeroline=False)
    _fig.update_yaxes(showgrid=False, zeroline=False)

# ── Render to HTML ────────────────────────────────────────────────────────────
def fig_to_div(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})

d1 = fig_to_div(fig1)
d2 = fig_to_div(fig2)
d3 = fig_to_div(fig3)
d4 = fig_to_div(fig4)
d5 = fig_to_div(fig5)
d6 = fig_to_div(fig6)
d7 = fig_to_div(fig7)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Upscaling Illusion: GPU Value Analysis 2018-2025</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: #f8f9fa;
    color: #1a1a1a;
    font-family: 'Segoe UI', system-ui, sans-serif;
    padding: 12px 16px;
    min-height: 100vh;
  }}

  /* ── Header ── */
  .header {{
    display: flex;
    align-items: baseline;
    gap: 14px;
    border-left: 4px solid #76b900;
    padding-left: 12px;
    margin-bottom: 10px;
  }}
  .header h1 {{ font-size: 17px; font-weight: 700; color: #1a1a1a; white-space: nowrap; }}
  .header p  {{ font-size: 11px; color: #888; }}

  /* ── Stat callouts ── */
  .stats {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 10px;
  }}
  .stat {{
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    border-top: 3px solid #76b900;
    padding: 10px 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }}
  .stat:nth-child(2) {{ border-top-color: #ED1C24; }}
  .stat:nth-child(3) {{ border-top-color: #f5a623; }}
  .stat:nth-child(4) {{ border-top-color: #0071c5; }}
  .stat-num  {{ font-size: 26px; font-weight: 700; line-height: 1.1; }}
  .stat-text {{ font-size: 10.5px; color: #666; margin-top: 3px; line-height: 1.4; }}

  /* ── Main charts ── */
  .main-charts {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 10px;
  }}

  /* ── Card ── */
  .card {{
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 8px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }}
  .card > div {{ width: 100%; }}

  /* ── Tab bar ── */
  .tab-bar {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    width: fit-content;
  }}
  .tab-label {{
    font-size: 10.5px;
    font-weight: 600;
    color: #999;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    white-space: nowrap;
    margin-right: 2px;
  }}
  .tab-btn {{
    background: #fff;
    border: 1px solid #d8d8d8;
    border-radius: 20px;
    padding: 6px 16px;
    font-size: 12px;
    font-family: inherit;
    color: #555;
    cursor: pointer;
    transition: background 0.13s, border-color 0.13s, color 0.13s;
    white-space: nowrap;
  }}
  .tab-btn:hover  {{ border-color: #76b900; color: #333; }}
  .tab-btn.active {{ background: #76b900; border-color: #76b900; color: #fff; font-weight: 600; }}

  /* ── Tab panel ── */
  .tab-panel {{ }}
  .tab-content         {{ display: none; }}
  .tab-content.active  {{ display: block; }}
  .tab-content > div   {{ width: 100%; }}

  /* ── Glossary ── */
  .glossary-row {{
    display: grid;
    grid-template-columns: 1fr 340px;
    gap: 10px;
    margin-top: 10px;
  }}
  .glossary-card {{ padding: 12px 16px !important; }}
  .glossary-title {{
    font-size: 10px; font-weight: 700; color: #aaa;
    text-transform: uppercase; letter-spacing: 0.08em;
    margin-bottom: 9px;
  }}
  .glossary-grid {{
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 5px 14px;
    align-items: baseline;
  }}
  .gt {{ font-size: 11.5px; font-weight: 600; color: #333; white-space: nowrap; }}
  .gd {{ font-size: 11px; color: #777; }}

  /* ── Responsive ── */
  @media (max-width: 860px) {{
    .main-charts   {{ grid-template-columns: 1fr; }}
    .stats         {{ grid-template-columns: repeat(2, 1fr); }}
    .header        {{ flex-direction: column; gap: 4px; }}
    .glossary-row  {{ grid-template-columns: 1fr; }}
    .tab-bar       {{ width: 100%; }}
  }}
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <h1>The Upscaling Illusion: GPU Value Analysis 2018–2025</h1>
  <p>Did AI upscaling genuinely improve value, or did it mask stagnant hardware progress while prices rose?</p>
</div>

<!-- Key stat callouts -->
<div class="stats">
  <div class="stat">
    <div class="stat-num" style="color:#76b900">~2×</div>
    <div class="stat-text">native silicon PPD gain<br>Nvidia RTX 2000 → RTX 5000 · 7 years</div>
  </div>
  <div class="stat">
    <div class="stat-num" style="color:#ED1C24">+42%</div>
    <div class="stat-text">Nvidia flagship price increase<br>inflation-adjusted 2024 dollars</div>
  </div>
  <div class="stat">
    <div class="stat-num" style="color:#f5a623">4×</div>
    <div class="stat-text">Nvidia effective PPD with DLSS + MFG<br>half from silicon · half AI-generated frames</div>
  </div>
  <div class="stat">
    <div class="stat-num" style="color:#0071c5">+50%</div>
    <div class="stat-text">RTX 3080 real avg cost over MSRP<br>$699 list · ~$1,050 actual · 2020–21 shortage</div>
  </div>
</div>

<!-- Always-visible: Divergence + Price Bracket side by side -->
<div class="main-charts">
  <div class="card">{d1}</div>
  <div class="card">{d5}</div>
</div>

<!-- Tab bar -->
<div class="tab-bar">
  <span class="tab-label">Explore more →</span>
  <button class="tab-btn active" data-tab="prices" onclick="showTab('prices')">📈 Flagship prices</button>
  <button class="tab-btn" data-tab="vram"   onclick="showTab('vram')"  >💾 VRAM breakdown</button>
  <button class="tab-btn" data-tab="street" onclick="showTab('street')">💰 MSRP vs actual paid</button>
</div>

<!-- Tab panel -->
<div class="tab-panel">
  <div class="card">
    <div class="tab-content active" id="chart-prices">{d2}</div>
    <div class="tab-content"        id="chart-vram"  >{d7}</div>
    <div class="tab-content"        id="chart-street">{d6}</div>
  </div>
</div>

<!-- Glossary -->
<div class="glossary-row">
  <div></div>
  <div class="card glossary-card">
    <div class="glossary-title">How to read this dashboard</div>
    <div class="glossary-grid">
      <span class="gt">PPD</span>
      <span class="gd">Performance Per Dollar — perf score ÷ 2024-adjusted launch price</span>
      <span class="gt">Native PPD</span>
      <span class="gd">Raw rasterisation only, zero AI assistance</span>
      <span class="gt">Effective PPD</span>
      <span class="gd">Native PPD × upscaling boost × frame generation multiplier</span>
      <span class="gt">Frame Gen</span>
      <span class="gd">AI-synthesised intermediate frames (RTX 4000+ · RX 7000+)</span>
      <span class="gt">MSRP</span>
      <span class="gd">Manufacturer list price at launch</span>
      <span class="gt">Street price</span>
      <span class="gd">Avg price buyers actually paid, tracked by Tom's Hardware &amp; Hardware Unboxed</span>
    </div>
  </div>
</div>

<script>
function showTab(name) {{
  document.querySelectorAll('.tab-content').forEach(function(el) {{ el.classList.remove('active'); }});
  document.querySelectorAll('.tab-btn').forEach(function(el) {{ el.classList.remove('active'); }});
  document.getElementById('chart-' + name).classList.add('active');
  document.querySelector('[data-tab="' + name + '"]').classList.add('active');
  // Trigger Plotly to resize to fit the newly visible container
  window.dispatchEvent(new Event('resize'));
}}
</script>

</body>
</html>"""

OUT.write_text(html, encoding="utf-8")
print(f"Written: {OUT}  ({OUT.stat().st_size // 1024} KB)")
