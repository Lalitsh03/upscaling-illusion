# The Upscaling Illusion
### Did AI features replace raw GPU performance — or just justify higher prices?

> An end-to-end data analysis project examining whether DLSS, FSR, and XeSS genuinely delivered better value per dollar across GPU generations, or whether manufacturers used AI upscaling as cover to slow raw hardware progress while raising prices.

---

## The Question

GPU manufacturers have spent the last three generations marketing AI upscaling as a revolution. DLSS 3, FSR 3, and XeSS all promise dramatically better performance with no extra silicon.

But strip out the AI-generated frames and ask what the hardware itself delivers: **has real performance per dollar improved, stagnated, or declined?**

This project answers that with data across Nvidia RTX 2000–5000, AMD RX 5000–9000, and Intel Arc A–B.

---

## Key Findings

### The divergence is real — but it is mostly frame generation

Raw (native) rasterization PPD improved modestly over ~7 years:

| Vendor | First Gen | Latest Gen | Native PPD Change |
|--------|-----------|-----------|-------------------|
| Nvidia | RTX 2000 (2018) | RTX 5000 (2025) | +101% |
| AMD | RX 5000 (2019) | RX 9000 (2025) | +72% |
| Intel | Arc A (2022) | Arc B (2024) | +46% |

Effective PPD with upscaling and frame generation tells a very different story:

- **Nvidia RTX 5000 with Multi Frame Gen reaches a 2.0× ratio vs native** — nearly half the stated performance gain comes from AI-generated frames, not rendered pixels
- Before frame generation existed (pre-2022), the upscaling ratio was only 1.1–1.3×

### Nvidia flagship prices rose 42% in real terms

| Generation | Avg Flagship Price (2024 USD) |
|-----------|-------------------------------|
| RTX 2000 (2018) | $746 |
| RTX 3000 (2020) | $904 (+21%) |
| RTX 4000 (2022) | $850 (-6%) |
| RTX 5000 (2025) | $1,057 (+24%) |

AMD moved in the opposite direction — flagship prices fell ~18% in real terms while native PPD improved.

### Generational leaps are getting smaller in raw terms

The RTX 4000 → RTX 5000 native PPD improvement (~26%) was the smallest single-generation jump in the dataset. Manufacturers are increasingly relying on AI features to justify upgrade cycles.

### The AMD brand halo did not appear in the data

AMD CPU share peaked at ~50% in 2021 — its strongest position in a decade. At that same moment, AMD GPU share was at its **lowest point (~18%)**. The correlation between AMD CPU and GPU market share over this period is **negative**.

---

## Dashboard Preview

The interactive dashboard (`looker/dashboard.html`) — open directly in any browser, no server needed.

Five visuals built in Plotly with a dark theme matching the Power BI version:

1. **The Divergence** — Raw vs Effective PPD per generation (small multiples: Nvidia / AMD / Intel)
2. **Flagship Price Trend** — 2024-adjusted USD with $999 reference line
3. **Frame Gen Breakdown** — Stacked bar splitting real vs artificial performance gains, with a vendor slicer
4. **CPU vs GPU Trajectory** — Growth rate comparison re-indexed to 2019=100
5. **AMD Brand Halo** — GPU share vs CPU share with the 2021 contradiction annotated

---

## Project Structure

```
.
├── data/
│   ├── raw/                   # Source CSVs: GPU specs, CPU benchmarks, CPI, market share
│   ├── processed/             # Cleaned data, exported charts (PNG)
│   └── powerbi/               # Reshaped CSVs for Power BI / Looker Studio (5 view tables)
│       ├── v1_divergence.csv
│       ├── v2_price_trend.csv
│       ├── v3_framegen_breakdown.csv
│       ├── v4_cpu_gpu_trajectory.csv
│       └── v5_brand_halo.csv
├── notebooks/
│   ├── 01_data_collection_and_cleaning.ipynb  # Load, validate, inflation-adjust, export to SQLite
│   └── 02_analysis.ipynb                      # Full analysis: divergence, price, CPU/GPU, brand halo
├── sql/
│   ├── 01_schema.sql              # SQLite schema documentation
│   └── 02_analysis_queries.sql   # 9 analysis queries — DBeaver-ready
├── powerbi/
│   ├── upscaling_illusion_dashboard.pbix
│   └── POWER_BI_BUILD_GUIDE.md   # Step-by-step build guide
└── looker/
    ├── dashboard.html             # Standalone interactive dashboard
    └── build_dashboard.py         # Script to regenerate dashboard.html
```

