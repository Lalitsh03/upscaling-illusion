-- =============================================================
-- The Upscaling Illusion — Core Analysis Queries
-- =============================================================
-- Run these in DBeaver against:
--   C:\Users\lalit\my-dashboard-project\data\gpu_analysis.db
--
-- NOTE on column name: the raw perf column in gpu_analysis is
--   perf_score_native_1440p  (not perf_score_native)
-- All queries below use the correct name.
-- =============================================================


-- ---------------------------------------------------------------
-- QUERY 1: The Divergence Table
-- Raw vs Effective perf/dollar across all GPUs, sorted by generation
-- This is the headline finding.
-- ---------------------------------------------------------------
SELECT
    vendor,
    generation,
    gpu_name,
    tier,
    launch_year,
    ROUND(launch_price_2024_adj, 0)                   AS price_2024_usd,
    ROUND(perf_score_native_1440p, 1)                 AS raw_perf,
    ROUND(perf_score_effective_no_fg, 1)              AS effective_perf_no_fg,
    ROUND(perf_score_effective_with_fg, 1)            AS effective_perf_with_fg,
    ROUND(perf_per_dollar_native, 3)                  AS ppd_native,
    ROUND(perf_per_dollar_effective_no_fg, 3)         AS ppd_eff_no_fg,
    ROUND(perf_per_dollar_effective_with_fg, 3)       AS ppd_eff_with_fg,
    ROUND(fg_inflation_factor, 2)                     AS frame_gen_contribution
FROM gpu_analysis
ORDER BY vendor, launch_year, perf_score_native_1440p;


-- ---------------------------------------------------------------
-- QUERY 2: Generation-Level Average — Per Vendor
-- Aggregates to generation level for the main trend chart
-- ---------------------------------------------------------------
SELECT
    vendor,
    generation,
    MIN(launch_year)                                  AS gen_launch_year,
    COUNT(*)                                          AS gpu_count,
    ROUND(AVG(launch_price_2024_adj), 0)              AS avg_price_2024_adj,
    ROUND(AVG(perf_score_native_1440p), 1)            AS avg_raw_perf,
    ROUND(AVG(perf_score_effective_no_fg), 1)         AS avg_eff_perf_no_fg,
    ROUND(AVG(perf_score_effective_with_fg), 1)       AS avg_eff_perf_with_fg,
    ROUND(AVG(perf_per_dollar_native), 4)             AS avg_ppd_native,
    ROUND(AVG(perf_per_dollar_effective_no_fg), 4)    AS avg_ppd_eff_no_fg,
    ROUND(AVG(perf_per_dollar_effective_with_fg), 4)  AS avg_ppd_eff_with_fg
FROM gpu_analysis
GROUP BY vendor, generation
ORDER BY vendor, gen_launch_year;


-- ---------------------------------------------------------------
-- QUERY 3: Tier-Locked Comparison (apples-to-apples)
-- Tracks same price tier across generations — avoids mixing
-- budget and flagship GPUs diluting the averages.
-- ---------------------------------------------------------------
SELECT
    vendor,
    tier,
    generation,
    MIN(launch_year)                                  AS gen_launch_year,
    ROUND(AVG(launch_price_2024_adj), 0)              AS avg_price_2024_adj,
    ROUND(AVG(perf_per_dollar_native), 4)             AS avg_ppd_native,
    ROUND(AVG(perf_per_dollar_effective_with_fg), 4)  AS avg_ppd_eff_with_fg,
    ROUND(
        AVG(perf_per_dollar_effective_with_fg)
        / AVG(perf_per_dollar_native), 2
    )                                                 AS upscaling_ppd_multiplier
FROM gpu_analysis
WHERE tier IN ('mid', 'high', 'flagship')
GROUP BY vendor, tier, generation
ORDER BY vendor, tier, gen_launch_year;


-- ---------------------------------------------------------------
-- QUERY 4: Frame Generation Contribution to Perceived Value
-- Splits effective PPD gain into two buckets:
--   pct_gain_from_upscaling = real quality improvement (rendered pixels)
--   pct_gain_from_framegen  = artificial frames injected by AI
-- ---------------------------------------------------------------
SELECT
    vendor,
    generation,
    gpu_name,
    launch_year,
    ROUND(perf_per_dollar_native, 4)                  AS ppd_native,
    ROUND(perf_per_dollar_effective_no_fg, 4)         AS ppd_real_upscaling,
    ROUND(perf_per_dollar_effective_with_fg, 4)       AS ppd_with_framegen,
    ROUND(
        (perf_per_dollar_effective_no_fg - perf_per_dollar_native)
        / perf_per_dollar_native * 100, 1
    )                                                 AS pct_gain_from_upscaling,
    ROUND(
        (perf_per_dollar_effective_with_fg - perf_per_dollar_effective_no_fg)
        / perf_per_dollar_effective_no_fg * 100, 1
    )                                                 AS pct_gain_from_framegen
FROM gpu_analysis
ORDER BY vendor, launch_year;


-- ---------------------------------------------------------------
-- QUERY 5: Launch Price Trend — Nominal vs Inflation-Adjusted
-- Per tier, per vendor — shows if real prices actually went up.
-- inflation_adjustment_pct: how much MORE you pay vs nominal
--   due to inflation (positive = price was understated in nominal $)
-- ---------------------------------------------------------------
SELECT
    vendor,
    tier,
    generation,
    MIN(launch_year)                                  AS gen_launch_year,
    ROUND(AVG(launch_price_usd), 0)                   AS avg_nominal_price,
    ROUND(AVG(launch_price_2024_adj), 0)              AS avg_real_price_2024,
    ROUND(
        (AVG(launch_price_2024_adj) - AVG(launch_price_usd))
        / AVG(launch_price_usd) * 100, 1
    )                                                 AS inflation_adjustment_pct
