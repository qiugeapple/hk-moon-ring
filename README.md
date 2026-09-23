# The phenomenon

<!-- This is the SD5913 assignment 2 template. Everything in this file is yours to
replace, and the check counts words: comments like this one are not words, so
delete each one as you write. Start with the heading: name the phenomenon.

Then, in this order, at least 150 words in total.

New to folders, paths, or the files here whose names start with a dot? Read
https://github.com/sd5913/pfad/blob/2026/reference/files.md first. Ten minutes. -->

![what the picture is]!(out/moon_heatmap.svg)


## The phenomenon
The visible time window of the moon changes day‑by‑day across each month. The moon rises, reaches its highest point in the sky, and sets at different clock times every calendar day. Based on Hong‑Kong Observatory monthly moon‑rise/moon‑transit/moon‑set records, this visualisation estimates a moon‑visibility index for every hour in January 2026. Brighter colours represent hours when the moon is more likely to be visible in the sky.
<!-- What goes up and down, and why you looked at it. -->

## The source
Data comes from Hong Kong Observatory open‑data API:
https://data.weather.gov.hk/weatherAPI/opendata/opendata.php?dataType=MRS&year=2026&rformat=csv
The source CSV file contains one row per calendar day of 2026. Each row stores moon‑rise, lunar‑transit and moon‑set clock‑time strings. Some cells are blank for missing transit records. This script filters and uses only January (31 days) data. If real CSV data cannot be loaded, the program falls back to synthetic simulated lunar time data.

## What the picture shows
This heatmap uses rows for days in January and columns for each hour of day‑time. Cell colour shows an estimated lunar‑visibility index ranging 0.0‑1.0, using the viridis colour palette. You can open `out/moon_heatmap.html` in a web browser to hover over each cell and read exact index values.
This visualisation discards real celestial altitude and azimuth measurements. The visibility number is a mathematical approximation calculated only from rise‑transit‑set clock‑time. Blank/missing transit entries trigger fallback simulated data rather than leaving gaps in the grid.

## Run it
uv run fetch.py
uv run plot.py