---

## Methodology

### Performance Per Dollar (PPD)

The core metric. For each GPU:

```
PPD (native)  = perf_score_native_1440p  / launch_price_2024_adj
PPD (no FG)   = perf_score_native × upscaling_boost_no_fg   / launch_price_2024_adj
PPD (with FG) = perf_score_native × upscaling_boost_with_fg / launch_price_2024_adj
```

`perf_score_native_1440p` is a 1440p rasterization index benchmarked relative to the RTX 3080 at launch = 100. Upscaling boost multipliers reflect quality-mode upscaling and frame generation gains per technology version.

| Technology | Upscaling only | With Frame Gen |
|-----------|---------------|---------------|
| DLSS 2.x | 1.30× | 1.30× (no FG on RTX 3000) |
| DLSS 3.x | 1.30× | 1.70× |
| DLSS 4.x (MFG) | 1.35× | 2.00× |
| FSR 2.x | 1.25× | 1.25× (no FG on RX 6000) |
| FSR 3.x | 1.25× | 1.65× |
| FSR 4.x | 1.35× | 1.75× |
| XeSS 1.x | 1.20× | 1.20× |
| XeSS 2.x | 1.35× | 1.35× |

Frame generation is tracked separately (`fg_inflation_factor`) because it generates interpolated frames rather than rendering them — inflating FPS without improving input latency.

### Inflation Adjustment

All launch prices converted to **2024 USD** using US Bureau of Labor Statistics CPI annual multipliers, making a 2018 $499 GPU directly comparable to a 2025 $599 GPU.

### CPU vs GPU Trajectory

Both CPU (single-thread) and GPU (1440p raster) series re-indexed to their own **2019 = 100** baseline so growth *rates* are comparable across different benchmark scales.

---

## How to Reproduce

**Requirements:** Python 3.10+

```bash
# 1. Clone
git clone https://github.com/Lalitsh03/upscaling-illusion.git
cd upscaling-illusion

# 2. Install dependencies
pip install pandas numpy matplotlib seaborn plotly nbformat jupyter

# 3. Run the notebooks in order
jupyter notebook notebooks/01_data_collection_and_cleaning.ipynb
jupyter notebook notebooks/02_analysis.ipynb

# 4. Regenerate the interactive HTML dashboard
python looker/build_dashboard.py
# Output: looker/dashboard.html — open in any browser
```

**SQL:** Open `data/gpu_analysis.db` in DBeaver, then run any query from `sql/02_analysis_queries.sql`.

---

## Limitations

- Benchmark data is not always directly comparable across generations — different test rigs and game mixes
- Upscaling boost multipliers are averages; per-game variance is high
- Frame generation adds input latency not captured in raw FPS metrics
- Market share data is estimated from JPR composites and Steam Hardware Survey
- Correlation ≠ causation throughout, especially the brand halo section

---

## Tools

| Layer | Tools |
|-------|-------|
| Data wrangling | Python 3.13, Pandas, NumPy |
| Database | SQLite, DBeaver |
| Analysis & charts | Matplotlib, Seaborn, Plotly |
| Dashboards | Power BI Desktop, Plotly HTML |
| Version control | Git, GitHub |

---

## Interview One-Liner

*"I found that AI upscaling genuinely improved value per dollar — but the headline numbers are misleading. Strip out frame generation, and Nvidia's native raw performance improved only ~100% over 7 years while prices rose 42% in real terms. The technology is real; the framing around it is marketing."*
