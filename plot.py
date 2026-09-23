import csv
import os

# 确保输出目录存在
os.makedirs("out", exist_ok=True)

WIDTH = 1120
HEIGHT = 440
PAD_L = 65
PAD_R = 35
PAD_T = 50
PAD_B = 40
PLOT_W = WIDTH - PAD_L - PAD_R
PLOT_H = HEIGHT - PAD_T - PAD_B

rows_data = []

# 1. 读取原始 CSV 数据
with open("data/moon-2026.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for r in reader:
        # 支持常见列名命名兼容
        date = r.get("Date") or r.get("DATE") or r.get("日期") or ""
        rise = r.get("RISE", "").strip()
        trans = r.get("TRAN.", "").strip() or r.get("TRANSIT", "").strip()
        m_set = r.get("SET", "").strip()
        rows_data.append({"date": date, "rise": rise, "trans": trans, "set": m_set})

total_days = max(len(rows_data), 365)


def time_to_frac(timestr):
    if not timestr or ":" not in timestr:
        return None
    try:
        parts = timestr.split(":")
        return (int(parts[0]) + int(parts[1]) / 60.0) / 24.0
    except Exception:
        return None


# 2. 构建现代化深空夜空风格的 SVG + 内嵌交互脚本
html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<title>2026 月球出没运动轨迹</title>
<style>
  body {{
    margin: 0;
    padding: 30px 15px;
    background: radial-gradient(ellipse at top, #0f172a 0%, #030712 100%);
    color: #f1f5f9;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
  }}
  .card {{
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
    padding: 24px;
    position: relative;
    backdrop-filter: blur(12px);
  }}
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }}
  .title {{ margin: 0; font-size: 18px; font-weight: 500; letter-spacing: 0.5px; }}
  .legend {{
    display: flex;
    gap: 16px;
    font-size: 12px;
  }}
  .leg-item {{ display: flex; align-items: center; gap: 6px; }}
  .dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; }}
  #tooltip {{
    position: absolute;
    pointer-events: none;
    background: rgba(15, 23, 42, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 12px;
    line-height: 1.6;
    color: #f8fafc;
    display: none;
    box-shadow: 0 10px 25px rgba(0,0,0,0.6);
    transform: translate(14px, -50%);
  }}
</style>
</head>
<body>

<div class="card">
  <div class="header">
    <h3 class="title">2026 年度香港月球运行轨图 (Moonrise · Transit · Moonset)</h3>
    <div class="legend">
      <span class="leg-item"><span class="dot" style="background:#4ade80; box-shadow:0 0 8px #4ade80;"></span> 月出 (Rise)</span>
      <span class="leg-item"><span class="dot" style="background:#facc15; box-shadow:0 0 8px #facc15;"></span> 中天 (Transit)</span>
      <span class="leg-item"><span class="dot" style="background:#f87171; box-shadow:0 0 8px #f87171;"></span> 月落 (Set)</span>
    </div>
  </div>

  <svg id="chart" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
    <defs>
      <!-- 发光滤镜 -->
      <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="1.5" result="coloredBlur"/>
        <feMerge>
          <feMergeNode in="coloredBlur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
    </defs>

    <g transform="translate({PAD_L},{PAD_T})">
      <!-- 白昼与夜间半透明光影分界（夜间 19:00 - 06:00 呈现微微深蓝） -->
      <rect x="0" y="0" width="{PLOT_W}" height="{6/24 * PLOT_H}" fill="#1e293b" opacity="0.3"/>
      <rect x="0" y="{19/24 * PLOT_H}" width="{PLOT_W}" height="{5/24 * PLOT_H}" fill="#1e293b" opacity="0.3"/>

      <!-- 24 小时横向网格刻度 -->
