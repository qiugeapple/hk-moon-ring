# Process

<!-- Same as assignment 1, same honesty. Which tools you used and for what; one
thing you kept and why it was good; one thing you rejected and why it was wrong.
"I did not use any" is fine if it is true.

If a model wrote most of plot.py, which is likely and allowed, the interesting part
is what you had to correct: did it invent a column name, use pandas where a list
would do, silently drop the rows it could not parse? -->

## Tools
I used Kimi and Doubao (AI assistants) during this assignment.
I used Kimi to help me organise and understand the raw Hong‑Kong Observatory moon‑rise dataset, sorting out the meaning of each CSV column.
I used Doubao to draft the initial Python plotting code for `plot.py`, including logic for reading the CSV file and generating SVG output.
Throughout the work, I manually inspected the data, fixed bugs in the generated script, and adjusted the output path so that the final SVG file saves into the `out` folder. I also handled empty cells in the dataset, which would otherwise crash the program. The overall design decisions for this visualisation were my own.
## Kept
I kept the core loop structure for iterating over CSV rows and converting time values into vertical SVG coordinates. This section of code was helpful because it provided a solid foundation to map clock times onto the 24‑hour vertical axis, and saved me from writing all of the parsing logic from scratch.
## Rejected
I rejected the AI’s suggestion to add slanted connecting lines between successive moon‑transit points. This idea would imply a continuous curved path of the moon across the sky. However, our dataset only contains discrete daily clock‑time records without angular position data. Drawing those lines would misrepresent the available source data and create unsupported visual information. Therefore I kept the scatter‑only circle rendering.