FROM gpu_analysis
WHERE tier IN ('mid', 'high', 'flagship')
GROUP BY vendor, tier, generation
ORDER BY vendor, tier, gen_launch_year;


-- ---------------------------------------------------------------
-- QUERY 6: CPU vs GPU Performance Growth (Subsection 2)
-- UNIONs GPU and CPU flagship series.
-- Both indexed to their own 2019 baseline in Python analysis —
-- here we return raw scores so DBeaver can inspect the source data.
-- Single-thread CPU score used (most relevant for gaming perf).
-- ---------------------------------------------------------------
SELECT
    'GPU'           AS component_type,
    vendor,
    generation,
    MIN(launch_year)                                  AS launch_year,
    ROUND(AVG(perf_score_native_1440p), 1)            AS avg_perf_score,
    ROUND(AVG(perf_per_dollar_native), 4)             AS avg_ppd
FROM gpu_analysis
WHERE tier = 'flagship'
GROUP BY vendor, generation

UNION ALL

SELECT
    'CPU'           AS component_type,
    cb.vendor,
    cb.generation,
    MIN(cb.launch_year)                               AS launch_year,
    ROUND(AVG(cb.perf_score_st), 1)                   AS avg_perf_score,
    ROUND(
        AVG(cb.perf_score_st
            / (cb.launch_price_usd * COALESCE(c.multiplier_to_2024, 1.0))),
        4
    )                                                 AS avg_ppd
FROM cpu_benchmarks cb
LEFT JOIN cpi_annual c ON cb.launch_year = c.year
WHERE cb.tier = 'flagship'
GROUP BY cb.vendor, cb.generation

ORDER BY component_type, vendor, launch_year;


-- ---------------------------------------------------------------
-- QUERY 7: AMD Brand Halo — GPU share vs CPU share (Subsection 3)
-- Both tables use different quarter cadences so we average to annual.
-- amd_gpu_minus_cpu_gap: negative = GPU share lags CPU share
-- ---------------------------------------------------------------
WITH gpu_annual AS (
    SELECT
        year,
        ROUND(AVG(amd_pct), 2)    AS amd_gpu_share_pct,
        ROUND(AVG(nvidia_pct), 2) AS nvidia_gpu_share_pct
    FROM gpu_market_share
    GROUP BY year
),
cpu_annual AS (
    SELECT
        year,
        ROUND(AVG(amd_cpu_pct), 2)   AS amd_cpu_share_pct,
        ROUND(AVG(intel_cpu_pct), 2) AS intel_cpu_share_pct
    FROM amd_cpu_market_share
    GROUP BY year
)
SELECT
    g.year,
    g.amd_gpu_share_pct,
    c.amd_cpu_share_pct,
    g.nvidia_gpu_share_pct,
    c.intel_cpu_share_pct,
    ROUND(g.amd_gpu_share_pct - c.amd_cpu_share_pct,  1) AS amd_gpu_minus_cpu_gap,
    ROUND(g.nvidia_gpu_share_pct - c.intel_cpu_share_pct, 1) AS nvidia_intel_gap
FROM gpu_annual g
JOIN cpu_annual c ON g.year = c.year
ORDER BY g.year;


-- ---------------------------------------------------------------
-- QUERY 8: Best Raw Value Per Generation
-- Ranks every GPU within its generation by native PPD.
-- Use this to find the "sweet spot" GPU per generation.
-- ---------------------------------------------------------------
SELECT
    vendor,
    generation,
    gpu_name,
    tier,
    launch_year,
    ROUND(launch_price_2024_adj, 0)                   AS price_2024_usd,
    ROUND(perf_per_dollar_native, 4)                  AS ppd_native,
    RANK() OVER (
        PARTITION BY generation, vendor
        ORDER BY perf_per_dollar_native DESC
    )                                                 AS value_rank_in_gen
FROM gpu_analysis
ORDER BY vendor, launch_year, value_rank_in_gen
;


-- ---------------------------------------------------------------
-- QUERY 9: Price vs Performance Efficiency Score
-- A single "value score": native PPD indexed vs generation average.
-- Score > 1 = better than generation average; < 1 = worse.
-- Highlights overpriced flagships and underrated mid-range GPUs.
-- ---------------------------------------------------------------
WITH gen_avg AS (
    SELECT
        vendor,
        generation,
        AVG(perf_per_dollar_native) AS gen_avg_ppd_native
    FROM gpu_analysis
    GROUP BY vendor, generation
)
SELECT
    g.vendor,
    g.generation,
    g.gpu_name,
    g.tier,
    ROUND(g.launch_price_2024_adj, 0)                 AS price_2024_usd,
    ROUND(g.perf_per_dollar_native, 4)                AS ppd_native,
    ROUND(g.perf_per_dollar_native / a.gen_avg_ppd_native, 2) AS value_vs_gen_avg,
    CASE
        WHEN g.perf_per_dollar_native / a.gen_avg_ppd_native >= 1.1 THEN 'Great value'
        WHEN g.perf_per_dollar_native / a.gen_avg_ppd_native >= 0.9 THEN 'Fair value'
        ELSE 'Overpriced for generation'
    END                                               AS value_label
FROM gpu_analysis g
JOIN gen_avg a ON g.vendor = a.vendor AND g.generation = a.generation
ORDER BY g.vendor, g.launch_year,
         g.perf_per_dollar_native / a.gen_avg_ppd_native DESC;
