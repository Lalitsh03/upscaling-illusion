# Power BI Dashboard — Complete Step-by-Step Guide
## The Upscaling Illusion: GPU Value Analysis 2018–2025

This guide assumes you have never used Power BI before.
Every click is written out. Do not skip steps.

---

## PART 1 — OPEN POWER BI AND START A NEW FILE

1. Click the **Windows Start button** (bottom left of your screen).
2. Type **Power BI Desktop** and press Enter.
3. Power BI opens with a splash screen. Click **X** to close the splash screen.
4. You should now see a blank white canvas that says "Add data to your report."
5. At the very top of the screen you will see a ribbon with tabs: **Home, Insert, Modeling, View, Optimize, Help.**
   You will mostly use **Home** and **Insert** throughout this guide.
6. Go to **File → Save As**.
7. Navigate to `C:\Users\lalit\my-dashboard-project\powerbi\`
8. Name the file: `upscaling_illusion_dashboard`
9. Click **Save**. Do this regularly as you work.

---

## PART 2 — LOAD ALL 5 DATA FILES

You will load 5 CSV files. Do them one at a time, exactly as shown below.

### Load File 1: v1_divergence.csv

1. Click the **Home** tab at the top.
2. Click the button that says **Get data** (it has a little cylinder icon).
3. A dropdown appears. Click **Text/CSV**.
4. A file browser window opens. Navigate to:
   `C:\Users\lalit\my-dashboard-project\data\powerbi\`
5. Click on **v1_divergence.csv** to select it.
6. Click **Open**.
7. A preview window appears showing the first few rows of the file.
   Check that you can see columns named: `vendor`, `generation`, `gen_launch_year`, `metric`, `perf_per_dollar`, `metric_label`, `metric_order`.
   If it looks right, click **Load** (bottom right of the preview window).
8. Wait a few seconds. The file loads.

### Load File 2: v2_price_trend.csv

1. Click **Get data → Text/CSV** again.
2. Select **v2_price_trend.csv** from the same folder.
3. Click **Open**.
4. Check columns: `vendor`, `generation`, `gpu_name`, `launch_year`, `nominal_price`, `real_price_2024`.
5. Click **Load**.

### Load File 3: v3_framegen_breakdown.csv

1. Click **Get data → Text/CSV** again.
2. Select **v3_framegen_breakdown.csv**.
3. Click **Open**.
4. Check columns: `vendor`, `generation`, `gen_launch_year`, `ppd_total`, `layer`, `ppd_value`, `layer_label`, `stack_order`.
5. Click **Load**.

### Load File 4: v4_cpu_gpu_trajectory.csv

1. Click **Get data → Text/CSV** again.
2. Select **v4_cpu_gpu_trajectory.csv**.
3. Click **Open**.
4. Check columns: `vendor`, `component`, `series_label`, `year`, `perf_index_2019_100`.
5. Click **Load**.

### Load File 5: v5_brand_halo.csv

1. Click **Get data → Text/CSV** again.
2. Select **v5_brand_halo.csv**.
3. Click **Open**.
4. Check columns: `year`, `amd_gpu_share`, `amd_cpu_share`, `nvidia_gpu_share`, `intel_cpu_share`, `amd_gpu_minus_cpu_gap`.
5. Click **Load**.

### Verify all 5 files loaded

Look at the right side of the screen. You will see a panel called **Data** (it may show a table icon).
You should see 5 tables listed:
- v1_divergence
- v2_price_trend
- v3_framegen_breakdown
- v4_cpu_gpu_trajectory
- v5_brand_halo

If all 5 are there, you are ready. Save the file now (Ctrl+S).

---

## PART 3 — CREATE A MEASURES TABLE (for DAX formulas)

Power BI stores calculated formulas in a special table. Here is how to create it:

1. Click the **Home** tab.
2. Click **Enter data** (it looks like a small table with a pencil).
3. A small pop-up window appears with one empty column.
4. In the **Name** field at the bottom of the window, delete the default text and type: `_Measures`
5. Click **Load**.
6. You will see `_Measures` appear in the Data panel on the right side.

### Add DAX Measure 1 — Frame Gen Share

This formula calculates what percentage of the total performance gain comes from frame generation (artificial frames).

1. In the **Data** panel on the right, click on **_Measures** to select it.
2. Click the **Home** tab → click **New measure** (it has an fx icon).
3. A formula bar appears at the top of the canvas. Delete whatever is in it.
4. Type the following exactly (you can copy-paste):

```
FrameGen Share % =
DIVIDE(
    CALCULATE(
        SUM(v3_framegen_breakdown[ppd_value]),
        v3_framegen_breakdown[layer] = "ppd_gain_framegen"
    ),
    CALCULATE(
        MAX(v3_framegen_breakdown[ppd_total])
    )
)
```

5. Press **Enter** or click the checkmark (✓) to the left of the formula bar.
6. The measure is saved.

### Add DAX Measure 2 — AMD Gap Label

This creates a readable text label for the brand halo chart.

1. With **_Measures** still selected, click **New measure** again.
2. Delete the existing text and type:

```
AMD Gap Label =
VAR gap = SELECTEDVALUE(v5_brand_halo[amd_gpu_minus_cpu_gap])
RETURN
    IF(
        gap < 0,
        FORMAT(gap, "0.0") & " pts  (GPU lags CPU)",
        FORMAT(gap, "+0.0") & " pts  (GPU leads CPU)"
    )
