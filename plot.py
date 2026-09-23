import csv
import json
import math
import os

os.makedirs("out", exist_ok=True)

# 1. Parse lunar ephemeris data (defaults to January 2026, 31 days)
csv_path = "data/moon-2026.csv"
month_days_data = {}


def parse_time(t_str):
    if not t_str or ":" not in t_str:
        return None
    try:
        parts = t_str.strip().split(":")
        return int(parts[0]) + int(parts[1]) / 60.0
    except Exception:
        return None


if os.path.exists(csv_path):
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            d_str = r.get("Date") or r.get("DATE") or r.get("日期") or ""
            # Match January records (format: YYYY-01-DD or YYYY/1/DD)
            if "2026-01" in d_str or "2026/1/" in d_str or "/1/" in d_str:
                day_num = int(d_str.replace("-", "/").split("/")[2])
                month_days_data[day_num] = {
                    "rise": parse_time(r.get("RISE")),
                    "trans": parse_time(
                        r.get("TRAN.") or r.get("TRANSIT")
                    ),
                    "set": parse_time(r.get("SET")),
                    "date": d_str,
                }

# Fallback simulation for 31 days if data is unavailable
if not month_days_data:
    for day in range(1, 32):
        t_trans = (13.5 + (day - 1) * (50.47 / 60.0)) % 24.0
        month_days_data[day] = {
            "trans": t_trans,
            "rise": (t_trans - 6.2) % 24.0,
            "set": (t_trans + 6.2) % 24.0,
            "date": f"2026-01-{day:02d}",
        }

# 2. Build 31 days (rows) x 24 hours (columns) visibility matrix (0.0 to 1.0)
DAYS = 31
HOURS = 24
matrix = []

for day in range(1, DAYS + 1):
    row_vals = []
    info = month_days_data.get(day)
    t_trans = info["trans"] if info else None

    for h in range(HOURS):
        if t_trans is None:
            row_vals.append(0.0)
            continue
        dt = abs(h - t_trans)
        if dt > 12:
            dt = 24 - dt
        half_dur = 6.2  # Approximate half-day lunar visibility duration
        if dt <= half_dur:
            val = math.cos((dt / half_dur) * (math.pi / 2))
            row_vals.append(round(max(0.0, val), 3))
        else:
            row_vals.append(0.0)
    matrix.append(row_vals)


# 3. Standard Viridis colormap mapping function (0.0 to 1.0)
def viridis_color(val):
    val = max(0.0, min(1.0, val))
    colors = [
        (68, 1, 84),  # 0.00: Deep purple
        (59, 82, 139),  # 0.25: Indigo blue
        (33, 145, 140),  # 0.50: Teal green
        (94, 201, 98),  # 0.75: Light green
        (253, 231, 37),  # 1.00: Vibrant yellow
    ]
    pos = val * (len(colors) - 1)
    idx = int(pos)
    frac = pos - idx
    if idx >= len(colors) - 1:
        c = colors[-1]
    else:
        c1, c2 = colors[idx], colors[idx + 1]
        c = (
            int(c1[0] + (c2[0] - c1[0]) * frac),
            int(c1[1] + (c2[1] - c1[1]) * frac),
            int(c1[2] + (c2[2] - c1[2]) * frac),
        )
    return f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}"


# 4. Generate static vector SVG
W_TOTAL, H_TOTAL = 680, 560
PAD_L, PAD_T, PAD_R, PAD_B = 65, 55, 100, 55
GRID_W = W_TOTAL - PAD_L - PAD_R
GRID_H = H_TOTAL - PAD_T - PAD_B
CELL_W = GRID_W / HOURS
CELL_H = GRID_H / DAYS

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_TOTAL}" height="{H_TOTAL}" viewBox="0 0 {W_TOTAL} {H_TOTAL}" style="background-color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">'
]
# Titles and axis labels
svg.append(
    f'<text x="{PAD_L + GRID_W/2}" y="32" text-anchor="middle" font-size="15" fill="#111827">the same numbers as colour — one square per hour</text>'
)
svg.append(
    f'<text x="{PAD_L + GRID_W/2}" y="{H_TOTAL - 15}" text-anchor="middle" font-size="13" fill="#374151">hour of the day</text>'
)
svg.append(
    f'<text x="20" y="{PAD_T + GRID_H/2}" text-anchor="middle" font-size="13" fill="#374151" transform="rotate(-90 20 {PAD_T + GRID_H/2})">day of the month</text>'
)

# Render grid cells
svg.append(f'<g transform="translate({PAD_L}, {PAD_T})">')
for r in range(DAYS):
    for c in range(HOURS):
        v = matrix[r][c]
        color = viridis_color(v)
        svg.append(
            f'<rect x="{c * CELL_W:.2f}" y="{r * CELL_H:.2f}" width="{CELL_W:.2f}" height="{CELL_H:.2f}" fill="{color}" stroke="none">'
            f'<title>Day {r+1} | Hour {c+1}:00&#10;Moon Altitude Index: {v:.2f}</title></rect>'
        )

# Grid frame
svg.append(
    f'<rect x="0" y="0" width="{GRID_W}" height="{GRID_H}" fill="none" stroke="#111827" stroke-width="1.2"/>'
)

