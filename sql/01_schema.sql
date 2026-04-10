-- =============================================================
-- The Upscaling Illusion — SQLite Schema
-- =============================================================

-- Raw GPU specs and performance data (loaded from gpu_specs_seed.csv)
CREATE TABLE IF NOT EXISTS gpu_specs (
    gpu_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    gpu_name            TEXT NOT NULL,
    vendor              TEXT NOT NULL CHECK(vendor IN ('Nvidia','AMD','Intel')),
    generation          TEXT NOT NULL,
    tier                TEXT NOT NULL CHECK(tier IN ('budget','mid','high','flagship')),
    launch_year         INTEGER NOT NULL,
    launch_month        INTEGER NOT NULL,
    launch_price_usd    REAL NOT NULL,
    tdp_watts           INTEGER,
    vram_gb             INTEGER,
    process_node_nm     INTEGER,
    upscaling_tech      TEXT,
    upscaling_version   TEXT,
    upscaling_boost_no_fg  REAL DEFAULT 1.0,   -- perf multiplier from upscaling alone
    upscaling_boost_with_fg REAL DEFAULT 1.0,  -- perf multiplier including frame generation
    perf_score_native_1440p REAL,              -- rasterization index, RTX 3080 = 100
    notes               TEXT
);

-- CPI data for inflation adjustment
CREATE TABLE IF NOT EXISTS cpi_annual (
    year                INTEGER PRIMARY KEY,
    cpi_index           REAL,
    multiplier_to_2024  REAL  -- multiply launch price by this to get 2024 dollars
);

-- Derived/calculated table — populated by Python, queried in Power BI / Looker
CREATE TABLE IF NOT EXISTS gpu_analysis (
    gpu_id                          INTEGER PRIMARY KEY REFERENCES gpu_specs(gpu_id),
    gpu_name                        TEXT,
    vendor                          TEXT,
    generation                      TEXT,
    tier                            TEXT,
    launch_year                     INTEGER,
    launch_price_usd                REAL,
    launch_price_2024_adj           REAL,   -- inflation-adjusted to 2024 dollars
    perf_score_native               REAL,   -- raw rasterization index
    perf_score_effective_no_fg      REAL,   -- native × upscaling_boost_no_fg
    perf_score_effective_with_fg    REAL,   -- native × upscaling_boost_with_fg
    perf_per_dollar_native          REAL,   -- perf_score_native / launch_price_2024_adj
    perf_per_dollar_effective_no_fg REAL,
    perf_per_dollar_effective_with_fg REAL,
    fg_inflation_factor             REAL    -- effective_with_fg / effective_no_fg (measures frame gen contribution)
);

-- GPU market share over time
CREATE TABLE IF NOT EXISTS gpu_market_share (
    share_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    year        INTEGER,
    quarter     TEXT,
    nvidia_pct  REAL,
    amd_pct     REAL,
    intel_pct   REAL,
    source_notes TEXT
);

-- CPU benchmark data for CPU-vs-GPU trajectory comparison
CREATE TABLE IF NOT EXISTS cpu_benchmarks (
    cpu_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cpu_name            TEXT,
    vendor              TEXT,
    generation          TEXT,
    tier                TEXT,
    launch_year         INTEGER,
    launch_month        INTEGER,
    launch_price_usd    REAL,
    tdp_watts           INTEGER,
    cores               INTEGER,
    process_node_nm     INTEGER,
    perf_score_st       REAL,   -- single-thread index, Core i7-8700K = 100
    perf_score_mt       REAL,   -- multi-thread index, Core i7-8700K = 100
    notes               TEXT
);

-- AMD CPU market share for brand halo subsection
CREATE TABLE IF NOT EXISTS amd_cpu_market_share (
    share_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    year            INTEGER,
    quarter         TEXT,
    intel_cpu_pct   REAL,
    amd_cpu_pct     REAL,
    source_notes    TEXT
);