```

3. Press Enter or click the checkmark.

Save the file (Ctrl+S).

---

## PART 4 — SET UP THE CANVAS AND PAGES

Your dashboard will have 1 main page with 5 visuals. Let us set the canvas size first.

1. Click anywhere on the blank white canvas.
2. On the right side, click the **Format** tab (it looks like a paint roller icon). If you do not see it, look for a panel on the far right with icons — it may be labeled **Visualizations**.
3. In the Format panel, scroll down until you see **Canvas settings** or **Page information**.
4. Under Canvas settings, change the Type to **Custom**.
5. Set Width: **1400** and Height: **900**. Press Enter after each.

### Rename the page

1. At the bottom of the screen, you will see a tab that says **Page 1**.
2. Double-click on **Page 1**.
3. Type: `Dashboard` and press Enter.

---

## PART 5 — ADD THE TITLE

1. Click the **Insert** tab at the top.
2. Click **Text box**.
3. Click on the canvas near the top left and drag to draw a wide rectangle.
4. Type: `The Upscaling Illusion: GPU Value Analysis 2018–2025`
5. Select all the text (Ctrl+A inside the text box).
6. Change the font size to **20** and make it **Bold**.
7. Below that, on a new line, type:
   `Did AI upscaling genuinely improve value — or did it mask stagnant hardware progress?`
8. Select that second line. Change font size to **12**. Make it a lighter grey color (click the font color button and pick a medium grey).
9. Click outside the text box to deselect.

---

## PART 6 — VISUAL 1: THE DIVERGENCE CHART
### "Raw vs Effective Performance Per Dollar — by Generation"

This is your most important chart. It shows the main finding of the entire project.

### Add the visual

1. Click on a blank area of the canvas below the title.
2. In the **Visualizations** panel on the right, click the **Line chart** icon.
   (It looks like a line going up and down. If you hover over the icons, a tooltip appears with the name.)
3. A blank chart placeholder appears on the canvas. Drag the corners to make it wide — roughly the left two-thirds of the canvas, about 400 pixels tall.

### Connect the data

4. In the **Data** panel on the right, expand **v1_divergence** by clicking the arrow next to it.
5. You need to drag fields into the chart. Look at the Visualizations panel — you will see boxes labeled **X-axis, Y-axis, Legend, Small multiples**, etc.
6. Drag **generation** into the **X-axis** box.
7. Drag **perf_per_dollar** into the **Y-axis** box.
8. Drag **metric_label** into the **Legend** box.
9. Drag **vendor** into the **Small multiples** box.

### Fix the X-axis sort order

Right now, the generations on the X-axis might be sorted alphabetically instead of by time. Fix it:

10. Click on the chart to select it.
11. Click the **three dots (...)** that appear in the top right corner of the chart.
12. Click **Sort axis → gen_launch_year → Sort ascending**.

### Format the lines

13. With the chart selected, click the **Format visual** tab in the Visualizations panel (the paint roller icon).
14. Scroll down to find **Lines** or **Data colors**.
15. Change the color for each series:
    - `Raw rasterization (native)` → color `#4472C4` (blue)
    - `Upscaling — no Frame Gen` → color `#ED7D31` (orange)
    - `Upscaling + Frame Gen` → color `#70AD47` (green)

    To enter a custom hex color: click the color swatch → click **Custom color** → type the hex code in the # field.

16. Turn on **Markers**: scroll to find **Markers** toggle and switch it On.
17. Under **Title**, type:
    `The Divergence: Raw vs Effective Performance Per Dollar`
18. Under **Subtitle** (if available), type:
    `Frame Generation (RTX 4000+ / RX 7000+) drives most of the gap`

### Add a text box annotation

