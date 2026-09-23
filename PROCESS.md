# Process

<!-- Same as assignment 1, same honesty. Which tools you used and for what; one
thing you kept and why it was good; one thing you rejected and why it was wrong.
"I did not use any" is fine if it is true.

If a model wrote most of plot.py, which is likely and allowed, the interesting part
is what you had to correct: did it invent a column name, use pandas where a list
would do, silently drop the rows it could not parse? -->


## Tools
I used Gemini and Doubao (AI assistants) for this assignment.
I used Gemini to help understand and organise Hong‑Kong Observatory moon‑rise CSV dataset fields.
I used Doubao to draft the heat‑map plotting logic, viridis colour‑mapping function, SVG grid layout and interactive HTML hover logic.
I modified the code with gemini : limited data scope to January only, added fallback simulated‑data logic for missing CSV records, fixed parsing for empty CSV cells, and adjusted axis labels, ticks and colour‑bar layout. All core design decisions for this heat‑map visualisation were my own.

## Kept
I kept the matrix‑grid computation logic which calculates moon‑visibility index from rise‑transit‑set timestamps. This block of code was valuable because it turns discrete daily time records into continuous hourly values suitable for heat‑map rendering, which would take much longer for me to write from scratch.

## Rejected
I rejected the initial AI suggestion to draw individual circle markers for rise / transit / set events over top of the heatmap grid, primarily for aesthetic and clarity reasons. Adding overlay circles cluttered the ethereal nocturnal gradient and disrupted the smooth reading of the color grid. From a visual design perspective, the circular markers felt like noisy data artifacts over an otherwise fluid celestial band. Scientifically, since our numbers represent an estimated visibility index rather than true celestial spherical altitude, discrete point markers also gave a misleading impression of pinpoint astronomical precision. I discarded those markers and kept the clean, atmospheric heatmap instead.