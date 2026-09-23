import csv
import json
import math
import os

os.makedirs("out", exist_ok=True)

# 1. Parse lunar ephemeris data (January 2026, 31 days)
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
                    "rise_raw": r.get("RISE", "--:--"),
                    "trans_raw": (
                        r.get("TRAN.", "") or r.get("TRANSIT", "--:--")
                    ),
                    "set_raw": r.get("SET", "--:--"),
                    "date": d_str,
                }

if not month_days_data:
    for day in range(1, 32):
        t_trans = (13.5 + (day - 1) * (50.47 / 60.0)) % 24.0
        month_days_data[day] = {
            "trans": t_trans,
            "rise": (t_trans - 6.2) % 24.0,
            "set": (t_trans + 6.2) % 24.0,
            "rise_raw": f"{(t_trans - 6.2) % 24.0:04.1f}",
            "trans_raw": f"{t_trans:04.1f}",
            "set_raw": f"{(t_trans + 6.2) % 24.0:04.1f}",
            "date": f"2026-01-{day:02d}",
        }

# 2. Compute Synodic Lunar Phases (Cycle: ~29.53 days)
SYNODIC_MONTH = 29.530588
NEW_MOON_REF = 18.16


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


DAYS = 31
HOURS = 24
matrix = []
day_phases = []

for day in range(1, DAYS + 1):
    meta = get_phase_meta(day - 1)
    day_phases.append(meta)

    info = month_days_data.get(day)
    t_trans = info["trans"] if info else None
    row_vals = []

    phase_lum_factor = 0.08 + 0.92 * (meta["illum"] / 100.0)

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
            combined_val = altitude_geom * phase_lum_factor
            row_vals.append(round(max(0.0, combined_val), 3))
        else:
            row_vals.append(0.0)
    matrix.append(row_vals)


# 3. Celestial Moonlight Palette
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


# 4. Generate SVG Output
W_TOTAL, H_TOTAL = 780, 620
PAD_L, PAD_T, PAD_R, PAD_B = 105, 65, 125, 60
GRID_W = W_TOTAL - PAD_L - PAD_R
GRID_H = H_TOTAL - PAD_T - PAD_B
CELL_W = GRID_W / HOURS
CELL_H = GRID_H / DAYS

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
    f'<text x="{PAD_L + GRID_W/2}" y="50" text-anchor="middle" font-size="11" fill="#94a3b8" letter-spacing="0.5">JANUARY 2026 · LUNAR PHASES &amp; CELESTIAL ILLUMINATION</text>'
)
svg.append(
    f'<text x="{PAD_L + GRID_W/2}" y="{H_TOTAL - 15}" text-anchor="middle" font-size="12" fill="#94a3b8">hour of the day</text>'
)
svg.append(
    f'<text x="22" y="{PAD_T + GRID_H/2}" text-anchor="middle" font-size="12" fill="#94a3b8" transform="rotate(-90 22 {PAD_T + GRID_H/2})">day of the month</text>'
)

svg.append(f'<g id="heatmap-cells" transform="translate({PAD_L}, {PAD_T})">')
for r in range(DAYS):
    for c in range(HOURS):
        v = matrix[r][c]
        color = dreamy_moon_color(v)
        p = day_phases[r]
        is_lit = "lit-cell" if v > 0.3 else ""
        delay_sec = round((r * 0.02 + c * 0.005), 3)
        svg.append(
            f'<rect class="cell {is_lit}" data-r="{r}" data-c="{c}" x="{c * CELL_W:.2f}" y="{r * CELL_H:.2f}" width="{CELL_W:.2f}" height="{CELL_H:.2f}" fill="{color}" stroke="rgba(255,255,255,0.03)" stroke-width="0.5" style="animation-delay: {delay_sec}s;">'
            f'<title>Jan {r+1} ({p["name"]}) | Hour {c+1:02d}:00&#10;Illumination: {p["illum"]}%&#10;Luminance Index: {v:.2f}</title></rect>'
        )

# 动态光标指示线 (扫描器用)
svg.append(
    f'<line id="scanLine" x1="0" y1="0" x2="{GRID_W}" y2="0" stroke="#fef08a" stroke-width="1.8" opacity="0" stroke-dasharray="4 2" style="filter: drop-shadow(0 0 6px #f472b6); pointer-events:none;"/>'
)

