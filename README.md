# The phenomenon

<!-- This is the SD5913 assignment 2 template. Everything in this file is yours to
replace, and the check counts words: comments like this one are not words, so
delete each one as you write. Start with the heading: name the phenomenon.

Then, in this order, at least 150 words in total.

New to folders, paths, or the files here whose names start with a dot? Read
https://github.com/sd5913/pfad/blob/2026/reference/files.md first. Ten minutes. -->

![what the picture is]![what the picture is](out/moon.svg)
> 🌕 **[Explore the Interactive Celestial Chart (Live Demo)](https://qiugeapple.github.io/hk-moon-ring/out/moon_celestial.html)**

## The phenomenon
The time at which the moon rises, reaches its highest point in the sky, and sets drifts later by roughly 50 minutes each day as a consequence of the moon's eastward orbit around Earth. Across 2026, this continuous lag creates rhythmic diagonal waves across the 24-hour cycle. In addition, the moon undergoes an ~29.53-day synodic cycle from New Moon to Full Moon. Because the lunar cycle does not synchronize evenly with Earth's 24-hour solar day, there are occasional calendar days without a recorded moonrise, transit, or moonset, leaving natural gaps in the ephemeris schedule.
<!-- What goes up and down, and why you looked at it. -->

## The source
Data comes from Hong Kong Observatory open‑data API:
[https://data.weather.gov.hk/weatherAPI/opendata/opendata.php?dataType=MRS&year=2026&rformat=json](https://data.weather.gov.hk/weatherAPI/opendata/opendata.php?dataType=MRS&year=2026&rformat=json)
This API returns daily records for the 365 days of 2026. Each row contains the date and three timestamp values: moonrise, lunar transit (culmination altitude), and moonset. Some cells are omitted when an event does not occur on that calendar day.
<!-- A link to the page or endpoint the file came from, and one line on what is in
the file: how many rows, what a row means, what the units are. -->

## What the picture shows
In this enhanced SVG visualization, the horizontal axis spans the 12 calendar months across 2026, while the vertical axis represents a 24-hour diurnal scale from 00:00 to 24:00 against a dark celestial sky backdrop. Luminous points map the daily lunar rhythms in three distinct hues—green for moonrise, golden yellow for lunar transit, and coral red for moonset—alongside translucent starlight markers indicating Full Moon (🌕) and New Moon (🌑) occurrences. Each point embeds an SVG tooltip that displays the exact date and event timestamp on hover.
This visualisation discards the physical azimuth and altitude coordinates of the moon in the sky dome, as well as daylight interference from the sun. Only clock-time values are mapped, transforming physical astronomical coordinates into a purely temporal ribbon of presence and absence.
<!-- Two or three sentences. Including what it hides: every transformation throws
something away, and naming what yours threw away is the easiest way to sound like
you know what you did. -->

## Run it
uv run fetch.py
uv run plot.py