# X-axis ticks (1, 6, 12, 18, 24)
x_ticks = [(0, "1"), (5, "6"), (11, "12"), (17, "18"), (23, "24")]
for c, txt in x_ticks:
    tx = (c + 0.5) * CELL_W
    svg.append(
        f'<line x1="{tx:.1f}" y1="{GRID_H}" x2="{tx:.1f}" y2="{GRID_H + 5}" stroke="#111827" stroke-width="1"/>'
    )
    svg.append(
        f'<text x="{tx:.1f}" y="{GRID_H + 18}" text-anchor="middle" font-size="11" fill="#111827">{txt}</text>'
    )

# Y-axis ticks (1, 5, 10, 15, 20, 25, 30)
y_ticks = [
    (0, "1"),
    (4, "5"),
    (9, "10"),
    (14, "15"),
    (19, "20"),
    (24, "25"),
    (29, "30"),
]
for r, txt in y_ticks:
    ty = (r + 0.5) * CELL_H
    svg.append(
        f'<line x1="0" y1="{ty:.1f}" x2="-5" y2="{ty:.1f}" stroke="#111827" stroke-width="1"/>'
    )
    svg.append(
        f'<text x="-8" y="{ty + 4:.1f}" text-anchor="end" font-size="11" fill="#111827">{txt}</text>'
    )
svg.append("</g>")

# Vertical Colorbar
CBAR_X = PAD_L + GRID_W + 28
CBAR_W = 18
CBAR_H = GRID_H
svg.append(
    f'<defs><linearGradient id="viridisGrad" x1="0" y1="1" x2="0" y2="0">'
)
for stop, c in [
    ("0%", "#440154"),
    ("25%", "#3b528b"),
    ("50%", "#21918c"),
    ("75%", "#5ec962"),
    ("100%", "#fde725"),
]:
    svg.append(f'<stop offset="{stop}" stop-color="{c}"/>')
svg.append("</linearGradient></defs>")
svg.append(
    f'<rect x="{CBAR_X}" y="{PAD_T}" width="{CBAR_W}" height="{CBAR_H}" fill="url(#viridisGrad)" stroke="#111827" stroke-width="1.2"/>'
)

# Colorbar ticks
cb_ticks = [
    (0.0, "0.00"),
    (0.25, "0.25"),
    (0.5, "0.50"),
    (0.75, "0.75"),
    (1.0, "1.00"),
]
for frac, lbl in cb_ticks:
    cy = PAD_T + (1.0 - frac) * CBAR_H
    svg.append(
        f'<line x1="{CBAR_X + CBAR_W}" y1="{cy:.1f}" x2="{CBAR_X + CBAR_W + 4}" y2="{cy:.1f}" stroke="#111827" stroke-width="1"/>'
    )
    svg.append(
        f'<text x="{CBAR_X + CBAR_W + 7}" y="{cy + 3.5:.1f}" font-size="10" fill="#111827">{lbl}</text>'
    )
svg.append(
    f'<text x="{CBAR_X + 54}" y="{PAD_T + CBAR_H/2}" text-anchor="middle" font-size="12" fill="#374151" transform="rotate(90 {CBAR_X + 54} {PAD_T + CBAR_H/2})">moon altitude / visibility index</text>'
)
svg.append("</svg>")

with open("out/moon_heatmap.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(svg))


# 5. Generate interactive HTML webpage
matrix_json = json.dumps(matrix)
html_str = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lunar Altitude Heatmap</title>
<style>
  body {{
    margin: 0;
    padding: 30px 10px;
    background: #f8fafc;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
  }}
  .card {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 25px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.06);
    position: relative;
  }}
  #hud {{
    font-size: 13px;
    color: #475569;
    margin-bottom: 12px;
    text-align: center;
    min-height: 20px;
  }}
  #hud span {{
    font-weight: 600;
    color: #0f172a;
  }}
</style>
</head>
<body>
<div class="card">
  <div id="hud">Hover cursor over the heatmap cells to inspect precise values</div>
  {"\n".join(svg)}
</div>
<script>
  const matrix = {matrix_json};
  const hud = document.getElementById("hud");
  const rects = document.querySelectorAll("g rect");
  
  rects.forEach((rect, idx) => {{
    const r = Math.floor(idx / 24);
    const c = idx % 24;
    rect.style.cursor = "pointer";
    rect.addEventListener("mouseenter", () => {{
      rect.style.stroke = "#ffffff";
      rect.style.strokeWidth = "1.5px";
      const val = matrix[r][c];
      hud.innerHTML = `Day: <span>Jan ${{r + 1}}</span> &nbsp;|&nbsp; Hour: <span>${{c + 1}}:00</span> &nbsp;|&nbsp; Altitude Index: <span>${{val.toFixed(2)}}</span>`;
    }});
    rect.addEventListener("mouseleave", () => {{
      rect.style.stroke = "none";
    }});
  }});
</script>
</body>
</html>
"""

with open("out/moon_heatmap.html", "w", encoding="utf-8") as f:
    f.write(html_str)

print("Generated successfully:")
print("1. SVG heatmap: out/moon_heatmap.svg")
print("2. HTML interactive page: out/moon_heatmap.html")