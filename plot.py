import csv
import math
import os

os.makedirs("out", exist_ok=True)

# 基础画布尺寸
WIDTH = 1200
HEIGHT = 520
PAD_L = 60
PAD_R = 30
PAD_T = 75   # 顶部留给月相与满月标记
PAD_B = 45
PLOT_W = WIDTH - PAD_L - PAD_R
PLOT_H = HEIGHT - PAD_T - PAD_B

# 1. 读取 CSV 数据
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
            rows_data.append({"date": date, "rise": rise, "trans": trans, "set": m_set})

# 本地无数据时的保底近似生成
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
            "set": fmt_t(t_set)
        })

total_days = len(rows_data)

# 2. 计算月相与光照百分比
SYNODIC_MONTH = 29.530588
NEW_MOON_REF = 18.16  # 2026 第 18.16 天为新月

for i, row in enumerate(rows_data):
    moon_age = (i - NEW_MOON_REF) % SYNODIC_MONTH
    phase_frac = moon_age / SYNODIC_MONTH
    illumination = (1 - math.cos(phase_frac * 2 * math.pi)) / 2 * 100

    row["moon_age"] = round(moon_age, 1)
    row["illum"] = round(illumination, 1)
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

# 3. 构造纯 SVG 图像
svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" style="background-color: #050b18; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">')

# 渐变与滤镜定义
svg.append('<defs>')
svg.append("""
  <linearGradient id="fullMoonBeam" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.35"/>
    <stop offset="70%" stop-color="#38bdf8" stop-opacity="0.08"/>
    <stop offset="100%" stop-color="#38bdf8" stop-opacity="0"/>
  </linearGradient>
""")
svg.append('</defs>')

# 标题与图例
svg.append(f'<text x="{PAD_L}" y="34" fill="#f8fafc" font-size="16" font-weight="bold" letter-spacing="1">2026 · 朔望月相与月球天行录</text>')
svg.append(f'<text x="{PAD_L}" y="52" fill="#64748b" font-size="11" letter-spacing="0.5">LUNAR PHASES &amp; CELESTIAL EPHEMERIS · HONG KONG OBSERVATORY</text>')

# 图例标注
legend_x = WIDTH - PAD_R - 380
svg.append(f'<g transform="translate({legend_x}, 38)" font-size="11" fill="#94a3b8">')
svg.append('<circle cx="0" cy="-4" r="3.5" fill="#34d399"/><text x="8" y="0">月出</text>')
svg.append('<circle cx="60" cy="-4" r="3.5" fill="#fde047"/><text x="68" y="0">中天</text>')
svg.append('<circle cx="120" cy="-4" r="3.5" fill="#f43f5e"/><text x="128" y="0">月落</text>')
svg.append('<text x="180" y="0">🌕 满月</text>')
svg.append('<text x="240" y="0">🌑 新月</text>')
svg.append('</g>')

# 坐标主绘图区
svg.append(f'<g transform="translate({PAD_L},{PAD_T})">')

# 满月竖向光柱与新月标记
for i, r in enumerate(rows_data):
    cx = (i / total_days) * PLOT_W
    if r["is_full"]:
        svg.append(f'<rect x="{cx - 10:.1f}" y="-20" width="20" height="{PLOT_H + 20}" fill="url(#fullMoonBeam)"/>')
        svg.append(f'<line x1="{cx:.1f}" y1="-20" x2="{cx:.1f}" y2="{PLOT_H}" stroke="rgba(224, 242, 254, 0.4)" stroke-dasharray="2 4"/>')
        svg.append(f'<text x="{cx:.1f}" y="-26" fill="#e0f2fe" font-size="11" text-anchor="middle">🌕</text>')
    elif r["is_new"]:
        svg.append(f'<text x="{cx:.1f}" y="-26" fill="#64748b" font-size="10" text-anchor="middle">🌑</text>')

# 24 小时横轴网格
for h in range(0, 25, 4):
    y = (h / 24.0) * PLOT_H
    svg.append(f'<line x1="0" y1="{y:.1f}" x2="{PLOT_W}" y2="{y:.1f}" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>')
    svg.append(f'<text x="-12" y="{y + 4:.1f}" fill="#64748b" font-size="11" text-anchor="end">{h:02d}:00</text>')

# 12 个月份纵向网格
month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
acc = 0
for m, days in enumerate(month_days, 1):
    mx = (acc / total_days) * PLOT_W
    svg.append(f'<line x1="{mx:.1f}" y1="-10" x2="{mx:.1f}" y2="{PLOT_H}" stroke="rgba(255,255,255,0.08)" stroke-dasharray="4 4"/>')
    svg.append(f'<text x="{mx + 8:.1f}" y="{PLOT_H + 22}" fill="#94a3b8" font-size="11">{m}月</text>')
    acc += days

# 绘制各点并内嵌 GitHub 原生悬停 Tooltip 提示
for i, r in enumerate(rows_data):
    x = (i / total_days) * PLOT_W
    date_display = r["date"] or f"第 {i+1} 天"
    illum_info = f"亮面: {r['illum']}%"

    fr = time_to_frac(r["rise"])
    ft = time_to_frac(r["trans"])
    fs = time_to_frac(r["set"])

    if fr is not None:
        svg.append(
            f'<circle cx="{x:.1f}" cy="{fr*PLOT_H:.1f}" r="1.8" fill="#34d399" opacity="0.85">'
            f'<title>{date_display} ({illum_info})&#10;月出: {r["rise"]}</title>'
            f'</circle>'
        )
    if ft is not None:
        svg.append(
            f'<circle cx="{x:.1f}" cy="{ft*PLOT_H:.1f}" r="1.8" fill="#fde047" opacity="0.85">'
            f'<title>{date_display} ({illum_info})&#10;中天: {r["trans"]}</title>'
            f'</circle>'
        )
    if fs is not None:
        svg.append(
            f'<circle cx="{x:.1f}" cy="{fs*PLOT_H:.1f}" r="1.8" fill="#f43f5e" opacity="0.85">'
            f'<title>{date_display} ({illum_info})&#10;月落: {r["set"]}</title>'
            f'</circle>'
        )

svg.append('</g>')
svg.append('</svg>')

# 写入文件
with open("out/moon.svg", "w", encoding="utf-8") as out:
    out.write("\n".join(svg))

print("✨ 成功生成兼容 GitHub 原生渲染与悬停交互的 SVG: out/moon.svg")