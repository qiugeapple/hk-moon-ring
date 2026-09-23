import csv
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

# Fallback simulation if CSV is missing
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

# 2. Compute lunar synodic cycle and illumination
SYNODIC_MONTH = 29.530588
NEW_MOON_REF = 18.16

for i, row in enumerate(rows_data):
    moon_age = (i - NEW_MOON_REF) % SYNODIC_MONTH
    phase_frac = moon_age / SYNODIC_MONTH
    illum = (1 - math.cos(phase_frac * 2 * math.pi)) / 2 * 100

    row["moon_age"] = round(moon_age, 1)
    row["illum"] = round(illum, 1)
    row["is_new"] = abs(moon_age) < 0.6 or abs(moon_age - SYNODIC_MONTH) < 0.6
    row["is_full"] = abs(moon_age - SYNODIC_MONTH / 2) < 0.6


def time_to_frac(timestr):
    if not timestr or ":" not in timestr:
        return None
    try:
        hh, mm = timestr.split(":")
        return (int(hh) + int(mm) / 60.0) / 24.0
    except Exception:
        return None


# ==========================================
# 3. Output 1: Static SVG for GitHub README
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
    '<circle cx="0" cy="-4" r="3.5" fill="#34d399"/><text x="8" y="0">Moonrise</text>'
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

# Full moon beams and new moon markers
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

# 24-hour diurnal grid lines
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

# 12-month calendar dividing lines
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

# Render scatter points with native SVG hover tooltips
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
# 4. Output 2: Interactive HTML for GitHub Pages
# ==========================================
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>2026 Lunar Phases & Celestial Ephemeris</title>
<style>
  body {{ margin: 0; padding: 25px 15px; background: #030712; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; justify-content: center; }}
  .card {{ position: relative; background: #0b1120; border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 20px; }}
  #tooltip {{ position: absolute; pointer-events: none; background: rgba(15,23,42,0.95); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 10px 14px; font-size: 12px; line-height: 1.6; display: none; transform: translate(14px,-50%); box-shadow: 0 12px 24px rgba(0,0,0,0.6); }}
</style>
</head>
<body>
<div class="card">
  {''.join(svg).replace('</svg>', f'<line id="crossX" x1="0" y1="-20" x2="0" y2="{PLOT_H}" stroke="rgba(255,255,255,0.4)" stroke-dasharray="3 3" style="display:none;"/></g><rect id="overlay" x="{PAD_L}" y="{PAD_T}" width="{PLOT_W}" height="{PLOT_H}" fill="transparent" style="cursor:crosshair;"/></svg>')}
  <div id="tooltip"></div>
</div>
<script>
  const data = {rows_data};
  const overlay = document.getElementById("overlay");
  const crossX = document.getElementById("crossX");
  const tooltip = document.getElementById("tooltip");
  const PLOT_W = {PLOT_W};

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

  overlay.addEventListener("mousemove", (e) => {{
    const rect = overlay.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    if (mouseX < 0 || mouseX > PLOT_W) return;
    const idx = Math.min(data.length - 1, Math.max(0, Math.round((mouseX / PLOT_W) * (data.length - 1))));
    const d = data[idx];
    if (!d) return;

    const snapX = (idx / data.length) * PLOT_W;
    crossX.setAttribute("x1", snapX);
    crossX.setAttribute("x2", snapX);
    crossX.style.display = "block";

    tooltip.style.display = "block";
    tooltip.style.left = (e.clientX - overlay.parentElement.getBoundingClientRect().left) + "px";
    tooltip.style.top = (e.clientY - overlay.parentElement.getBoundingClientRect().top) + "px";
    tooltip.innerHTML = `
      <div style="color:#38bdf8;font-weight:bold;margin-bottom:4px;">${{d.date}}</div>
      <div style="color:#cbd5e1;margin-bottom:4px;">${{getMoonPhaseName(d.illum, d.moon_age)}} (${{d.illum}}%)</div>
      <div><span style="color:#34d399">● Moonrise:</span> ${{d.rise || 'None'}}</div>
      <div><span style="color:#fde047">● Transit:</span> ${{d.trans || 'None'}}</div>
      <div><span style="color:#f43f5e">● Moonset:</span> ${{d.set || 'None'}}</div>
    `;
  }});

  overlay.addEventListener("mouseleave", () => {{
    crossX.style.display = "none";
    tooltip.style.display = "none";
  }});
</script>
</body>
</html>
"""

with open("out/moon_celestial.html", "w", encoding="utf-8") as out:
    out.write(html_content)

print("Generated out/moon.svg and out/moon_celestial.html successfully.")