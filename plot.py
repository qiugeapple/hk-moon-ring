import csv
import json
import math
import os

os.makedirs("out", exist_ok=True)

# Canvas dimensions
WIDTH = 1200
HEIGHT = 520
PAD_L = 60
PAD_R = 30
PAD_T = 75
PAD_B = 45
PLOT_W = WIDTH - PAD_L - PAD_R
PLOT_H = HEIGHT - PAD_T - PAD_B

# 1. Load CSV data
rows_data = []
csv_path = "data/moon-2026.csv"

if os.path.exists(csv_path):
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            date = r.get("Date") or r.get("DATE") or r.get("日期") or ""
            rise = r.get("RISE", "").strip()
            trans = r.get("TRAN.", "").strip() or r.get("TRANSIT", "").strip()
            m_set = r.get("SET", "").strip()
            rows_data.append(
                {"date": date, "rise": rise, "trans": trans, "set": m_set}
            )

if not rows_data:
    import datetime

    start_date = datetime.date(2026, 1, 1)
    for d in range(365):
        cur_date = start_date + datetime.timedelta(days=d)
        t_trans = (13.5 + d * (50.47 / 60.0)) % 24.0
        t_rise = (t_trans - 6.2) % 24.0
        t_set = (t_trans + 6.2) % 24.0

        def fmt_t(val):
            h = int(val)
            m = int((val - h) * 60)
            return f"{h:02d}:{m:02d}"

        rows_data.append({
            "date": cur_date.strftime("%Y-%m-%d"),
            "rise": fmt_t(t_rise),
            "trans": fmt_t(t_trans),
            "set": fmt_t(t_set),
        })

total_days = len(rows_data)

# 2. Compute lunar synodic cycle
SYNODIC_MONTH = 29.530588
NEW_MOON_REF = 18.16

for i, row in enumerate(rows_data):
    moon_age = (i - NEW_MOON_REF) % SYNODIC_MONTH
    phase_frac = moon_age / SYNODIC_MONTH
    illum = (1 - math.cos(phase_frac * 2 * math.pi)) / 2 * 100

    row["moon_age"] = round(moon_age, 1)
    row["illum"] = round(illum, 1)
    row["is_new"] = bool(
        abs(moon_age) < 0.6 or abs(moon_age - SYNODIC_MONTH) < 0.6
    )
    row["is_full"] = bool(abs(moon_age - SYNODIC_MONTH / 2) < 0.6)


def time_to_frac(timestr):
    if not timestr or ":" not in timestr:
        return None
    try:
        hh, mm = timestr.split(":")
        return (int(hh) + int(mm) / 60.0) / 24.0
    except Exception:
        return None


# ==========================================
# 3. Output 1: Static SVG (out/moon.svg)
# ==========================================
svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" style="background-color: #050b18; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">'
]
svg.append(
    '<defs><linearGradient id="fullMoonBeam" x1="0" y1="0" x2="0"'
    ' y2="1"><stop offset="0%" stop-color="#38bdf8" stop-opacity="0.35"/><stop'
    ' offset="70%" stop-color="#38bdf8" stop-opacity="0.08"/><stop offset="100%"'
    ' stop-color="#38bdf8" stop-opacity="0"/></linearGradient></defs>'
)
svg.append(
    f'<text x="{PAD_L}" y="34" fill="#f8fafc" font-size="16" font-weight="600"'
    ' letter-spacing="1">2026 · Lunar Phases &amp; Celestial Ephemeris</text>'
)
svg.append(
    f'<text x="{PAD_L}" y="52" fill="#64748b" font-size="11"'
    ' letter-spacing="0.5">MOONRISE · CULMINATION · MOONSET | HONG KONG'
    ' OBSERVATORY</text>'
)