"""

# 添加横向时间网格
for h in range(0, 25, 4):
    y = (h / 24.0) * PLOT_H
    html_content += f"""
      <line x1="0" y1="{y:.1f}" x2="{PLOT_W}" y2="{y:.1f}" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
      <text x="-12" y="{y + 4:.1f}" fill="#64748b" font-size="11" text-anchor="end">{h:02d}:00</text>
    """

# 月份纵向分界虚线
month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
acc_day = 0
for m, days in enumerate(month_days, 1):
    mx = (acc_day / total_days) * PLOT_W
    html_content += f"""
      <line x1="{mx:.1f}" y1="0" x2="{mx:.1f}" y2="{PLOT_H}" stroke="rgba(255,255,255,0.08)" stroke-dasharray="3 3"/>
      <text x="{mx + 8:.1f}" y="{PLOT_H + 22}" fill="#94a3b8" font-size="11">{m}月</text>
    """
    acc_day += days

# 绘制月升、中天、月落点
pts_rise, pts_trans, pts_set = [], [], []

for i, row in enumerate(rows_data):
    x = (i / total_days) * PLOT_W
    f_rise = time_to_frac(row["rise"])
    f_trans = time_to_frac(row["trans"])
    f_set = time_to_frac(row["set"])

    if f_rise is not None:
        y = f_rise * PLOT_H
        pts_rise.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.8" fill="#4ade80" filter="url(#glow)" opacity="0.85"/>'
        )
    if f_trans is not None:
        y = f_trans * PLOT_H
        # 修复：确保 cx 始终为 x，不再是 y_trans
        pts_trans.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.8" fill="#facc15" filter="url(#glow)" opacity="0.85"/>'
        )
    if f_set is not None:
        y = f_set * PLOT_H
        pts_set.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.8" fill="#f87171" filter="url(#glow)" opacity="0.85"/>'
        )

html_content += "\n".join(pts_rise)
html_content += "\n".join(pts_trans)
html_content += "\n".join(pts_set)

# 交互指示线
html_content += f"""
      <line id="focusLine" x1="0" y1="0" x2="0" y2="{PLOT_H}" stroke="rgba(255,255,255,0.4)" stroke-dasharray="4 4" style="display:none; pointer-events:none;"/>
    </g>
    <!-- 交互透明捕捉层 -->
    <rect id="hitArea" x="{PAD_L}" y="{PAD_T}" width="{PLOT_W}" height="{PLOT_H}" fill="transparent" style="cursor: crosshair;"/>
  </svg>
  <div id="tooltip"></div>
</div>

<script>
  const rawData = {rows_data};
  const hitArea = document.getElementById("hitArea");
  const focusLine = document.getElementById("focusLine");
  const tooltip = document.getElementById("tooltip");
  const chart = document.getElementById("chart");

  const PAD_L = {PAD_L};
  const PLOT_W = {PLOT_W};

  hitArea.addEventListener("mousemove", (e) => {{
    const rect = chart.getBoundingClientRect();
    const mouseX = e.clientX - rect.left - PAD_L;
    if (mouseX < 0 || mouseX > PLOT_W) return;

    const dayIdx = Math.min(rawData.length - 1, Math.max(0, Math.round((mouseX / PLOT_W) * rawData.length)));
    const d = rawData[dayIdx];
    if (!d) return;

    const snapX = (dayIdx / rawData.length) * PLOT_W;
    focusLine.setAttribute("x1", snapX);
    focusLine.setAttribute("x2", snapX);
    focusLine.style.display = "block";

    tooltip.style.display = "block";
    tooltip.style.left = (e.clientX - rect.left) + "px";
    tooltip.style.top = (e.clientY - rect.top) + "px";
    
    const displayDate = d.date || `第 ${{dayIdx + 1}} 天`;
    tooltip.innerHTML = `
      <div style="font-weight:600; color:#38bdf8; margin-bottom:4px;">${{displayDate}}</div>
      <div><span style="color:#4ade80">● 月出:</span> ${{d.rise || '未升起'}}</div>
      <div><span style="color:#facc15">● 中天:</span> ${{d.trans || '未过中天'}}</div>
      <div><span style="color:#f87171">● 月落:</span> ${{d.set || '未落下'}}</div>
    `;
  }});

  hitArea.addEventListener("mouseleave", () => {{
    focusLine.style.display = "none";
    tooltip.style.display = "none";
  }});
</script>
</body>
</html>
"""

with open("out/moon_interactive.html", "w", encoding="utf-8") as out:
    out.write(html_content)

print("✨ 优化完成，已生成现代交互式图表: out/moon_interactive.html")