svg.append(
    f'<rect x="0" y="0" width="{GRID_W}" height="{GRID_H}" fill="none" stroke="rgba(255,255,255,0.18)" stroke-width="1.2" pointer-events="none"/>'
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
    p = day_phases[r]
    svg.append(
        f'<line x1="0" y1="{ty:.1f}" x2="-5" y2="{ty:.1f}" stroke="rgba(255,255,255,0.3)" stroke-width="1"/>'
    )
    svg.append(
        f'<text x="-8" y="{ty + 4:.1f}" text-anchor="end" font-size="11" fill="#94a3b8">{txt}</text>'
    )
    svg.append(
        f'<text x="-25" y="{ty + 4:.1f}" text-anchor="end" font-size="11">{p["icon"]}</text>'
    )
svg.append("</g>")

# Right Colorbar
CBAR_X = PAD_L + GRID_W + 34
CBAR_W = 16
CBAR_H = GRID_H
svg.append(
    f'<rect x="{CBAR_X}" y="{PAD_T}" width="{CBAR_W}" height="{CBAR_H}" rx="3" fill="url(#dreamyGrad)" stroke="rgba(255,255,255,0.2)" stroke-width="1"/>'
)

cb_ticks = [
    (0.0, "0.00 (Dark / Void)"),
    (0.25, "0.25 (Crescent / Low)"),
    (0.5, "0.50 (Quarter Moon)"),
    (0.75, "0.75 (Gibbous Glow)"),
    (1.0, "1.00 (Full Moon Zenith)"),
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
    f'<text x="{CBAR_X + 96}" y="{PAD_T + CBAR_H/2}" text-anchor="middle" font-size="11" fill="#94a3b8" letter-spacing="0.5" transform="rotate(90 {CBAR_X + 96} {PAD_T + CBAR_H/2})">lunar luminance index</text>'
)
svg.append("</svg>")

with open("out/moon_heatmap.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(svg))


# 5. Interactive & Animated HTML Webpage
matrix_json = json.dumps(matrix)
phases_json = json.dumps(day_phases)
ephem_json = json.dumps(month_days_data)

html_str = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dynamic Celestial Lunar Heatmap · 2026</title>
<style>
  * {{ box-sizing: border-box; }}
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
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 24px;
    padding: 24px;
    box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.9), 0 0 50px rgba(192, 38, 211, 0.15);
    backdrop-filter: blur(16px);
  }}
  #hud {{
    font-size: 13px;
    color: #cbd5e1;
    margin-bottom: 14px;
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 12px;
    min-height: 32px;
  }}
  .badge {{
    padding: 4px 14px;
    border-radius: 9999px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s ease;
  }}
  .highlight {{
    color: #fde047;
    font-weight: 600;
  }}
  
  /* 动效 1: 进场流光瀑布动画 */
  .cell {{
    opacity: 0;
    transform: scale(0.92);
    animation: cellCascade 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }}
  @keyframes cellCascade {{
    to {{
      opacity: 1;
      transform: scale(1);
    }}
  }}

  /* 动效 2: 皓月光晕呼吸流动 */
  .lit-cell {{
    animation: cellCascade 0.6s forwards, moonPulse 3.5s ease-in-out infinite alternate;
  }}
  @keyframes moonPulse {{
    0% {{ filter: drop-shadow(0 0 0px transparent); }}
    100% {{ filter: drop-shadow(0 0 5px rgba(254, 240, 138, 0.6)); }}
  }}

  /* 控制栏组件 */
  .controls {{
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 16px;
    margin-top: 16px;
  }}
  .btn {{
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #f8fafc;
    border-radius: 20px;
    padding: 6px 16px;
    font-size: 12px;
    cursor: pointer;
    transition: background 0.2s, transform 0.1s;
  }}
  .btn:hover {{
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-1px);
  }}
  .status-text {{
    font-size: 12px;
    color: #94a3b8;
  }}
</style>
</head>
<body>

<div class="card">
  <div id="hud">
    <div class="badge">✨ Initializing celestial time-lapse engine...</div>
  </div>

  {"\n".join(svg)}

  <div class="controls">
    <button class="btn" id="togglePlay">⏸ Pause Scan</button>
    <button class="btn" id="speedBtn">⚡ Speed: 1x</button>
    <div class="status-text" id="statusDesc">Auto-scrubbing January diurnal cycle</div>
  </div>
</div>

