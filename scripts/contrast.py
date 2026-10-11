"""WCAG contrast check for the design tokens (static/src/tokens.css). Run: python scripts/contrast.py"""
import re, sys
css = open("static/src/tokens.css", encoding="utf-8").read()

def block(sel):
    m = re.search(re.escape(sel) + r"\s*\{(.*?)\n\}", css, re.S)
    return dict((k, tuple(map(int, v.split()))) for k, v in re.findall(r"--([a-z-]+):\s*(\d+ \d+ \d+);", m.group(1)))

def lum(c):
    f = lambda v: (v / 255 / 12.92) if v / 255 <= 0.03928 else (((v / 255 + 0.055) / 1.055) ** 2.4)
    r, g, b = map(f, c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

themes = {"dark": block(':root,\n:root[data-theme="dark"]'), "light": block(':root[data-theme="light"]')}
text_pairs = [("text-primary", "bg-base", 7), ("text-primary", "bg-raised", 7), ("text-secondary", "bg-base", 4.5), ("text-secondary", "bg-raised", 4.5),
              ("text-secondary", "bg-sunken", 4.5), ("accent-water", "bg-raised", 4.5), ("accent-laterite", "bg-raised", 4.5), ("accent-leaf", "bg-raised", 4.5),
              ("signal-skip", "bg-raised", 4.5), ("signal-watch", "bg-raised", 4.5), ("signal-stress", "bg-raised", 4.5),
              ("on-accent", "accent-laterite", 4.5), ("on-accent", "accent-water", 4.5)]
bad = 0
for name, t in themes.items():
    print(f"\n{name}")
    for fg, bg, need in text_pairs:
        r = ratio(t[fg], t[bg]); ok = r >= need; bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {fg:16s} on {bg:16s} {r:5.2f}  (need {need})")
sys.exit(1 if bad else 0)