19. Click **Insert → Text box**.
20. Draw a small box overlapping the top-right area of the chart.
21. Type:
    `RTX 5000 with Multi Frame Gen shows 2× effective PPD vs raw — but nearly half that gain comes from AI-generated frames, not rendered pixels.`
22. Font size: 9. Text color: dark grey.

---

## PART 7 — VISUAL 2: FLAGSHIP PRICE TREND
### "Have Flagship GPU Prices Actually Gone Up in Real Terms?"

### Add the visual

1. Click a blank area of the canvas — bottom left area, roughly quarter width.
2. Click the **Line chart** icon in the Visualizations panel.
3. Draw it to fill the bottom-left quarter.

### Connect the data (trend line — generation averages only)

4. Expand **v2_price_trend** in the Data panel.
5. Drag **launch_year** → **X-axis**.
6. Drag **real_price_2024** → **Y-axis**.
7. Drag **vendor** → **Legend**.

### Filter to generation averages only

You only want the average line, not individual GPU dots cluttering the chart at this stage.

8. With the chart selected, look at the **Filters** panel on the right (it may be a tab next to Visualizations).
9. Under **Filters on this visual**, drag the **gpu_name** field into the filter box.
10. In the filter, choose **Basic filtering**.
11. Check only **GEN_AVG**. Click **Apply filter**.

### Format

12. Vendor line colors: Nvidia = `#76b900`, AMD = `#ed1c24`, Intel = `#0071c5`.
13. Click the **Y-axis** settings and set the format to **Currency** with 0 decimal places.
14. Under **Title**, type: `Flagship GPU Price — 2024-Adjusted USD`
15. Add a **Constant line** (look in Format panel → Analytics tab → Constant line → Add):
    - Value: `999`
    - Label: `The $999 ceiling`
    - Color: grey, dashed style.

---

## PART 8 — VISUAL 3: FRAME GEN STACKED BAR
### "What Are You Actually Paying For?"

This chart shows that the green/orange improvement in Chart 1 is not all equal — some of it is real, some is artificial frames.

### Add the visual

1. Click a blank area — to the right of Visual 1, upper right area.
2. In Visualizations, click the **Stacked bar chart** icon.
   (It looks like horizontal bars stacked on top of each other.)
3. Draw it to fill the upper-right area of the canvas.

### Connect the data

4. Expand **v3_framegen_breakdown** in the Data panel.
5. Drag **generation** → **X-axis**.
6. Drag **ppd_value** → **Y-axis**.
7. Drag **layer_label** → **Legend**.

### Fix the sort order

8. Click the three dots on the chart → **Sort axis → gen_launch_year → Ascending**.
9. Also sort the stacked segments: click the three dots → **Sort legend → stack_order → Ascending**.

### Add a Vendor slicer so users can filter by company

10. Click a blank area near the top of the canvas (above Visual 3).
11. In Visualizations, click the **Slicer** icon (it looks like a funnel).
12. Drag **vendor** from **v3_framegen_breakdown** into the **Field** box.
13. In the Format panel, change the slicer style to **Tile** (so it shows Nvidia / AMD / Intel as clickable buttons).
14. Resize the slicer to be small and place it neatly above Visual 3.

### Format the colors — this is important

The frame gen segment needs to be red to visually signal "this part is artificial."

15. With the chart selected, go to Format → Data colors.
16. Set colors:
    - `1 Raw performance` → `#4472C4` (blue)
    - `2 Upscaling quality gain` → `#ED7D31` (orange)
    - `3 Frame Gen gain (artificial frames)` → `#C00000` (red)
17. Under **Title**, type: `Effective Performance Per Dollar — What Drives the Gain?`
18. Add a subtitle or text box below saying: `Red = AI-generated frames (not rendered pixels)`

---

## PART 9 — VISUAL 4: CPU VS GPU GROWTH TRAJECTORY
### "Did CPUs Outpace GPUs in Raw Performance Growth?"

### Add the visual

1. Click a blank area — bottom middle section of the canvas.
2. Click the **Line chart** icon.
3. Draw it to fill the bottom middle area.

### Connect the data

4. Expand **v4_cpu_gpu_trajectory** in the Data panel.
5. Drag **year** → **X-axis**.
6. Drag **perf_index_2019_100** → **Y-axis**.
7. Drag **series_label** → **Legend**.

### Format

8. Line colors:
    - `GPU: Nvidia Flagship (1440p raster)` → `#76b900` (green), solid line, thickness 2.5
    - `GPU: AMD Flagship (1440p raster)` → `#C00000` (dark red), solid line, thickness 2.5
    - `CPU: Intel Flagship (single-thread)` → `#0071c5` (blue), **dashed** line, thickness 1.5
    - `CPU: AMD Flagship (single-thread)` → `#FF8C00` (orange), **dashed** line, thickness 1.5

    To make a line dashed: Format → Lines → find the series → change **Line style** to Dashed.

