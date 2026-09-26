import urllib.request
import re
import os
import json
import glob
import subprocess
from collections import Counter
from datetime import datetime

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, "data")
cache_file = os.path.join(data_dir, "local_contributions.json")
output_svg = os.path.join(base_dir, "assets", "contributions.svg")

# 1. Load existing cache if available
date_counts = Counter()
if os.path.exists(cache_file):
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            for d, c in saved_data.items():
                date_counts[d] = int(c)
    except Exception as e:
        print("Cache read error:", e)

# 2. If running locally with access to E:\dev, scan all repositories
dev_dir = r"E:\dev"
if os.path.exists(dev_dir):
    print("Scanning local repositories in E:\\dev...")
    repos = [d for d in glob.glob(os.path.join(dev_dir, "*")) if os.path.isdir(os.path.join(d, ".git"))]
    for r in repos:
        # Ignore external forks
        if os.path.basename(r) == "VALORANT-rank-yoinker":
            continue
        try:
            out = subprocess.check_output(
                ["git", "-C", r, "log", "--date=short", "--pretty=format:%ad"],
                text=True, stderr=subprocess.DEVNULL
            )
            for line in out.splitlines():
                d = line.strip()
                if len(d) == 10 and d.count("-") == 2:
                    date_counts[d] += 1
        except Exception:
            pass

    # Save aggregated counts to cache so GitHub Actions can use it in CI
    os.makedirs(data_dir, exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(dict(date_counts), f, indent=2, sort_keys=True)
    print(f"Saved {len(date_counts)} dates to {cache_file} (total {sum(date_counts.values())} local commits)")

# 3. Fetch GitHub calendar grid structure (to align the exact 53 weeks)
url = "https://github.com/users/Clickdroit/contributions"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8")
except Exception as e:
    print("GitHub fetch error:", e)
    html = ""

pattern = r'<td[^>]*data-date="([^"]+)"[^>]*data-level="([0-9])"'
matches = re.findall(pattern, html)
print(f"Matched {len(matches)} days from GitHub calendar grid")

# We want exactly 53 columns * 7 days = 371 days
if len(matches) >= 371:
    days_grid = matches[-371:]
else:
    days_grid = matches

# 4. Map each day in the grid to its true combined contribution count
combined_days = []
total_annual_contributions = 0

for d_str, gh_level in days_grid:
    loc_count = date_counts.get(d_str, 0)
    gh_lvl = int(gh_level) if gh_level.isdigit() else 0
    
    # Calculate level based on total activity
    if loc_count > 0:
        total_annual_contributions += loc_count
        if loc_count == 1:
            lvl = 1
        elif loc_count <= 4:
            lvl = 2
        elif loc_count <= 9:
            lvl = 3
        else:
            lvl = 4
    elif gh_lvl > 0:
        total_annual_contributions += gh_lvl
        lvl = gh_lvl
    else:
        lvl = 0
        
    combined_days.append((d_str, lvl, loc_count))

print(f"Total annual contributions calculated: {total_annual_contributions}")

# Group into 53 columns
cols = []
for c in range(53):
    cols.append(combined_days[c*7 : (c+1)*7])

# Color palette (Tokyonight / Slate / Neon Blue & Purple)
level_colors = [
    "#161e2e",  # 0: Empty slot (slate/dark navy)
    "#1e3a8a",  # 1: Low (dark electric blue)
    "#2563eb",  # 2: Medium (blue)
    "#8b5cf6",  # 3: High (vivid purple)
    "#38bdf8"   # 4: Highest (bright cyan glow)
]

level_strokes = [
    "#222f44",
    "#2563eb",
    "#3b82f6",
    "#a78bfa",
    "#7dd3fc"
]

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
svg_lines.append('    .text-stat { font-family: "SF Mono", Consolas, monospace; font-size: 11px; font-weight: 600; fill: #38bdf8; }')

for c in range(53):
    delay_ms = int(c * 20)
    svg_lines.append(f'    .col-{c} {{ animation-delay: {delay_ms}ms; }}')

svg_lines.append('  </style>')

# Container background
svg_lines.append('  <rect width="880" height="160" rx="12" fill="url(#bg)" stroke="#1e293b" stroke-width="1.2" />')

# Header
svg_lines.append('  <g transform="translate(30, 26)">')
svg_lines.append('    <circle cx="6" cy="6" r="4" fill="#38bdf8" />')
svg_lines.append('    <circle cx="6" cy="6" r="8" fill="#38bdf8" fill-opacity="0.25" />')
svg_lines.append('    <text x="22" y="10" class="text-title">Contribution Calendar</text>')
svg_lines.append(f'    <text x="180" y="10" class="text-muted">• </text>')
svg_lines.append(f'    <text x="192" y="10" class="text-stat">{total_annual_contributions}+ Contributions</text>')
svg_lines.append('    <text x="350" y="10" class="text-muted">(Public &amp; Private Systems Engineering)</text>')
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

# Grid of Rectangles
tile_size = 9.5
step_x = 14.5
step_y = 11.5

for c_idx, col in enumerate(cols):
    svg_lines.append(f'  <g class="col col-{c_idx}">')
    for r_idx, (date_str, lvl, count) in enumerate(col):
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

os.makedirs(os.path.dirname(output_svg), exist_ok=True)
with open(output_svg, "w", encoding="utf-8") as f:
    f.write(svg_content)

print(f"Generated {output_svg} successfully ({len(svg_content)} bytes)")
