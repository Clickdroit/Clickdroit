import urllib.request
import re
from datetime import datetime

url = 'https://github.com/users/Clickdroit/contributions'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
except Exception as e:
    print("Fetch error:", e)
    html = ""

pattern = r'<td[^>]*data-date="([^"]+)"[^>]*data-level="([0-9])"'
matches = re.findall(pattern, html)
print(f"Matched {len(matches)} days")

# Colors for modern developer dark theme (Tokyonight / Slate / Cyan)
level_colors = [
    "#161e2e",  # 0: Empty slot (slate/dark navy)
    "#1e3a8a",  # 1: Low (dark blue)
    "#2563eb",  # 2: Medium (blue)
    "#7c3aed",  # 3: High (purple)
    "#38bdf8"   # 4: Highest (bright cyan glow)
]

level_strokes = [
    "#222f44",
    "#2563eb",
    "#3b82f6",
    "#a78bfa",
    "#7dd3fc"
]

# Grid setup: 53 columns x 7 days
# Group days into columns of 7
days_data = matches[-371:] if len(matches) >= 371 else matches
# We want exactly 53 columns * 7 days = 371 days
if len(days_data) < 371:
    padding = [("", "0")] * (371 - len(days_data))
    days_data = padding + days_data

cols = []
for c in range(53):
    col_days = days_data[c*7 : (c+1)*7]
    cols.append(col_days)

# Month label heuristics
month_labels = [
    (0, "Oct"), (4, "Nov"), (9, "Dec"), (13, "Jan"), (17, "Feb"),
    (22, "Mar"), (26, "Apr"), (31, "May"), (35, "Jun"), (39, "Jul"),
    (44, "Aug"), (48, "Sep")
]

svg_lines = []
svg_lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 160" width="100%" height="100%">')
svg_lines.append('  <defs>')
svg_lines.append('    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">')
svg_lines.append('      <stop offset="0%" stop-color="#0a0f1d" />')
svg_lines.append('      <stop offset="100%" stop-color="#0d1322" />')
svg_lines.append('    </linearGradient>')
svg_lines.append('  </defs>')
svg_lines.append('  <style>')
svg_lines.append('    @keyframes colAppear {')
svg_lines.append('      0% { opacity: 0; transform: translateY(6px) scale(0.6); }')
svg_lines.append('      70% { opacity: 1; transform: translateY(-1px) scale(1.1); }')
svg_lines.append('      100% { opacity: 1; transform: translateY(0) scale(1); }')
svg_lines.append('    }')
svg_lines.append('    .col {')
svg_lines.append('      animation: colAppear 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards;')
svg_lines.append('      opacity: 0;')
svg_lines.append('    }')
svg_lines.append('    .text-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; font-size: 13px; font-weight: 600; fill: #cbd5e1; }')
svg_lines.append('    .text-muted { font-family: "SF Mono", Consolas, monospace; font-size: 10px; fill: #64748b; }')

for c in range(53):
    delay_ms = int(c * 22)
    svg_lines.append(f'    .col-{c} {{ animation-delay: {delay_ms}ms; }}')

svg_lines.append('  </style>')

# Container background
svg_lines.append('  <rect width="880" height="160" rx="12" fill="url(#bg)" stroke="#1e293b" stroke-width="1.2" />')

# Header
svg_lines.append('  <g transform="translate(30, 26)">')
svg_lines.append('    <circle cx="6" cy="6" r="4" fill="#38bdf8" />')
svg_lines.append('    <circle cx="6" cy="6" r="8" fill="#38bdf8" fill-opacity="0.25" />')
svg_lines.append('    <text x="22" y="10" class="text-title">Contribution Calendar</text>')
svg_lines.append('    <text x="180" y="10" class="text-muted">• Activity &amp; Commit History</text>')
svg_lines.append('  </g>')

# Month labels
x_start = 65
y_grid = 60
for col_idx, m_name in month_labels:
    x_pos = x_start + (col_idx * 14.5)
    svg_lines.append(f'  <text x="{x_pos:.1f}" y="{y_grid - 8}" class="text-muted">{m_name}</text>')

# Day labels
day_labels = [(1, "Mon"), (3, "Wed"), (5, "Fri")]
for r_idx, d_name in day_labels:
    y_pos = y_grid + (r_idx * 11.5) + 8
    svg_lines.append(f'  <text x="32" y="{y_pos:.1f}" class="text-muted">{d_name}</text>')

# The Grid of Rectangles
tile_size = 9.5
step_x = 14.5
step_y = 11.5

for c_idx, col in enumerate(cols):
    svg_lines.append(f'  <g class="col col-{c_idx}">')
    for r_idx, (date_str, level_str) in enumerate(col):
        lvl = int(level_str) if level_str.isdigit() else 0
        lvl = min(lvl, 4)
        fill_col = level_colors[lvl]
        stroke_col = level_strokes[lvl]
        rx_pos = x_start + (c_idx * step_x)
        ry_pos = y_grid + (r_idx * step_y)
        svg_lines.append(f'    <rect x="{rx_pos:.1f}" y="{ry_pos:.1f}" width="{tile_size}" height="{tile_size}" rx="2" fill="{fill_col}" stroke="{stroke_col}" stroke-width="0.8" />')
    svg_lines.append('  </g>')

# Legend at bottom right
svg_lines.append('  <g transform="translate(680, 145)">')
svg_lines.append('    <text x="0" y="8" class="text-muted">Less</text>')
for i in range(5):
    lx = 32 + (i * 13)
    svg_lines.append(f'    <rect x="{lx}" y="0" width="9" height="9" rx="2" fill="{level_colors[i]}" stroke="{level_strokes[i]}" stroke-width="0.8" />')
svg_lines.append('    <text x="104" y="8" class="text-muted">More</text>')
svg_lines.append('  </g>')

svg_lines.append('</svg>')

svg_content = "\n".join(svg_lines)

import os
output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "contributions.svg")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(svg_content)

print(f"Generated {output_path} successfully ({len(svg_content)} bytes)")
