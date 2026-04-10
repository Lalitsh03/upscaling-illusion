"""
The Upscaling Illusion — Interactive HTML Dashboard
Generates a standalone dashboard.html that mirrors the Power BI layout.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "powerbi"
OUT_FILE = Path(__file__).parent / "dashboard.html"

# ── Load data ──────────────────────────────────────────────────────────────────
v1 = pd.read_csv(DATA_DIR / "v1_divergence.csv")
v2 = pd.read_csv(DATA_DIR / "v2_price_trend.csv")
v3 = pd.read_csv(DATA_DIR / "v3_framegen_breakdown.csv")
v4 = pd.read_csv(DATA_DIR / "v4_cpu_gpu_trajectory.csv")
v5 = pd.read_csv(DATA_DIR / "v5_brand_halo.csv")

# ── Colours ────────────────────────────────────────────────────────────────────
C = {
    "blue":       "#4472C4",
    "orange":     "#ED7D31",
    "green":      "#70AD47",
    "red":        "#C00000",
    "nvidia":     "#76b900",
    "amd":        "#ed1c24",
    "intel":      "#0071c5",
    "amd_orange": "#FF8C00",
    "grey":       "#888888",
    "bg":         "#1a1a2e",
    "card":       "#16213e",
    "text":       "#e0e0e0",
    "subtext":    "#a0a0b0",
}

METRIC_COLORS = {
    "Raw rasterization (native)":   C["blue"],
    "Upscaling — no Frame Gen":     C["orange"],
    "Upscaling + Frame Gen":        C["green"],
}

LAYER_COLORS = {
    "1 Raw performance":            C["blue"],
    "2 Upscaling quality gain":     C["orange"],
    "3 Frame Gen gain (artificial frames)": C["red"],
}

VENDOR_ORDER = ["Nvidia", "AMD", "Intel"]

# ── Helper ─────────────────────────────────────────────────────────────────────
def card_style():
    return dict(
        bgcolor=C["card"],
        bordercolor="#2a2a4a",
        font_color=C["text"],
    )

# ══════════════════════════════════════════════════════════════════════════════
# CHART 1 — The Divergence  (small multiples: Nvidia | AMD | Intel)
# ══════════════════════════════════════════════════════════════════════════════
def build_chart1():
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=["Nvidia", "AMD", "Intel"],
        shared_yaxes=True,
        horizontal_spacing=0.05,
    )

    metrics_ordered = [
        "Raw rasterization (native)",
        "Upscaling — no Frame Gen",
        "Upscaling + Frame Gen",
    ]

    for col_idx, vendor in enumerate(VENDOR_ORDER, start=1):
        df = v1[v1["vendor"] == vendor].copy()
        df = df.sort_values("gen_launch_year")

        for metric in metrics_ordered:
            sub = df[df["metric_label"] == metric]
            if sub.empty:
                continue
            fig.add_trace(
                go.Scatter(
                    x=sub["generation"],
                    y=sub["perf_per_dollar"],
                    mode="lines+markers",
                    name=metric,
                    line=dict(color=METRIC_COLORS[metric], width=2.5),
                    marker=dict(size=8),
                    showlegend=(col_idx == 1),
                    legendgroup=metric,
                    hovertemplate=(
                        f"<b>{vendor}</b><br>"
                        "%{x}<br>"
                        "PPD: %{y:.3f}<extra></extra>"
                    ),
                ),
                row=1, col=col_idx,
            )

    fig.update_layout(
        title=dict(
            text="<b>The Divergence: Raw vs Effective Performance Per Dollar</b><br>"
                 "<span style='font-size:12px;color:#a0a0b0'>"
                 "Frame Generation (RTX 4000+ / RX 7000+) drives most of the gap</span>",
            font_size=16,
            font_color=C["text"],
            x=0.5,
        ),
        paper_bgcolor=C["bg"],
        plot_bgcolor=C["card"],
        font_color=C["text"],
        legend=dict(
            orientation="h",
            yanchor="bottom", y=-0.25,
            xanchor="center", x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font_size=11,
        ),
        margin=dict(t=100, b=80, l=50, r=20),
        height=380,
        annotations=[
            dict(
                x=0.98, y=0.98,
                xref="paper", yref="paper",
                text=(
                    "RTX 5000 Multi Frame Gen shows 2× effective PPD vs raw —<br>"
                    "but nearly half that gain comes from AI-generated frames,<br>"
                    "not rendered pixels."
                ),
                showarrow=False,
                align="right",
                font=dict(size=9, color=C["subtext"]),
                bgcolor="rgba(26,26,46,0.8)",
                bordercolor="#2a2a4a",
                borderwidth=1,
            )
        ],
    )
    fig.update_xaxes(showgrid=False, linecolor="#2a2a4a", tickfont_size=10)
    fig.update_yaxes(showgrid=True, gridcolor="#2a2a4a", tickformat=".2f", title_text="Perf / Dollar", col=1)
    for ann in fig.layout.annotations[:3]:  # subplot titles
        ann.font.color = C["subtext"]
        ann.font.size = 12
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# CHART 2 — Flagship Price Trend
# ══════════════════════════════════════════════════════════════════════════════
def build_chart2():
    df = v2[v2["gpu_name"] == "GEN_AVG"].copy()
    df = df.sort_values("launch_year")

    fig = go.Figure()

    vendor_colors = {"Nvidia": C["nvidia"], "AMD": C["amd"], "Intel": C["intel"]}

    for vendor in VENDOR_ORDER:
        sub = df[df["vendor"] == vendor]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["launch_year"],
            y=sub["real_price_2024"],
            mode="lines+markers",
            name=vendor,
            line=dict(color=vendor_colors[vendor], width=2.5),
            marker=dict(size=9),
            hovertemplate=(
                f"<b>{vendor}</b><br>"
                "Year: %{x}<br>"
                "Price (2024 USD): $%{y:,.0f}<extra></extra>"
            ),
        ))

    # $999 reference line
    fig.add_hline(
        y=999,
        line=dict(color=C["grey"], dash="dash", width=1.5),
        annotation_text="$999 ceiling",
        annotation_position="bottom right",
        annotation_font=dict(color=C["subtext"], size=10),
    )

    fig.update_layout(
        title=dict(
            text="<b>Flagship GPU Price — 2024-Adjusted USD</b>",
            font_size=14, font_color=C["text"], x=0.5,
        ),
        paper_bgcolor=C["bg"],
        plot_bgcolor=C["card"],
        font_color=C["text"],
        xaxis=dict(showgrid=False, linecolor="#2a2a4a", dtick=1),
        yaxis=dict(
            showgrid=True, gridcolor="#2a2a4a",
            tickprefix="$", tickformat=",",
        ),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=60, b=40, l=60, r=20),
        height=320,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# CHART 3 — Frame Gen Stacked Bar
# ══════════════════════════════════════════════════════════════════════════════
def build_chart3(vendor_filter=None):
    df = v3.copy()
    if vendor_filter:
        df = df[df["vendor"] == vendor_filter]
    df = df.sort_values(["gen_launch_year", "stack_order"])

    layers_ordered = [
        "1 Raw performance",
        "2 Upscaling quality gain",
        "3 Frame Gen gain (artificial frames)",
    ]

    fig = go.Figure()

    # Group by vendor+generation for x-axis labels
    df["x_label"] = df["vendor"] + "<br>" + df["generation"]

    for layer in layers_ordered:
        sub = df[df["layer_label"] == layer]
        fig.add_trace(go.Bar(
            x=sub["x_label"],
            y=sub["ppd_value"],
            name=layer,
            marker_color=LAYER_COLORS.get(layer, "#999"),
            hovertemplate=(
                "<b>%{x}</b><br>"
                f"{layer}<br>"
                "PPD contribution: %{y:.3f}<extra></extra>"
            ),
        ))

    fig.update_layout(
        barmode="stack",
        title=dict(
            text="<b>Effective PPD — What Drives the Gain?</b><br>"
                 "<span style='font-size:11px;color:#C00000'>■ Red = AI-generated frames (not rendered pixels)</span>",
            font_size=14, font_color=C["text"], x=0.5,
        ),
        paper_bgcolor=C["bg"],
        plot_bgcolor=C["card"],
        font_color=C["text"],
        xaxis=dict(showgrid=False, linecolor="#2a2a4a", tickfont_size=9),
        yaxis=dict(showgrid=True, gridcolor="#2a2a4a", tickformat=".2f"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5,
                    bgcolor="rgba(0,0,0,0)", font_size=10),
        margin=dict(t=80, b=80, l=50, r=20),
        height=380,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# CHART 4 — CPU vs GPU Growth Trajectory
# ══════════════════════════════════════════════════════════════════════════════
def build_chart4():
    df = v4.copy().sort_values("year")

    series_styles = {
        "GPU: Nvidia Flagship (1440p raster)": dict(color=C["nvidia"], dash="solid",  width=2.5),
        "GPU: AMD Flagship (1440p raster)":    dict(color=C["red"],    dash="solid",  width=2.5),
        "CPU: Intel Flagship (single-thread)": dict(color=C["intel"],  dash="dash",   width=1.5),
        "CPU: AMD Flagship (single-thread)":   dict(color=C["amd_orange"], dash="dash", width=1.5),
    }

    fig = go.Figure()

    for label, style in series_styles.items():
        sub = df[df["series_label"] == label]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["year"],
            y=sub["perf_index_2019_100"],
            mode="lines+markers",
            name=label,
            line=dict(color=style["color"], dash=style["dash"], width=style["width"]),
            marker=dict(size=7),
            hovertemplate=(
                "<b>%{fullData.name}</b><br>"
                "Year: %{x}<br>"
                "Index: %{y:.1f}<extra></extra>"
            ),
        ))

    # 2019 baseline
    fig.add_hline(y=100, line=dict(color=C["grey"], dash="dot", width=1),
                  annotation_text="2019 baseline = 100",
                  annotation_position="bottom left",
                  annotation_font=dict(color=C["subtext"], size=9))

    # Frame Gen era
    fig.add_vline(x=2022, line=dict(color=C["grey"], dash="dot", width=1),
                  annotation_text="Frame Gen era begins",
                  annotation_position="top right",
                  annotation_font=dict(color=C["subtext"], size=9))

    fig.update_layout(
        title=dict(
            text="<b>CPU vs GPU Performance Growth — Flagship Tier</b>",
            font_size=14, font_color=C["text"], x=0.5,
        ),
        paper_bgcolor=C["bg"],
        plot_bgcolor=C["card"],
        font_color=C["text"],
        xaxis=dict(showgrid=False, linecolor="#2a2a4a", dtick=1),
        yaxis=dict(showgrid=True, gridcolor="#2a2a4a", ticksuffix=" idx"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font_size=10),
        margin=dict(t=60, b=60, l=60, r=20),
        height=320,
        annotations=[
            dict(
                x=0.01, y=-0.18,
                xref="paper", yref="paper",
                text="Note: Each series uses its own 2019 baseline = 100. "
                     "This chart compares growth rates, not absolute performance.",
                showarrow=False,
                font=dict(size=9, color=C["subtext"]),
                align="left",
            )
        ],
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# CHART 5 — AMD Brand Halo
# ══════════════════════════════════════════════════════════════════════════════
def build_chart5():
    df = v5.copy().sort_values("year")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["year"], y=df["amd_gpu_share"],
        mode="lines+markers",
        name="AMD GPU share %",
        line=dict(color=C["red"], width=2.5),
        marker=dict(size=8),
        hovertemplate="Year: %{x}<br>AMD GPU share: %{y:.1f}%<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df["year"], y=df["amd_cpu_share"],
        mode="lines+markers",
        name="AMD CPU share %",
        line=dict(color=C["amd_orange"], dash="dash", width=2),
        marker=dict(size=8, symbol="diamond"),
        hovertemplate="Year: %{x}<br>AMD CPU share: %{y:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        title=dict(
            text="<b>AMD Brand Halo — Did Ryzen Pull GPU Share?</b>",
            font_size=14, font_color=C["text"], x=0.5,
        ),
        paper_bgcolor=C["bg"],
        plot_bgcolor=C["card"],
        font_color=C["text"],
        xaxis=dict(showgrid=False, linecolor="#2a2a4a", dtick=1),
        yaxis=dict(showgrid=True, gridcolor="#2a2a4a", ticksuffix="%", range=[0, 70]),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=60, b=60, l=50, r=20),
        height=320,
        annotations=[
            dict(
                x=2021, y=18.25,
                xref="x", yref="y",
                text="AMD CPU peaked ~50%<br>but GPU share hit lowest (18%)<br>— brand halo did not appear",
                showarrow=True,
                arrowhead=2,
                arrowcolor=C["subtext"],
                ax=80, ay=-60,
                font=dict(size=9, color=C["subtext"]),
                bgcolor="rgba(26,26,46,0.85)",
                bordercolor="#2a2a4a",
                borderwidth=1,
            ),
            dict(
                x=0.01, y=-0.18,
                xref="paper", yref="paper",
                text="Correlation analysis only — causation not claimed.",
                showarrow=False,
                font=dict(size=8, color=C["subtext"], style="italic"),
                align="left",
            ),
        ],
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# ASSEMBLE HTML
# ══════════════════════════════════════════════════════════════════════════════
def chart_html(fig, full_html=False):
    return pio.to_html(fig, include_plotlyjs=False, full_html=full_html, config={"responsive": True})


def build_html():
    c1 = chart_html(build_chart1())
    c2 = chart_html(build_chart2())
    c3 = chart_html(build_chart3())
    c4 = chart_html(build_chart4())
    c5 = chart_html(build_chart5())

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
    background: #1a1a2e;
    color: #e0e0e0;
    font-family: 'Segoe UI', system-ui, sans-serif;
    padding: 24px;
  }}
  .header {{
    margin-bottom: 24px;
  }}
  .header h1 {{
    font-size: 22px;
    font-weight: 700;
    color: #e0e0e0;
    margin-bottom: 6px;
  }}
  .header p {{
    font-size: 13px;
    color: #a0a0b0;
  }}
  .slicer-row {{
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
    align-items: center;
  }}
  .slicer-label {{
    font-size: 12px;
    color: #a0a0b0;
    margin-right: 4px;
  }}
  .slicer-btn {{
    padding: 5px 16px;
    border-radius: 4px;
    border: 1px solid #4472C4;
    background: transparent;
    color: #e0e0e0;
    cursor: pointer;
    font-size: 12px;
    transition: background 0.15s;
  }}
  .slicer-btn:hover, .slicer-btn.active {{
    background: #4472C4;
    color: #fff;
  }}
  .grid {{
    display: grid;
    gap: 16px;
  }}
  .row-full  {{ grid-template-columns: 1fr; }}
  .row-split {{ grid-template-columns: 1fr 1fr; }}
  .row-split3 {{ grid-template-columns: 1.1fr 1fr 1fr; }}
  .card {{
    background: #16213e;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    padding: 12px;
    overflow: hidden;
  }}
  .card > div {{ width: 100%; }}
  @media (max-width: 900px) {{
    .row-split, .row-split3 {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

<div class="header">
  <h1>The Upscaling Illusion: GPU Value Analysis 2018–2025</h1>
  <p>Did AI upscaling genuinely improve value — or did it mask stagnant hardware progress?</p>
</div>

<!-- Slicer for Chart 3 -->
<div class="slicer-row">
  <span class="slicer-label">Filter Chart 3 by vendor:</span>
  <button class="slicer-btn active" onclick="filterChart3('All')">All</button>
  <button class="slicer-btn" onclick="filterChart3('Nvidia')">Nvidia</button>
  <button class="slicer-btn" onclick="filterChart3('AMD')">AMD</button>
  <button class="slicer-btn" onclick="filterChart3('Intel')">Intel</button>
</div>

<!-- Row 1: Chart 1 (full width) -->
<div class="grid row-full" style="margin-bottom:16px">
  <div class="card">{c1}</div>
</div>

<!-- Row 2: Chart 2 | Chart 3 -->
<div class="grid row-split" style="margin-bottom:16px">
  <div class="card">{c2}</div>
  <div class="card" id="chart3-container">{c3}</div>
</div>

<!-- Row 3: Chart 4 | Chart 5 -->
<div class="grid row-split" style="margin-bottom:16px">
  <div class="card">{c4}</div>
  <div class="card">{c5}</div>
</div>

<script>
// ── Vendor slicer data for Chart 3 ──────────────────────────────────────────
const v3data = {{}};

// Pre-compute filtered traces per vendor from the embedded data
// We re-render chart3 from raw data via Plotly.newPlot

const RAW_V3 = {v3.to_json(orient='records')};

const LAYER_ORDER = [
  "1 Raw performance",
  "2 Upscaling quality gain",
  "3 Frame Gen gain (artificial frames)"
];
const LAYER_COLORS = {{
  "1 Raw performance":            "#4472C4",
  "2 Upscaling quality gain":     "#ED7D31",
  "3 Frame Gen gain (artificial frames)": "#C00000"
}};

function buildChart3Traces(vendorFilter) {{
  const rows = vendorFilter === 'All' ? RAW_V3 : RAW_V3.filter(r => r.vendor === vendorFilter);
  const xLabels = [...new Set(rows.map(r => r.vendor + "<br>" + r.generation))];

  return LAYER_ORDER.map(layer => {{
    const sub = rows.filter(r => r.layer_label === layer);
    return {{
      type: 'bar',
      name: layer,
      x: sub.map(r => r.vendor + "<br>" + r.generation),
      y: sub.map(r => r.ppd_value),
      marker: {{ color: LAYER_COLORS[layer] }},
      hovertemplate: '<b>%{{x}}</b><br>' + layer + '<br>PPD: %{{y:.3f}}<extra></extra>'
    }};
  }});
}}

function filterChart3(vendor) {{
  // Update button states
  document.querySelectorAll('.slicer-btn').forEach(b => {{
    b.classList.toggle('active', b.textContent === vendor || (vendor === 'All' && b.textContent === 'All'));
  }});

  const container = document.getElementById('chart3-container');
  const plotDiv = container.querySelector('.plotly-graph-div') || container.querySelector('[id^="chart3"]');
  if (!plotDiv) return;

  const traces = buildChart3Traces(vendor);
  const layout = {{
    barmode: 'stack',
    title: {{
      text: '<b>Effective PPD — What Drives the Gain?</b><br><span style="font-size:11px;color:#C00000">■ Red = AI-generated frames (not rendered pixels)</span>',
      font: {{ size: 14, color: '#e0e0e0' }}, x: 0.5
    }},
    paper_bgcolor: '#1a1a2e',
    plot_bgcolor: '#16213e',
    font: {{ color: '#e0e0e0' }},
    xaxis: {{ showgrid: false, linecolor: '#2a2a4a', tickfont: {{ size: 9 }} }},
    yaxis: {{ showgrid: true, gridcolor: '#2a2a4a', tickformat: '.2f' }},
    legend: {{ orientation: 'h', yanchor: 'bottom', y: -0.35, xanchor: 'center', x: 0.5,
               bgcolor: 'rgba(0,0,0,0)', font: {{ size: 10 }} }},
    margin: {{ t: 80, b: 80, l: 50, r: 20 }},
    height: 380
  }};
  Plotly.react(plotDiv, traces, layout, {{responsive: true}});
}}

// Wire up slicer on load
document.addEventListener('DOMContentLoaded', () => filterChart3('All'));
</script>
</body>
</html>
"""
    return html


if __name__ == "__main__":
    print("Building dashboard...")
    html = build_html()
    OUT_FILE.write_text(html, encoding="utf-8")
    print(f"Done → {OUT_FILE}")