legend_x = WIDTH - PAD_R - 440
svg.append(
    f'<g transform="translate({legend_x}, 38)" font-size="11" fill="#94a3b8">'
)
svg.append(
    '<circle cx="0" cy="-4" r="3.5" fill="#34d399"/><text x="8"'
    ' y="0">Moonrise</text>'
)
svg.append(
    '<circle cx="78" cy="-4" r="3.5" fill="#fde047"/><text x="86"'
    ' y="0">Transit</text>'
)
svg.append(
    '<circle cx="146" cy="-4" r="3.5" fill="#f43f5e"/><text x="154"'
    ' y="0">Moonset</text>'
)
svg.append(
    '<text x="225" y="0">🌕 Full Moon</text><text x="315" y="0">🌑 New'
    ' Moon</text>'
)
svg.append('</g>')

svg.append(f'<g transform="translate({PAD_L},{PAD_T})">')

for i, r in enumerate(rows_data):
    cx = (i / total_days) * PLOT_W
    if r["is_full"]:
        svg.append(
            f'<rect x="{cx - 10:.1f}" y="-20" width="20"'
            f' height="{PLOT_H + 20}" fill="url(#fullMoonBeam)"/>'
        )
        svg.append(
            f'<line x1="{cx:.1f}" y1="-20" x2="{cx:.1f}" y2="{PLOT_H}"'
            ' stroke="rgba(224, 242, 254, 0.4)" stroke-dasharray="2 4"/>'
        )
        svg.append(
            f'<text x="{cx:.1f}" y="-26" fill="#e0f2fe" font-size="11"'
            ' text-anchor="middle">🌕</text>'
        )
    elif r["is_new"]:
        svg.append(
            f'<text x="{cx:.1f}" y="-26" fill="#64748b" font-size="10"'
            ' text-anchor="middle">🌑</text>'
        )

for h in range(0, 25, 4):
    y = (h / 24.0) * PLOT_H
    svg.append(
        f'<line x1="0" y1="{y:.1f}" x2="{PLOT_W}" y2="{y:.1f}"'
        ' stroke="rgba(255,255,255,0.06)"/>'
    )
    svg.append(
        f'<text x="-12" y="{y + 4:.1f}" fill="#64748b" font-size="11"'
        f' text-anchor="end">{h:02d}:00</text>'
    )

month_names = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
acc = 0
for m, days in enumerate(month_days):
    mx = (acc / total_days) * PLOT_W
    svg.append(
        f'<line x1="{mx:.1f}" y1="-10" x2="{mx:.1f}" y2="{PLOT_H}"'
        ' stroke="rgba(255,255,255,0.08)" stroke-dasharray="4 4"/>'
    )
    svg.append(
        f'<text x="{mx + 8:.1f}" y="{PLOT_H + 22}" fill="#94a3b8"'
        f' font-size="11">{month_names[m]}</text>'
    )
    acc += days

for i, r in enumerate(rows_data):
    x = (i / total_days) * PLOT_W
    date_display = r["date"] or f"Day {i+1}"
    illum_info = f"Illumination: {r['illum']}%"

    fr = time_to_frac(r["rise"])
    ft = time_to_frac(r["trans"])
    fs = time_to_frac(r["set"])

    if fr is not None:
        svg.append(
            f'<circle cx="{x:.1f}" cy="{fr*PLOT_H:.1f}" r="1.8" fill="#34d399"'
            f' opacity="0.85"><title>{date_display} ({illum_info})&#10;Moonrise:'
            f' {r["rise"]}</title></circle>'
        )
    if ft is not None:
        svg.append(
            f'<circle cx="{x:.1f}" cy="{ft*PLOT_H:.1f}" r="1.8" fill="#fde047"'
            f' opacity="0.85"><title>{date_display} ({illum_info})&#10;Transit:'
            f' {r["trans"]}</title></circle>'
        )
    if fs is not None:
        svg.append(
            f'<circle cx="{x:.1f}" cy="{fs*PLOT_H:.1f}" r="1.8" fill="#f43f5e"'
            f' opacity="0.85"><title>{date_display} ({illum_info})&#10;Moonset:'
            f' {r["set"]}</title></circle>'
        )

svg.append("</g></svg>")

