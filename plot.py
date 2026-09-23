import csv
import json
import math
import os
from datetime import datetime, timedelta

os.makedirs("out", exist_ok=True)

# 1. Parse full year 2026 lunar ephemeris data (365 days)
csv_path = "data/moon-2026.csv"
year_data = {}


def parse_time(t_str):
    if not t_str or ":" not in t_str:
        return None
    try:
        parts = t_str.strip().split(":")
        return int(parts[0]) + int(parts[1]) / 60.0
    except Exception:
        return None


# Build complete 365-day calendar mapping for 2026
start_date = datetime(2026, 1, 1)
total_days = 365

# Load CSV if available
if os.path.exists(csv_path):
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            d_str = r.get("Date") or r.get("DATE") or r.get("日期") or ""
            d_clean = d_str.strip().replace("-", "/").replace(".", "/")
            parts = d_clean.split("/")
            if len(parts) >= 3:
                try:
                    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                    dt = datetime(y, m, d)
                    day_of_year = (dt - start_date).days
                    if 0 <= day_of_year < total_days:
                        year_data[day_of_year] = {
                            "rise": parse_time(r.get("RISE")),
                            "trans": parse_time(
                                r.get("TRAN.") or r.get("TRANSIT")
                            ),
                            "set": parse_time(r.get("SET")),
                            "rise_raw": r.get("RISE", "--:--"),
                            "trans_raw": (
                                r.get("TRAN.", "")
                                or r.get("TRANSIT", "--:--")
                            ),
                            "set_raw": r.get("SET", "--:--"),
                            "date": dt.strftime("%b %d, %Y"),
                            "day_str": dt.strftime("%b %d"),
                        }
                except Exception:
                    pass

# 2. Synodic Lunar Phase calculation (~29.53059 days)
# 2026 First New Moon: ~Jan 18.9
SYNODIC_MONTH = 29.530588
NEW_MOON_REF = 18.0


def get_phase_meta(day_idx):
    moon_age = (day_idx - NEW_MOON_REF) % SYNODIC_MONTH
    phase_frac = moon_age / SYNODIC_MONTH
    illum = (1 - math.cos(phase_frac * 2 * math.pi)) / 2 * 100

    if moon_age < 1.5 or moon_age > 28:
        name, icon = "New Moon", "🌑"
    elif moon_age < 6.5:
        name, icon = "Waxing Crescent", "🌒"
    elif moon_age < 8.5:
        name, icon = "First Quarter", "🌓"
    elif moon_age < 13.5:
        name, icon = "Waxing Gibbous", "🌔"
    elif moon_age < 16.0:
        name, icon = "Full Moon", "🌕"
    elif moon_age < 21.0:
        name, icon = "Waning Gibbous", "🌖"
    elif moon_age < 23.0:
        name, icon = "Last Quarter", "🌗"
    else:
        name, icon = "Waning Crescent", "🌘"

    return {
        "age": round(moon_age, 1),
        "illum": round(illum, 1),
        "name": name,
        "icon": icon,
    }


# 3. Build Full 365 Days x 24 Hours Matrix
HOURS = 24
full_matrix = []
full_days_meta = []

for day_idx in range(total_days):
    curr_dt = start_date + timedelta(days=day_idx)
    phase = get_phase_meta(day_idx)

    info = year_data.get(day_idx)
    if not info:
        # Fallback physics calculation for transit (shifts ~50.47 min per day)
        t_trans = (13.5 + day_idx * (50.47 / 60.0)) % 24.0
        info = {
            "trans": t_trans,
            "rise": (t_trans - 6.2) % 24.0,
            "set": (t_trans + 6.2) % 24.0,
            "rise_raw": f"{(t_trans - 6.2) % 24.0:04.1f}",
            "trans_raw": f"{t_trans:04.1f}",
            "set_raw": f"{(t_trans + 6.2) % 24.0:04.1f}",
            "date": curr_dt.strftime("%b %d, %Y"),
            "day_str": curr_dt.strftime("%b %d"),
        }

    meta_entry = {
        "day_idx": day_idx,
        "date": info["date"],
        "day_str": info["day_str"],
        "month": curr_dt.strftime("%B"),
        "phase_name": phase["name"],
        "phase_icon": phase["icon"],
        "illum": phase["illum"],
        "rise_raw": info["rise_raw"],
        "trans_raw": info["trans_raw"],
        "set_raw": info["set_raw"],
    }
    full_days_meta.append(meta_entry)

    # Compute hourly values
    t_trans = info["trans"]
    row_vals = []
    lum_factor = 0.08 + 0.92 * (phase["illum"] / 100.0)

    for h in range(HOURS):
        if t_trans is None:
            row_vals.append(0.0)
            continue
        dt = abs(h - t_trans)
        if dt > 12:
            dt = 24 - dt
        half_dur = 6.2
        if dt <= half_dur:
            altitude_geom = math.cos((dt / half_dur) * (math.pi / 2))
            combined_val = altitude_geom * lum_factor
            row_vals.append(round(max(0.0, combined_val), 3))
        else:
            row_vals.append(0.0)
    full_matrix.append(row_vals)


