import csv

WIDTH = 365 * 3
HEIGHT = 300

svg_lines = []
svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}">')

with open("data/moon-2026.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    day_index = 0
    for row in reader:
        # row["YYYY‑MM‑DD"] 日期
        rise_str = row["RISE"]
        trans_str = row["TRAN."]
        set_str = row["SET"]

        x = day_index * 3

        def time_to_y(timestr):
            if not timestr.strip():
                return None
            hh, mm = timestr.split(":")
            hours = int(hh) + int(mm)/60
            # y从顶部0到底部HEIGHT，24小时映射
            y = hours / 24 * HEIGHT
            return y

        y_rise = time_to_y(rise_str)
        y_trans = time_to_y(trans_str)
        y_set = time_to_y(set_str)

        if y_rise is not None:
            svg_lines.append(f'<circle cx="{x}" cy="{y_rise}" r="2" fill="#ffdd44"/>')
        if y_trans is not None:
            svg_lines.append(f'<circle cx="{x}" cy="{y_trans}" r="2" fill="#ffaa00"/>')
        if y_set is not None:
            svg_lines.append(f'<circle cx="{x}" cy="{y_set}" r="2" fill="#ffee77"/>')

        day_index +=1

svg_lines.append("</svg>")

with open("moon.svg","w",encoding="utf‑8") as out:
    out.write("\n".join(svg_lines))

print("saved moon.svg")