9. Add a **Constant line** at Y = 100:
    - Go to the **Analytics** tab (looks like a magnifying glass) in the Visualizations panel.
    - Click **Constant line → Add**.
    - Value: `100`. Label: `2019 baseline`. Color: grey, dashed.

10. Add another constant line at X = 2022:
    - Click **Constant line → Add** again.
    - Value: `2022`. Label: `Frame Gen era begins`. Color: grey, dashed.

11. Under **Title**, type: `CPU vs GPU Performance Growth — Flagship Tier`
12. Add a text box below the chart:
    `Note: Each series uses its own 2019 baseline = 100. This chart compares growth rates, not absolute performance.`
    Font size: 9, grey text.

---

## PART 10 — VISUAL 5: AMD BRAND HALO
### "Did Ryzen's CPU Dominance Pull AMD's GPU Share Up?"

### Add the visual

1. Click a blank area — bottom right of the canvas.
2. Click the **Line chart** icon.
3. Draw it to fill the bottom-right area.

### Connect the data

4. Expand **v5_brand_halo** in the Data panel.
5. Drag **year** → **X-axis**.
6. Drag **amd_gpu_share** → **Y-axis**.
7. Now drag **amd_cpu_share** into the **Y-axis** box as well (it will add a second line).

### Format

8. Line colors:
    - `amd_gpu_share` → `#C00000` (solid red)
    - `amd_cpu_share` → `#FF8C00` (dashed orange)
9. Under **Title**, type: `AMD Brand Halo — Did Ryzen Pull GPU Share?`
10. Add a text box annotation pointing to the year 2021:
    `AMD CPU share peaked at ~50% in 2021 — but AMD GPU share hit its lowest point (18%). The brand halo did not appear.`
    Font size: 9, dark grey.
11. Add a small text box at the bottom of the chart:
    `Correlation analysis only — causation not claimed.`
    Font size: 8, light grey, italic.

---

## PART 11 — FINAL LAYOUT ARRANGEMENT

Arrange your 5 visuals so the most important one is biggest and in the best position.

**Recommended layout:**

```
┌──────────────────────────────────────────────┬─────────────────────┐
│  Title + subtitle                            │   Vendor Slicer     │
├──────────────────────────────────────────────┤                     │
│                                              │                     │
│   VISUAL 1: The Divergence (LARGEST)         │  VISUAL 3:          │
│   Small multiples: Nvidia | AMD | Intel      │  Stacked Bar        │
│                                              │  Frame Gen          │
│                                              │  Breakdown          │
├───────────────────┬──────────────────────────┴─────────────────────┤
│                   │                                                 │
│  VISUAL 2:        │   VISUAL 4: CPU vs GPU Trajectory               │
│  Price Trend      ├─────────────────────────────────────────────────┤
│                   │   VISUAL 5: AMD Brand Halo                      │
└───────────────────┴─────────────────────────────────────────────────┘
```

**How to resize a visual:**
- Click on it to select it.
- Drag the handles (small squares) on the corners and edges to resize.
- Drag the title bar of the visual to move it.

**How to align visuals neatly:**
- Hold **Ctrl** and click multiple visuals to select them all.
- In the **Format** tab at the top ribbon, click **Align** and choose Left, Top, etc.

---

## PART 12 — SAVE AND EXPORT

1. Press **Ctrl+S** to save the .pbix file.
2. To export as PDF: **File → Export → Export to PDF**.
3. To publish to Power BI Service (online): **Home → Publish**. You will need a Power BI account (free accounts work for personal use).

---

## COMMON PROBLEMS AND FIXES

| Problem | Fix |
|---------|-----|
| X-axis is sorted alphabetically, not by time | Click the three dots on the chart → Sort axis → gen_launch_year → Ascending |
| All lines are the same color | Make sure `metric_label` or `series_label` is in the Legend box, not in Y-axis |
| The stacked bar chart shows one giant bar | Make sure `layer_label` is in Legend, not in X-axis |
| The price chart shows too many zigzag lines | Add a filter on `gpu_name` = "GEN_AVG" for the trend line visual |
| The brand halo chart only shows one line | Make sure you dragged BOTH `amd_gpu_share` AND `amd_cpu_share` into the Y-axis field well |
| A DAX measure shows an error | Check that the table name in the formula exactly matches the table name in the Data panel (case-sensitive) |
| The canvas looks tiny | View → Page view → Fit to page |
| Text box is in front of a chart blocking it | Right-click the text box → Send backward |