# 4. Color Palette
def dreamy_moon_color(val):
    val = max(0.0, min(1.0, val))
    palette = [
        (7, 11, 26),  # 0.00: Deep void night
        (30, 27, 75),  # 0.20: Midnight indigo
        (88, 28, 135),  # 0.45: Twilight purple
        (192, 38, 211),  # 0.70: Nebula magenta
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


# 5. Generate Default 30-Day SVG Snapshot (for README embedding)
W_TOTAL, H_TOTAL = 780, 620
PAD_L, PAD_T, PAD_R, PAD_B = 105, 65, 125, 60
GRID_W = W_TOTAL - PAD_L - PAD_R
GRID_H = H_TOTAL - PAD_T - PAD_B
PREVIEW_DAYS = 31
CELL_W = GRID_W / HOURS
CELL_H = GRID_H / PREVIEW_DAYS

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_TOTAL}" height="{H_TOTAL}" viewBox="0 0 {W_TOTAL} {H_TOTAL}" style="background-color: #050814; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;">'
]
svg.append("""<defs>
  <linearGradient id="dreamyGrad" x1="0" y1="1" x2="0" y2="0">
    <stop offset="0%" stop-color="#070b1a"/>
    <stop offset="20%" stop-color="#1e1b4b"/>
    <stop offset="45%" stop-color="#581c87"/>
    <stop offset="70%" stop-color="#c026d3"/>
    <stop offset="88%" stop-color="#f472b6"/>
    <stop offset="100%" stop-color="#fef08a"/>
  </linearGradient>
</defs>""")
svg.append(
    f'<text x="{PAD_L + GRID_W/2}" y="32" text-anchor="middle" font-size="16" font-weight="600" fill="#f8fafc" letter-spacing="1">the same numbers as colour — one square per hour</text>'
)
svg.append(
    f'<text x="{PAD_L + GRID_W/2}" y="50" text-anchor="middle" font-size="11" fill="#94a3b8" letter-spacing="0.5">JANUARY 2026 · CELESTIAL MOONBEAM WATERFALL</text>'
)
svg.append(
    f'<text x="{PAD_L + GRID_W/2}" y="{H_TOTAL - 15}" text-anchor="middle" font-size="12" fill="#94a3b8">hour of the day</text>'
)
svg.append(
    f'<text x="22" y="{PAD_T + GRID_H/2}" text-anchor="middle" font-size="12" fill="#94a3b8" transform="rotate(-90 22 {PAD_T + GRID_H/2})">day of the month</text>'
)

svg.append(f'<g transform="translate({PAD_L}, {PAD_T})">')
for r in range(PREVIEW_DAYS):
    for c in range(HOURS):
        v = full_matrix[r][c]
        color = dreamy_moon_color(v)
        p = full_days_meta[r]
        svg.append(
            f'<rect x="{c * CELL_W:.2f}" y="{r * CELL_H:.2f}" width="{CELL_W:.2f}" height="{CELL_H:.2f}" fill="{color}" stroke="rgba(255,255,255,0.03)" stroke-width="0.5"/>'
        )

