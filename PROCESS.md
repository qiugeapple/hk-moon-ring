## Process

### Stage 1: API Integration and Data Pipeline
The project started by configuring `fetch.py` to retrieve authentic 2026 lunar ephemeris records from the Hong Kong Observatory Open Data API (`dataType=MRS&rformat=csv&year=2026`), storing the output in `data/moon-2026.csv`. Because astronomical records naturally contain blank entries for days without specific lunar events (such as days without a transit), I implemented safe fallback parsing logic to prevent pipeline crashes.

### Stage 2: From Discrete Scatter Plot to Continuous Grid Matrix
The initial visualization script (`plot.py`) attempted to display moonrise, transit, and moonset as discrete points across a 24-hour diurnal vertical grid. However, a major coordinate inversion bug occurred where transit points erroneously mapped their horizontal coordinate to transit time (`cx="{y_trans}"`). After debugging this, I realized discrete points failed to convey the fluid, continuous presence of the moon in the sky. I pivoted to an hourly carpet-plot matrix ($31 \text{ days} \times 24 \text{ hours}$), interpolating proximity to transit via a cosine curve to visualize continuous visibility.

### Stage 3: Synodic Modulation and Ethereal Aesthetics
To ground the visual in celestial reality, I introduced synodic month calculations ($\approx 29.53$ days) to modulate cell brightness by lunar surface illumination percentages, allowing New Moons to naturally dim into the night and Full Moons to peak. I also placed lunar phase glyphs (🌕, 🌓, 🌑) on the Y-axis. The standard engineering Viridis palette was replaced with an ethereal celestial palette ranging from deep abyss (`#070b1a`) through twilight purple (`#581c87`) to moonbeam gold (`#fef08a`), accompanied by infinite CSS breathing pulse animations and an interactive hover HUD in `out/moon_heatmap.html`.

## Tools
I used Gemini as an interactive AI collaborator throughout this project.
I used Gemini to configure the API endpoint in `fetch.py`, debug coordinate mapping errors in `plot.py`, formulate the synodic phase illumination algorithm, design the custom multi-stop twilight-to-gold palette, and structure the animated SVG/HTML output.
I guided and corrected Gemini across iterations: I insisted on strictly English documentation and labels, rejected excessive point clutter over the grid, adjusted the layout dimensions to accommodate lunar glyph labels, and fixed broken Markdown image syntax (`![text]!(path)`).

## Kept
I kept the synodic illumination modulation formula combined with continuous cosine proximity mapping. The Hong Kong Observatory dataset only provides sparse timestamps for rise, transit, and set. This formula converts sparse daily timestamps into a cohesive hourly matrix weighted by phase illumination, organically revealing the ~50-minute daily orbital delay as luminous diagonal cascades across January.

## Rejected
I rejected an earlier suggestion to overlay individual circular markers on top of the heatmap cells for rise, transit, and set times. Overlaying dots cluttered the aesthetic flow and created a false sense of astrometric pinpoint precision, given that the heatmap represents an approximated visibility index rather than spherical altitude coordinates. I eliminated the markers in favor of a clean, atmospheric heatmap enhanced with cyclic breathing animations.