<script>
  const matrix = {matrix_json};
  const phases = {phases_json};
  const ephem = {ephem_json};
  const CELL_H = {CELL_H};
  const DAYS = {DAYS};
  const HOURS = {HOURS};

  const hud = document.getElementById("hud");
  const scanLine = document.getElementById("scanLine");
  const togglePlay = document.getElementById("togglePlay");
  const speedBtn = document.getElementById("speedBtn");
  const statusDesc = document.getElementById("statusDesc");
  const rects = document.querySelectorAll("g rect.cell");

  let isPlaying = true;
  let currentDay = 0;
  let speed = 1;
  let autoTimer = null;
  let activeRect = null;

  function updateDisplay(r, c) {{
    const val = matrix[r][c];
    const p = phases[r];
    const ep = ephem[r + 1] || {{}};

    // 移动黄色天象扫描线
    scanLine.setAttribute("y1", (r + 0.5) * CELL_H);
    scanLine.setAttribute("y2", (r + 0.5) * CELL_H);
    scanLine.style.opacity = "0.85";

    // 高亮当前格子
    if (activeRect) {{
      activeRect.style.stroke = "rgba(255,255,255,0.03)";
      activeRect.style.strokeWidth = "0.5px";
      activeRect.style.filter = "none";
    }}
    const targetIdx = r * HOURS + c;
    activeRect = rects[targetIdx];
    if (activeRect) {{
      activeRect.style.stroke = "#fef08a";
      activeRect.style.strokeWidth = "1.5px";
      activeRect.style.filter = "drop-shadow(0 0 10px #ec4899)";
    }}

    hud.innerHTML = `
      <div class="badge">Date: <span class="highlight">Jan ${{r + 1}}</span></div>
      <div class="badge">Phase: <span class="highlight">${{p.icon}} ${{p.name}}</span></div>
      <div class="badge">Illumination: <span class="highlight">${{p.illum}}%</span></div>
      <div class="badge">Peak/Hour: <span class="highlight">${{String(c + 1).padStart(2, '0')}}:00</span></div>
      <div class="badge">Luminance: <span class="highlight">${{val.toFixed(2)}}</span></div>
      <div class="badge">Rise/Set: <span class="highlight">${{ep.rise_raw || '--'}} / ${{ep.set_raw || '--'}}</span></div>
    `;
  }}

  // 自动巡航主循环
  function autoStep() {{
    if (!isPlaying) return;
    // 寻找当天月光最亮的时刻高亮展示
    let maxHour = 12;
    let maxVal = -1;
    for (let h = 0; h < HOURS; h++) {{
      if (matrix[currentDay][h] > maxVal) {{
        maxVal = matrix[currentDay][h];
        maxHour = h;
      }}
    }}
    updateDisplay(currentDay, maxHour);
    currentDay = (currentDay + 1) % DAYS;

    const delay = 450 / speed;
    autoTimer = setTimeout(autoStep, delay);
  }}

  // 启动
  autoStep();

  // 鼠标交互接管
  rects.forEach((rect) => {{
    rect.style.cursor = "pointer";
    rect.addEventListener("mouseenter", () => {{
      if (isPlaying) {{
        clearTimeout(autoTimer);
        statusDesc.textContent = "Manual inspection active (Hovering)";
      }}
      const r = parseInt(rect.getAttribute("data-r"), 10);
      const c = parseInt(rect.getAttribute("data-c"), 10);
      updateDisplay(r, c);
    }});

    rect.addEventListener("mouseleave", () => {{
      if (isPlaying) {{
        statusDesc.textContent = "Resuming celestial scan...";
        currentDay = parseInt(rect.getAttribute("data-r"), 10);
        clearTimeout(autoTimer);
        autoTimer = setTimeout(autoStep, 800);
      }}
    }});
  }});

  // 播放 / 暂停切换
  togglePlay.addEventListener("click", () => {{
    isPlaying = !isPlaying;
    if (isPlaying) {{
      togglePlay.textContent = "⏸ Pause Scan";
      statusDesc.textContent = "Auto-scrubbing January diurnal cycle";
      autoStep();
    }} else {{
      togglePlay.textContent = "▶ Resume Scan";
      statusDesc.textContent = "Scan paused";
      clearTimeout(autoTimer);
    }}
  }});

  // 调速功能 (1x -> 2x -> 0.5x)
  speedBtn.addEventListener("click", () => {{
    if (speed === 1) speed = 2;
    else if (speed === 2) speed = 0.5;
    else speed = 1;
    speedBtn.textContent = `⚡ Speed: ${{speed}}x`;
  }});
</script>
</body>
</html>
"""

with open("out/moon_heatmap.html", "w", encoding="utf-8") as f:
    f.write(html_str)

print("Dynamic animations successfully baked into:")
print("1. out/moon_heatmap.svg")
print("2. out/moon_heatmap.html")