svg.append(
    f'<rect x="0" y="0" width="{GRID_W}" height="{GRID_H}" fill="none" stroke="rgba(255,255,255,0.18)" stroke-width="1.2"/>'
)

# X-axis ticks
x_ticks = [(0, "1"), (5, "6"), (11, "12"), (17, "18"), (23, "24")]
for c, txt in x_ticks:
    tx = (c + 0.5) * CELL_W
    svg.append(
        f'<line x1="{tx:.1f}" y1="{GRID_H}" x2="{tx:.1f}" y2="{GRID_H + 5}" stroke="rgba(255,255,255,0.3)" stroke-width="1"/>'
    )
    svg.append(
        f'<text x="{tx:.1f}" y="{GRID_H + 20}" text-anchor="middle" font-size="11" fill="#94a3b8">{txt}</text>'
    )

# Y-axis ticks
for r in [0, 4, 9, 14, 19, 24, 29]:
    ty = (r + 0.5) * CELL_H
    p = full_days_meta[r]
    svg.append(
        f'<line x1="0" y1="{ty:.1f}" x2="-5" y2="{ty:.1f}" stroke="rgba(255,255,255,0.3)" stroke-width="1"/>'
    )
    svg.append(
        f'<text x="-8" y="{ty + 4:.1f}" text-anchor="end" font-size="11" fill="#94a3b8">{r+1}</text>'
    )
    svg.append(
        f'<text x="-25" y="{ty + 4:.1f}" text-anchor="end" font-size="11">{p["phase_icon"]}</text>'
    )
svg.append("</g>")

# Colorbar
CBAR_X = PAD_L + GRID_W + 34
CBAR_W = 16
CBAR_H = GRID_H
svg.append(
    f'<rect x="{CBAR_X}" y="{PAD_T}" width="{CBAR_W}" height="{CBAR_H}" rx="3" fill="url(#dreamyGrad)" stroke="rgba(255,255,255,0.2)" stroke-width="1"/>'
)
for frac, lbl in [
    (0.0, "0.00 (Dark / Void)"),
    (0.25, "0.25 (Crescent / Low)"),
    (0.5, "0.50 (Quarter Moon)"),
    (0.75, "0.75 (Gibbous Glow)"),
    (1.0, "1.00 (Full Moon Zenith)"),
]:
    cy = PAD_T + (1.0 - frac) * CBAR_H
    svg.append(
        f'<line x1="{CBAR_X + CBAR_W}" y1="{cy:.1f}" x2="{CBAR_X + CBAR_W + 5}" y2="{cy:.1f}" stroke="rgba(255,255,255,0.4)" stroke-width="1"/>'
    )
    svg.append(
        f'<text x="{CBAR_X + CBAR_W + 8}" y="{cy + 3.5:.1f}" font-size="10" fill="#94a3b8">{lbl}</text>'
    )
svg.append(
    f'<text x="{CBAR_X + 96}" y="{PAD_T + CBAR_H/2}" text-anchor="middle" font-size="11" fill="#94a3b8" letter-spacing="0.5" transform="rotate(90 {CBAR_X + 96} {PAD_T + CBAR_H/2})">lunar luminance index</text>'
)
svg.append("</svg>")