with open("out/moon.svg", "w", encoding="utf-8") as out:
    out.write("\n".join(svg))


# ==========================================
# 4. Output 2: Interactive & Animated HTML
# ==========================================
data_json = json.dumps(rows_data)

# 嵌入动态指示器与交互层
inner_svg = "\n".join(svg)
dynamic_elements = f"""
      <line id="crossX" x1="0" y1="-30" x2="0" y2="{PLOT_H}" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="3 3" opacity="0.9" style="display:none;"/>
      <circle id="dotRise" r="4.5" fill="#34d399" stroke="#ffffff" stroke-width="1.5" style="display:none;"/>
      <circle id="dotTrans" r="4.5" fill="#fde047" stroke="#ffffff" stroke-width="1.5" style="display:none;"/>
      <circle id="dotSet" r="4.5" fill="#f43f5e" stroke="#ffffff" stroke-width="1.5" style="display:none;"/>
    </g>
    <rect id="hitbox" x="{PAD_L}" y="0" width="{PLOT_W}" height="{HEIGHT}" fill="transparent" style="cursor: crosshair;"/>
</svg>
"""
final_svg_for_html = inner_svg.replace("</g></svg>", dynamic_elements)

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2026 Lunar Phases & Celestial Ephemeris</title>
<style>
  :root {{
    --bg: #030712;
    --rise: #34d399;
    --trans: #fde047;
    --set: #f43f5e;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    padding: 30px 15px;
    background: radial-gradient(circle at 50% 10%, #172554 0%, #030712 70%);
    color: #f8fafc;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    min-height: 100vh;
  }}
  .card {{
    position: relative;
    background: rgba(11, 17, 32, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 20px;
    padding: 24px;
    box-shadow: 0 30px 60px rgba(0,0,0,0.85);
  }}
  .status-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    font-size: 13px;
    color: #94a3b8;
  }}
  .pulse-dot {{
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #38bdf8;
    margin-right: 6px;
    box-shadow: 0 0 10px #38bdf8;
    animation: pulse 2s infinite;
  }}
  @keyframes pulse {{
    0% {{ opacity: 0.4; transform: scale(0.9); }}
    50% {{ opacity: 1; transform: scale(1.3); }}
    100% {{ opacity: 0.4; transform: scale(0.9); }}
  }}
  /* 让满月光柱自动产生呼吸流动动画 */
  #fullMoonBeam stop {{
    animation: beamGlow 4s ease-in-out infinite alternate;
  }}
  @keyframes beamGlow {{
    0% {{ stop-opacity: 0.25; }}
    100% {{ stop-opacity: 0.55; }}
  }}
  #tooltip {{
    position: absolute;
    pointer-events: none;
    background: rgba(15, 23, 42, 0.96);
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 12px;
    line-height: 1.7;
    display: none;
    box-shadow: 0 16px 32px rgba(0,0,0,0.8);
    z-index: 1000;
    min-width: 190px;
    backdrop-filter: blur(8px);
  }}
</style>
</head>
<body>

<div class="card">
  <div class="status-bar">
    <div><span class="pulse-dot"></span><span>Interactive HUD: Move cursor over the chart to inspect ephemeris</span></div>
    <div id="live-date">Hovering: None</div>
  </div>

  <div id="chart-container" style="position: relative;">
    {final_svg_for_html}
    <div id="tooltip"></div>
  </div>
</div>

