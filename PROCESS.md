# Process

<!-- Same as assignment 1, same honesty. Which tools you used and for what; one
thing you kept and why it was good; one thing you rejected and why it was wrong.
"I did not use any" is fine if it is true.

If a model wrote most of plot.py, which is likely and allowed, the interesting part
is what you had to correct: did it invent a column name, use pandas where a list
would do, silently drop the rows it could not parse? -->

## Process
I began by fetching the 2026 lunar ephemeris dataset from the Hong Kong Observatory open-data API using `fetch.py` to observe the cyclical rhythms of moonrise, culmination, and moonset across the year. 

After using Gemini to decipher the columns and Doubao to generate a preliminary plotting script, I encountered several practical challenges: the script had a critical coordinate bug on transit points, lacked handling for blank cells when transits did not occur on a given day, and rendered points floating in an empty space without any time or calendar references. 

To resolve these issues, I inspected and cleaned the data, corrected the coordinate calculations, and built a structured astronomical layout around the points—adding a 24-hour diurnal vertical scale and a 12-month calendar timeline against a dark celestial sky. I also layered the 29.53-day synodic lunar cycle into the visualization, introducing subtle vertical light columns for Full Moons and markers for New Moons. Finally, to keep the chart interactive while preserving the scatter-only design and ensuring direct rendering on GitHub without external dependencies, I embedded native SVG `<title>` tooltips into each data point so viewers can hover over any moment to inspect exact dates, moon phases, and times.

## Tools
I used Gemini and Doubao (AI assistants) during this assignment.
I used Gemini to help me organise and understand the raw Hong‑Kong Observatory moon‑rise dataset, sorting out the meaning of each CSV column.
I used Doubao to draft the initial Python plotting code for `plot.py`, including logic for reading the CSV file and generating SVG output.
Throughout the work, I manually inspected the data, fixed bugs in the generated script, and adjusted the output path so that the final SVG file saves into the `out` folder. I also handled empty cells in the dataset, which would otherwise crash the program. The overall design decisions for this visualisation were my own.

## Kept
I kept the core loop structure for iterating over CSV rows and converting time values into vertical SVG coordinates. This section of code was helpful because it provided a solid foundation to map clock times onto the 24‑hour vertical axis, and saved me from writing all of the parsing logic from scratch.

## Rejected
I rejected the AI’s suggestion to add slanted connecting lines between successive moon‑transit points. This idea would imply a continuous curved path of the moon across the sky. However, our dataset only contains discrete daily clock‑time records without angular position data. Drawing those lines would misrepresent the available source data and create unsupported visual information. Therefore I kept the scatter‑only circle rendering.