with open("out/moon_heatmap.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(svg))


# 6. Interactive HTML Webpage with Time-Scrubbing Axis Slider
full_matrix_json = json.dumps(full_matrix)
full_meta_json = json.dumps(full_days_meta)

html_str = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2026 Celestial Moonbeam Carpet · Year-Round Scrubber</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    padding: 24px 16px;
    background: radial-gradient(circle at 50% 12%, #1e1b4b 0%, #050814 60%, #02040a 100%);
    color: #f8fafc;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    min-height: 100vh;
  }}
  .card {{
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 24px;
    padding: 24px;
    box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.9), 0 0 50px rgba(192, 38, 211, 0.18);
    backdrop-filter: blur(16px);
    max-width: 900px;
    width: 100%;
  }}
  #hud {{
    font-size: 13px;
    color: #cbd5e1;
    margin-bottom: 16px;
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 10px;
    min-height: 32px;
  }}
  .badge {{
    padding: 4px 12px;
    border-radius: 9999px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
  }}
  .highlight {{
    color: #fde047;
    font-weight: 600;
  }}
  
  /* Timeline Scrubber Axis Panel */
  .slider-panel {{
    margin: 18px 0 10px 0;
    padding: 16px 20px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
  }}
  .slider-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    font-size: 13px;
  }}
  .slider-title {{
    font-weight: 600;
    color: #fef08a;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .range-container {{
    position: relative;
    width: 100%;
  }}
  input[type="range"] {{
    -webkit-appearance: none;
    width: 100%;
    height: 8px;
    border-radius: 5px;
    background: linear-gradient(to right, #3b82f6, #ec4899, #fde047, #3b82f6);
    outline: none;
    cursor: pointer;
  }}
  input[type="range"]::-webkit-slider-thumb {{
    -webkit-appearance: none;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: #ffffff;
    border: 2px solid #ec4899;
    box-shadow: 0 0 12px #f472b6;
    cursor: grab;
    transition: transform 0.1s;
  }}
  input[type="range"]::-webkit-slider-thumb:active {{
    cursor: grabbing;
    transform: scale(1.2);
  }}
  .month-labels {{
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: #94a3b8;
    margin-top: 6px;
  }}
  .view-presets {{
    display: flex;
    gap: 8px;
    margin-top: 12px;
    justify-content: center;
  }}
  .btn-chip {{
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #cbd5e1;
    border-radius: 8px;
    padding: 4px 12px;
    font-size: 11px;
    cursor: pointer;
    transition: all 0.15s;
  }}
  .btn-chip.active, .btn-chip:hover {{
    background: #ec4899;
    color: #ffffff;
    border-color: #f472b6;
  }}
  
  canvas {{
    display: block;
    width: 100%;
    height: auto;
    border-radius: 8px;
    cursor: crosshair;
  }}
</style>
</head>
<body>

<div class="card">
  <div id="hud">
    <div class="badge">✨ Drag the Time Axis below to navigate 2026 lunar waterfalls</div>
  </div>

  <!-- Canvas for dynamic rendering of 365-day waterfall -->
  <div style="position: relative; width: 100%;">
    <canvas id="heatmapCanvas" width="820" height="520"></canvas>
  </div>

  <!-- Time Axis Scrubber -->
  <div class="slider-panel">
    <div class="slider-header">
      <div class="slider-title">
        <span>⏱ Celestial Date Axis (Day 1 - 365)</span>
      </div>
      <div id="windowRangeLabel" style="color: #94a3b8; font-size: 12px;">Jan 01 - Jan 31 (31 Days)</div>
    </div>
    
    <div class="range-container">
      <input type="range" id="timeSlider" min="0" max="335" value="0" step="1"/>
    </div>
    
    <div class="month-labels">
      <span>Jan</span><span>Feb</span><span>Mar</span><span>Apr</span><span>May</span><span>Jun</span>
      <span>Jul</span><span>Aug</span><span>Sep</span><span>Oct</span><span>Nov</span><span>Dec</span>
    </div>

    <div class="view-presets">
      <button class="btn-chip active" data-span="30">Monthly View (30d)</button>
      <button class="btn-chip" data-span="60">Bimonthly (60d)</button>
      <button class="btn-chip" data-span="90">Seasonal (90d)</button>
      <button class="btn-chip" data-span="365">Full Year (365d)</button>
    </div>
  </div>
</div>

<script>
  const fullMatrix = {full_matrix_json};
  const fullMeta = {full_meta_json};
  const TOTAL_DAYS = 365;
  const HOURS = 24;

  const canvas = document.getElementById("heatmapCanvas");
  const ctx = canvas.getContext("2d");
  const slider = document.getElementById("timeSlider");
  const hud = document.getElementById("hud");
  const rangeLabel = document.getElementById("windowRangeLabel");
  const presetBtns = document.querySelectorAll(".btn-chip");

  let startDay = 0;
  let viewSpan = 30; // Number of days displayed at once

  // Color mapping function in JS
  function getColor(v) {{
    v = Math.max(0, Math.min(1, v));
    const palette = [
      [7, 11, 26],     // 0.00
      [30, 27, 75],    // 0.20
      [88, 28, 135],   // 0.45
      [192, 38, 211],  // 0.70
      [244, 114, 182], // 0.88
      [254, 240, 138]  // 1.00
    ];
    const pos = v * (palette.length - 1);
    const idx = Math.floor(pos);
    const frac = pos - idx;
    if (idx >= palette.length - 1) return `rgb(${{palette[palette.length - 1].join(',')}})`;
    const c1 = palette[idx], c2 = palette[idx + 1];
    const r = Math.round(c1[0] + (c2[0] - c1[0]) * frac);
    const g = Math.round(c1[1] + (c2[1] - c1[1]) * frac);
    const b = Math.round(c1[2] + (c2[2] - c1[2]) * frac);
    return `rgb(${{r}},${{g}},${{b}})`;
  }}

  // Draw Heatmap Canvas
  function draw() {{
    const W = canvas.width;
    const H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    const padL = 90, padT = 50, padR = 100, padB = 40;
    const gridW = W - padL - padR;
    const gridH = H - padT - padB;

    const actualSpan = Math.min(viewSpan, TOTAL_DAYS - startDay);
    const cellW = gridW / HOURS;
    const cellH = gridH / actualSpan;

    // Header Title
    ctx.fillStyle = "#f8fafc";
    ctx.font = "600 14px -apple-system, BlinkMacSystemFont, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("the same numbers as colour — one square per hour", padL + gridW / 2, 25);

    ctx.fillStyle = "#94a3b8";
    ctx.font = "11px -apple-system, BlinkMacSystemFont, sans-serif";
    ctx.fillText(`2026 CELESTIAL MOONBEAM WATERFALL · WINDOW: DAY ${{startDay + 1}} TO ${{startDay + actualSpan}}`, padL + gridW / 2, 40);

    // Axis Labels
    ctx.fillText("hour of the day", padL + gridW / 2, H - 12);
    ctx.save();
    ctx.translate(22, padT + gridH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText("calendar timeline", 0, 0);
    ctx.restore();

    // Draw Heatmap Cells
    for (let r = 0; r < actualSpan; r++) {{
      const dayIdx = startDay + r;
      for (let c = 0; c < HOURS; c++) {{
        const v = fullMatrix[dayIdx][c];
        ctx.fillStyle = getColor(v);
        ctx.fillRect(padL + c * cellW, padT + r * cellH, cellW - 0.5, cellH - 0.5);
      }}
    }}

    // Grid Outer Border
    ctx.strokeStyle = "rgba(255, 255, 255, 0.2)";
    ctx.lineWidth = 1;
    ctx.strokeRect(padL, padT, gridW, gridH);

    // X-Axis Ticks
    const xTicks = [1, 6, 12, 18, 24];
    ctx.fillStyle = "#94a3b8";
    ctx.font = "10px sans-serif";
    xTicks.forEach(h => {{
      const tx = padL + (h - 0.5) * cellW;
      ctx.beginPath();
      ctx.moveTo(tx, padT + gridH);
      ctx.lineTo(tx, padT + gridH + 4);
      ctx.strokeStyle = "rgba(255,255,255,0.4)";
      ctx.stroke();
      ctx.fillText(h, tx, padT + gridH + 16);
    }});

    // Y-Axis Ticks & Lunar Glyphs
    const yStep = Math.max(1, Math.floor(actualSpan / 8));
    for (let r = 0; r < actualSpan; r += yStep) {{
      const dayIdx = startDay + r;
      const meta = fullMeta[dayIdx];
      const ty = padT + (r + 0.5) * cellH;

      ctx.beginPath();
      ctx.moveTo(padL - 4, ty);
      ctx.lineTo(padL, ty);
      ctx.strokeStyle = "rgba(255,255,255,0.4)";
      ctx.stroke();

      ctx.textAlign = "right";
      ctx.fillStyle = "#cbd5e1";
      ctx.fillText(meta.day_str, padL - 8, ty + 3);
      ctx.fillText(meta.phase_icon, padL - 55, ty + 3);
    }}

    // Right Colorbar
    const cbX = padL + gridW + 28, cbW = 14, cbH = gridH;
    const grad = ctx.createLinearGradient(0, padT + cbH, 0, padT);
    grad.addColorStop(0, "#070b1a");
    grad.addColorStop(0.2, "#1e1b4b");
    grad.addColorStop(0.45, "#581c87");
    grad.addColorStop(0.7, "#c026d3");
    grad.addColorStop(0.88, "#f472b6");
    grad.addColorStop(1, "#fef08a");
    ctx.fillStyle = grad;
    ctx.fillRect(cbX, padT, cbW, cbH);
    ctx.strokeStyle = "rgba(255,255,255,0.3)";
    ctx.strokeRect(cbX, padT, cbW, cbH);

    // Colorbar labels
    ctx.textAlign = "left";
    ctx.fillStyle = "#94a3b8";
    ctx.font = "9px sans-serif";
    ctx.fillText("1.00 Zenith", cbX + cbW + 6, padT + 8);
    ctx.fillText("0.50 Half", cbX + cbW + 6, padT + cbH / 2 + 3);
    ctx.fillText("0.00 Void", cbX + cbW + 6, padT + cbH);
  }}

  // Update Slider & Labels
  function updateSlider() {{
    slider.max = Math.max(0, TOTAL_DAYS - viewSpan);
    if (startDay > slider.max) startDay = parseInt(slider.max);
    slider.value = startDay;

    const actualSpan = Math.min(viewSpan, TOTAL_DAYS - startDay);
    const firstDay = fullMeta[startDay].day_str;
    const lastDay = fullMeta[startDay + actualSpan - 1].day_str;
    rangeLabel.textContent = `${{firstDay}} - ${{lastDay}} (${{actualSpan}} Days)`;
    draw();
  }}

  slider.addEventListener("input", (e) => {{
    startDay = parseInt(e.target.value);
    updateSlider();
  }});

  // Preset Buttons (30d / 60d / 90d / 365d)
  presetBtns.forEach(btn => {{
    btn.addEventListener("click", () => {{
      presetBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      viewSpan = parseInt(btn.getAttribute("data-span"));
      updateSlider();
    }});
  }});

  // Interactive Hover on Canvas
  canvas.addEventListener("mousemove", (e) => {{
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const mx = (e.clientX - rect.left) * scaleX;
    const my = (e.clientY - rect.top) * scaleY;

    const padL = 90, padT = 50, padR = 100, padB = 40;
    const gridW = canvas.width - padL - padR;
    const gridH = canvas.height - padT - padB;
    const actualSpan = Math.min(viewSpan, TOTAL_DAYS - startDay);

    if (mx >= padL && mx <= padL + gridW && my >= padT && my <= padT + gridH) {{
      const cellW = gridW / HOURS;
      const cellH = gridH / actualSpan;
      const c = Math.floor((mx - padL) / cellW);
      const r = Math.floor((my - padT) / cellH);
      const dayIdx = startDay + r;

      if (dayIdx < TOTAL_DAYS && c >= 0 && c < 24) {{
        const v = fullMatrix[dayIdx][c];
        const meta = fullMeta[dayIdx];
        hud.innerHTML = `
          <div class="badge">Date: <span class="highlight">${{meta.date}}</span></div>
          <div class="badge">Phase: <span class="highlight">${{meta.phase_icon}} ${{meta.phase_name}}</span></div>
          <div class="badge">Illumination: <span class="highlight">${{meta.illum}}%</span></div>
          <div class="badge">Hour: <span class="highlight">${{String(c + 1).padStart(2, '0')}}:00</span></div>
          <div class="badge">Luminance: <span class="highlight">${{v.toFixed(2)}}</span></div>
          <div class="badge">Rise/Set: <span class="highlight">${{meta.rise_raw}} / ${{meta.set_raw}}</span></div>
        `;
      }}
    }}
  }});

  // Initial draw
  updateSlider();
</script>
</body>
</html>
"""

with open("out/moon_heatmap.html", "w", encoding="utf-8") as f:
    f.write(html_str)

print("Year-Round Moonbeam Carpet with Time Axis successfully generated:")
print("1. Default preview SVG: out/moon_heatmap.svg")
print("2. Interactive Scrubber: out/moon_heatmap.html")