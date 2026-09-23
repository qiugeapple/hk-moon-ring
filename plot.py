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

# Fallback simulation if CSV data is missing
if not month_days_data:
    for day in range(1, 32):
        t_trans = (13.5 + (day - 1) * (50.47 / 60.0)) % 24.0
        month_days_data[day] = {
            "trans": t_trans,
            "rise": (t_trans - 6.2) % 24.0,
            "set": (t_trans + 6.2) % 24.0,
            "date": f"2026-01-{day:02d}",
        }

# 2. Build 31 days x 24 hours lunar visibility matrix (0.0 to 1.0)
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
        half_dur = 6.2  # Duration from rise to transit
        if dt <= half_dur:
            val = math.cos((dt / half_dur) * (math.pi / 2))
            row_vals.append(round(max(0.0, val), 3))
        else:
            row_vals.append(0.0)
    matrix.append(row_vals)


# 3. Dreamy Celestial Palette: Deep Abyss -> Indigo Starlight -> Twilight Purple -> Ethereal Rose -> Moonlight Gold
def dreamy_moon_color(val):
    val = max(0.0, min(1.0, val))
    palette = [
        (7, 11, 26),  # 0.00: Deep void / night sky
        (30, 27, 75),  # 0.20: Midnight indigo
        (88, 28, 135),  # 0.45: Celestial amethyst / twilight
        (192, 38, 211),  # 0.70: Ethereal nebula magenta
        (244, 114, 182),  # 0.88: Lunar halo rose
        (254, 240, 138),  # 1.00: Luminous moonbeam gold
    ]
    pos = val * (len(palette) - 1)
    idx = int(pos)
    frac = pos - idx
    if idx >= len(palette) - 1:
        c = palette[-1]
    else:
        c1, c2 = palette[idx], palette[idx + 1]
        c = (
            int(c1[0] + (c2[0] - c1[0]) * frac),
            int(c1[1] + (c2[1] - c1[1]) * frac),
            int(c1[2] + (c2[2] - c1[2]) * frac),
        )
    return f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}"


# 4. Generate SVG Chart
W_TOTAL, H_TOTAL = 740, 600
PAD_L, PAD_T, PAD_R, PAD_B = 70, 65, 120, 60
GRID_W = W_TOTAL - PAD_L - PAD_R
GRID_H = H_TOTAL - PAD_T - PAD_B
CELL_W = GRID_W / HOURS
CELL_H = GRID_H / DAYS

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_TOTAL}" height="{H_TOTAL}" viewBox="0 0 {W_TOTAL} {H_TOTAL}" style="background-color: #050814; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;">'
]

# Dreamy Gradients & Glow Filters
svg.append("""<defs>
  <linearGradient id="dreamyGrad" x1="0" y1="1" x2="0" y2="0">
    <stop offset="0%" stop-color="#070b1a"/>
    <stop offset="20%" stop-color="#1e1b4b"/>
    <stop offset="45%" stop-color="#581c87"/>
    <stop offset="70%" stop-color="#c026d3"/>
    <stop offset="88%" stop-color="#f472b6"/>
    <stop offset="100%" stop-color="#fef08a"/>
  </linearGradient>
  <filter id="moonGlow" x="-20%" y="-20%" width="140%" height="140%">
    <feGaussianBlur stdDeviation="3" result="blur"/>
    <feComposite in="SourceGraphic" in2="blur" operator="over"/>
  </filter>
</defs>""")

# Headers
svg.append(
    f'<text x="{PAD_L + GRID_W/2}" y="32" text-anchor="middle" font-size="16" font-weight="600" fill="#f8fafc" letter-spacing="1">the same numbers as colour — one square per hour</text>'
)
svg.append(
    f'<text x="{PAD_L + GRID_W/2}" y="50" text-anchor="middle" font-size="11" fill="#94a3b8" letter-spacing="0.5">JANUARY 2026 · CELESTIAL MOONBEAM &amp; DIURNAL RHYTHM</text>'
)

# Axis Titles
svg.append(
    f'<text x="{PAD_L + GRID_W/2}" y="{H_TOTAL - 15}" text-anchor="middle" font-size="12" fill="#94a3b8">hour of the day</text>'
)
svg.append(
    f'<text x="22" y="{PAD_T + GRID_H/2}" text-anchor="middle" font-size="12" fill="#94a3b8" transform="rotate(-90 22 {PAD_T + GRID_H/2})">day of the month</text>'
)

# Grid Frame & Cells
svg.append(f'<g transform="translate({PAD_L}, {PAD_T})">')
for r in range(DAYS):
    for c in range(HOURS):
        v = matrix[r][c]
        color = dreamy_moon_color(v)
        # Subtle cell border for starlight grid feel
        svg.append(
            f'<rect x="{c * CELL_W:.2f}" y="{r * CELL_H:.2f}" width="{CELL_W:.2f}" height="{CELL_H:.2f}" fill="{color}" stroke="rgba(255,255,255,0.03)" stroke-width="0.5">'
            f'<title>Day {r+1} | Hour {c+1:02d}:00&#10;Moon Altitude Index: {v:.2f}</title></rect>'
        )

# Outer Frame
svg.append(
    f'<rect x="0" y="0" width="{GRID_W}" height="{GRID_H}" fill="none" stroke="rgba(255,255,255,0.18)" stroke-width="1.2"/>'
)