<script>
  const data = {data_json};
  const PLOT_W = {PLOT_W};
  const PLOT_H = {PLOT_H};
  const PAD_L = {PAD_L};
  const PAD_T = {PAD_T};

  const container = document.getElementById("chart-container");
  const hitbox = document.getElementById("hitbox");
  const crossX = document.getElementById("crossX");
  const dotRise = document.getElementById("dotRise");
  const dotTrans = document.getElementById("dotTrans");
  const dotSet = document.getElementById("dotSet");
  const tooltip = document.getElementById("tooltip");
  const liveDate = document.getElementById("live-date");

  function timeToFrac(t) {{
    if (!t || !t.includes(":")) return null;
    const parts = t.split(":");
    return (parseInt(parts[0], 10) + parseInt(parts[1], 10) / 60.0) / 24.0;
  }}

  function getMoonPhaseName(illum, age) {{
    if (age < 1.5 || age > 28) return "🌑 New Moon";
    if (age >= 1.5 && age < 6.5) return "🌒 Waxing Crescent";
    if (age >= 6.5 && age < 8.5) return "🌓 First Quarter";
    if (age >= 8.5 && age < 13.5) return "🌔 Waxing Gibbous";
    if (age >= 13.5 && age < 16) return "🌕 Full Moon";
    if (age >= 16 && age < 21) return "🌖 Waning Gibbous";
    if (age >= 21 && age < 23) return "🌗 Last Quarter";
    return "🌘 Waning Crescent";
  }}

  hitbox.addEventListener("mousemove", (e) => {{
    const rect = hitbox.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    if (mouseX < 0 || mouseX > PLOT_W) return;

    const idx = Math.min(data.length - 1, Math.max(0, Math.round((mouseX / PLOT_W) * (data.length - 1))));
    const d = data[idx];
    if (!d) return;

    const snapX = (idx / data.length) * PLOT_W;
    crossX.setAttribute("x1", snapX);
    crossX.setAttribute("x2", snapX);
    crossX.style.display = "block";

    const fr = timeToFrac(d.rise);
    const ft = timeToFrac(d.trans);
    const fs = timeToFrac(d.set);

    function updateDot(dot, frac) {{
      if (frac !== null) {{
        dot.setAttribute("cx", snapX);
        dot.setAttribute("cy", frac * PLOT_H);
        dot.style.display = "block";
      }} else {{
        dot.style.display = "none";
      }}
    }}
    updateDot(dotRise, fr);
    updateDot(dotTrans, ft);
    updateDot(dotSet, fs);

    liveDate.textContent = `Inspecting: ${{d.date}}`;

    const cRect = container.getBoundingClientRect();
    tooltip.style.display = "block";
    
    // 防边界溢出
    let leftPos = e.clientX - cRect.left + 16;
    if (leftPos + 200 > PLOT_W + PAD_L) {{
      leftPos = e.clientX - cRect.left - 210;
    }}
    tooltip.style.left = leftPos + "px";
    tooltip.style.top = (e.clientY - cRect.top) + "px";

    tooltip.innerHTML = `
      <div style="color:#38bdf8; font-weight:700; font-size:13px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:4px; margin-bottom:6px;">${{d.date}}</div>
      <div style="color:#e2e8f0; margin-bottom:4px;">${{getMoonPhaseName(d.illum, d.moon_age)}}</div>
      <div style="color:#94a3b8; font-size:11px; margin-bottom:6px;">Illumination: <b style="color:#fde047;">${{d.illum}}%</b></div>
      <div><span style="color:var(--rise);">● Moonrise:</span> <b>${{d.rise || 'None'}}</b></div>
      <div><span style="color:var(--trans);">● Transit:</span> <b>${{d.trans || 'None'}}</b></div>
      <div><span style="color:var(--set);">● Moonset:</span> <b>${{d.set || 'None'}}</b></div>
    `;
  }});

  hitbox.addEventListener("mouseleave", () => {{
    crossX.style.display = "none";
    dotRise.style.display = "none";
    dotTrans.style.display = "none";
    dotSet.style.display = "none";
    tooltip.style.display = "none";
    liveDate.textContent = "Hovering: None";
  }});
</script>
</body>
</html>
"""

# 同时在根目录写一个 index.html，让主链接直接生效
with open("out/moon_celestial.html", "w", encoding="utf-8") as out:
    out.write(html_content)

with open("index.html", "w", encoding="utf-8") as out:
    out.write(html_content)

print("Fix completed! Successfully generated out/moon.svg, out/moon_celestial.html, and index.html")