# X-axis ticks (1, 6, 12, 18, 24)
x_ticks = [(0, "1"), (5, "6"), (11, "12"), (17, "18"), (23, "24")]
for c, txt in x_ticks:
    tx = (c + 0.5) * CELL_W
    svg.append(
        f'<line x1="{tx:.1f}" y1="{GRID_H}" x2="{tx:.1f}" y2="{GRID_H + 5}" stroke="rgba(255,255,255,0.3)" stroke-width="1"/>'
    )
    svg.append(
        f'<text x="{tx:.1f}" y="{GRID_H + 20}" text-anchor="middle" font-size="11" fill="#94a3b8">{txt}</text>'
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
        f'<line x1="0" y1="{ty:.1f}" x2="-5" y2="{ty:.1f}" stroke="rgba(255,255,255,0.3)" stroke-width="1"/>'
    )
    svg.append(
        f'<text x="-9" y="{ty + 4:.1f}" text-anchor="end" font-size="11" fill="#94a3b8">{txt}</text>'
    )
svg.append("</g>")

# Dreamy Colorbar
CBAR_X = PAD_L + GRID_W + 32
CBAR_W = 16
CBAR_H = GRID_H
svg.append(
    f'<rect x="{CBAR_X}" y="{PAD_T}" width="{CBAR_W}" height="{CBAR_H}" rx="3" fill="url(#dreamyGrad)" stroke="rgba(255,255,255,0.2)" stroke-width="1"/>'
)

# Colorbar Ticks and Labels
cb_ticks = [
    (0.0, "0.00 (Sub-horizon)"),
    (0.25, "0.25 (Rising/Setting)"),
    (0.5, "0.50 (Mid Altitude)"),
    (0.75, "0.75 (High Sky)"),
    (1.0, "1.00 (Zenith Peak)"),
]
for frac, lbl in cb_ticks:
    cy = PAD_T + (1.0 - frac) * CBAR_H
    svg.append(
        f'<line x1="{CBAR_X + CBAR_W}" y1="{cy:.1f}" x2="{CBAR_X + CBAR_W + 5}" y2="{cy:.1f}" stroke="rgba(255,255,255,0.4)" stroke-width="1"/>'
    )
    svg.append(
        f'<text x="{CBAR_X + CBAR_W + 8}" y="{cy + 3.5:.1f}" font-size="10" fill="#94a3b8">{lbl}</text>'
    )

svg.append(
    f'<text x="{CBAR_X + 90}" y="{PAD_T + CBAR_H/2}" text-anchor="middle" font-size="11" fill="#94a3b8" letter-spacing="0.5" transform="rotate(90 {CBAR_X + 90} {PAD_T + CBAR_H/2})">lunar elevation index</text>'
)
svg.append("</svg>")

with open("out/moon_heatmap.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(svg))


# 5. Generate Dreamy Animated Interactive Webpage
matrix_json = json.dumps(matrix)
html_str = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ethereal Lunar Heatmap · 2026</title>
<style>
  body {{
    margin: 0;
    padding: 30px 15px;
    background: radial-gradient(circle at 50% 15%, #1e1b4b 0%, #050814 60%, #02040a 100%);
    color: #f8fafc;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    min-height: 100vh;
  }}
  .card {{
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 20px;
    padding: 24px;
    box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.9), 0 0 40px rgba(192, 38, 211, 0.15);
    backdrop-filter: blur(16px);
  }}
  #hud {{
    font-size: 13px;
    color: #cbd5e1;
    margin-bottom: 14px;
    text-align: center;
    letter-spacing: 0.5px;
    display: flex;
    justify-content: center;
    gap: 16px;
    min-height: 24px;
  }}
  .badge {{
    padding: 2px 10px;
    border-radius: 9999px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }}
  .highlight {{
    color: #fde047;
    font-weight: 600;
  }}
</style>
</head>
<body>
<div class="card">
  <div id="hud">
    <div class="badge">Hover cursor across the starlight grid to inspect coordinates</div>
  </div>
  {"\n".join(svg)}
</div>
<script>
  const matrix = {matrix_json};
  const hud = document.getElementById("hud");
  const rects = document.querySelectorAll("g rect:not([fill='none'])");
  
  rects.forEach((rect, idx) => {{
    const r = Math.floor(idx / 24);
    const c = idx % 24;
    rect.style.cursor = "pointer";
    rect.style.transition = "transform 0.1s ease, filter 0.1s ease";
    
    rect.addEventListener("mouseenter", () => {{
      rect.style.stroke = "#fef08a";
      rect.style.strokeWidth = "1.5px";
      rect.style.filter = "drop-shadow(0 0 6px #ec4899)";
      const val = matrix[r][c];
      
      let state = "Below Horizon (Night/Day)";
      if (val > 0.8) state = "🌕 Zenith Moonlight (Culmination)";
      else if (val > 0.4) state = "🌔 High Sky Glow";
      else if (val > 0.05) state = "🌘 Horizon Rise/Set Phase";
      
      hud.innerHTML = `
        <div class="badge">Date: <span class="highlight">Jan ${{r + 1}}</span></div>
        <div class="badge">Time: <span class="highlight">${{String(c + 1).padStart(2, '0')}}:00</span></div>
        <div class="badge">Elevation Index: <span class="highlight">${{val.toFixed(2)}}</span></div>
        <div class="badge">${{state}}</div>
      `;
    }});
    rect.addEventListener("mouseleave", () => {{
      rect.style.stroke = "rgba(255,255,255,0.03)";
      rect.style.strokeWidth = "0.5px";
      rect.style.filter = "none";
    }});
  }});
</script>
</body>
</html>
"""

with open("out/moon_heatmap.html", "w", encoding="utf-8") as f:
    f.write(html_str)

print("Generated ethereal celestial heatmap successfully:")
print("1. SVG vector: out/moon_heatmap.svg")
print("2. Live HTML:   out/moon_heatmap.html")