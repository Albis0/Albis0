#!/usr/bin/env python3
"""Draw the profile graphics from data/activity.json into assets/.

stdlib only. env TODAY=YYYY-MM-DD pins the date (previews, tests).
"""
import datetime as dt, html, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
A = json.load(open(os.path.join(ROOT, "data", "activity.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "assets")
TODAY = dt.date.fromisoformat(os.environ.get("TODAY") or dt.date.today().isoformat())
DAYS = {dt.date.fromisoformat(k): v for k, v in A["days"].items()}
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
CARD = dict(bg="#0d1117", edge="#30363d", bar="#161b22", text="#e6edf3", muted="#8b949e", dim="#484f58", accent="#58a6ff")


def write(name, svg):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote", name, len(svg))


# ------------------------------------------------------------------ numbers
def stats():
    total = sum(DAYS.values())
    first = min(DAYS)
    active = len(DAYS)
    best = max(DAYS.values())
    best_day = max(DAYS, key=DAYS.get)
    # streaks
    longest = cur = run = 0
    d = first
    while d <= TODAY:
        run = run + 1 if d in DAYS else 0
        longest = max(longest, run)
        d += dt.timedelta(days=1)
    d = TODAY if TODAY in DAYS else TODAY - dt.timedelta(days=1)
    while d in DAYS:
        cur += 1
        d -= dt.timedelta(days=1)
    months = (TODAY.year - first.year) * 12 + TODAY.month - first.month + 1
    start52 = TODAY - dt.timedelta(days=(TODAY.weekday() + 1) % 7) - dt.timedelta(weeks=52)
    win = {k: v for k, v in DAYS.items() if start52 <= k <= TODAY}
    return dict(total=total, first=first, active=active, best=best, best_day=best_day, longest=longest, cur=cur,
                months=months, repos=len(A["repos"]), start52=start52, win=win,
                win_total=sum(win.values()), win_active=len(win))


S = stats()


# ------------------------------------------------------------------ 3D skyline
def activity3d():
    U, V, GAP, HMAX = (14.0, 4.0), (-7.0, 6.0), 0.82, 92
    W, X0, Y0 = 830, 7 * 7.0 + 10, 92 + 8
    MAXC = max(S["win"].values())
    themes = {
        "dark": dict(base="#161b22", top=("#1f6feb", "#58a6ff", "#79c0ff", "#a5d6ff"), muted="#8b949e", text="#e6edf3"),
        "light": dict(base="#eaeef2", top=("#54aeff", "#218bff", "#0969da", "#0550ae"), muted="#656d76", text="#1f2328"),
    }

    def shade(c, f):
        h = c.lstrip("#"); r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        return "#%02x%02x%02x" % tuple(max(0, min(255, round(x * f))) for x in (r, g, b))

    def pt(w, d, h=0):
        return X0 + w * U[0] + d * V[0], Y0 + w * U[1] + d * V[1] - h

    poly = lambda pts: " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    weeks = ((TODAY - S["start52"]).days // 7) + 1
    for theme, t in themes.items():
        cells = []
        for w in range(weeks):
            for d in range(7):
                day = S["start52"] + dt.timedelta(days=w * 7 + d)
                if day <= TODAY:
                    cells.append((w, d, day, S["win"].get(day, 0)))
        cells.sort(key=lambda c: (c[0] * U[1] + c[1] * V[1], c[0]))
        body = []
        for w, d, day, c in cells:
            lv = -1 if c == 0 else (0 if c / MAXC < .08 else 1 if c / MAXC < .22 else 2 if c / MAXC < .5 else 3)
            gx = (1 - GAP) / 2
            a, b, cc, dd = (w + gx, d + gx), (w + 1 - gx, d + gx), (w + 1 - gx, d + 1 - gx), (w + gx, d + 1 - gx)
            h = 1.4 if lv < 0 else 5 + (HMAX - 5) * (c / MAXC) ** .62
            base = t["base"] if lv < 0 else t["top"][lv]
            P = lambda p, hh: pt(p[0], p[1], hh)
            body.append(
                f'<g class="b" style="animation-delay:{(w * .022 + d * .012):.2f}s"><g class="w" style="animation-delay:{1 + w * .09 + d * .03:.2f}s">'
                f'<polygon points="{poly([P(dd, h), P(cc, h), P(cc, 0), P(dd, 0)])}" fill="{shade(base, .68)}"/>'
                f'<polygon points="{poly([P(b, h), P(cc, h), P(cc, 0), P(b, 0)])}" fill="{shade(base, .5)}"/>'
                f'<polygon points="{poly([P(a, h), P(b, h), P(cc, h), P(dd, h)])}" fill="{base}"/></g></g>')
        labels, last = [], None
        for w in range(weeks):
            day = S["start52"] + dt.timedelta(days=w * 7)
            if day.month != last and day.day <= 7:
                x, y = pt(w, 7.6)
                labels.append(f'<text class="m" x="{x - 8:.1f}" y="{y + 13:.1f}">{day.strftime("%b")}</text>')
            last = day.month
        H = int(Y0 + 53 * U[1] + 7 * V[1] + 52)
        css = ("@keyframes rise{from{transform:translateY(14px);opacity:0}to{transform:none;opacity:1}}"
               "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}"
               ".b{animation:rise .7s cubic-bezier(.2,.8,.2,1) both}.w{animation:bob 6s ease-in-out infinite}"
               f".m{{font:500 11px {SANS};fill:{t['muted']}}}.k{{font:600 13px {SANS};fill:{t['text']}}}"
               "@media (prefers-reduced-motion:reduce){.b,.w{animation:none}}")
        write(f"activity-{theme}.svg",
              f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
              f'aria-label="Commit activity over the last 12 months as a 3D skyline: {S["win_total"]} commits on {S["win_active"]} days">'
              f'<style>{css}</style><g>{"".join(body)}</g>{"".join(labels)}'
              f'<text x="4" y="{H - 10}"><tspan class="k">{S["win_total"]:,} commits</tspan>'
              f'<tspan class="m" dx="10">on {S["win_active"]} days in the last 12 months</tspan></text></svg>\n')


# ------------------------------------------------------------------ terminal
def terminal():
    W, T, FS, CW, PX, PY, LH = 830, 22.0, 14, 8.4, 28, 70, 28
    P = "albis0@github"
    lines = [("whoami", "17 y/o developer, Türkiye"),
             ("git stats", f'{S["total"]:,} commits in {S["repos"]} repos, since {S["first"]}'),
             ("ls projects/", "ficsit-planner   yt2mp   glimpse   vavis"),
             ("cat stack.txt", "javascript  typescript  react  node  express  mongodb")]
    pct = lambda t: f"{t / T * 100:.3f}%"
    css = [f".t{{font:{FS}px {MONO}}}.ti{{font:500 12px {SANS}}}",
           "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.cur{animation:blink 1.05s steps(1) infinite}",
           "@media (prefers-reduced-motion:reduce){.a,.cur,.cg{animation:none!important}}"]
    body, y, t0 = [], PY, .7
    tail = f"{pct(T - 2.6)}{{opacity:1}}{pct(T - 1.7)}{{opacity:0}}100%{{opacity:0}}"
    for i, (cmd, out) in enumerate(lines):
        n = len(cmd) + len(P) + 3
        ts, te = t0, t0 + .05 * n + .25
        os_, oe = te + .25, te + .55
        css.append(f"@keyframes c{i}{{0%{{clip-path:inset(0 100% 0 0);opacity:1}}{pct(ts)}{{clip-path:inset(0 100% 0 0);animation-timing-function:steps({n},end)}}"
                   f"{pct(te)}{{clip-path:inset(0 0 0 0);opacity:1}}{pct(T - 2.6)}{{clip-path:inset(0 0 0 0);opacity:1}}{pct(T - 1.7)}{{clip-path:inset(0 0 0 0);opacity:0}}100%{{clip-path:inset(0 100% 0 0);opacity:0}}}}.c{i}{{animation:c{i} {T}s linear infinite}}")
        css.append(f"@keyframes o{i}{{0%{{opacity:0;transform:translateX(-6px)}}{pct(os_)}{{opacity:0;transform:translateX(-6px)}}{pct(oe)}{{opacity:1;transform:none}}{tail}}}.o{i}{{animation:o{i} {T}s linear infinite}}")
        body.append(f'<text class="t a c{i}" x="{PX}" y="{y}" xml:space="preserve"><tspan fill="#58a6ff">{P}</tspan><tspan fill="#8b949e">:~</tspan><tspan fill="#e6edf3"> $ </tspan><tspan fill="#e6edf3">{html.escape(cmd)}</tspan></text>')
        body.append(f'<text class="t a o{i}" x="{PX}" y="{y + LH * .78:.0f}" fill="{"#7ee787" if i == 1 else "#8b949e"}" xml:space="preserve">{html.escape(out)}</text>')
        y += LH * 1.75
        t0 = oe + .6
    css.append(f"@keyframes cg{{0%{{opacity:0}}{pct(t0)}{{opacity:0}}{pct(t0 + .1)}{{opacity:1}}{tail}}}.cg{{animation:cg {T}s linear infinite}}")
    body.append(f'<g class="cg"><text class="t" x="{PX}" y="{y}" xml:space="preserve"><tspan fill="#58a6ff">{P}</tspan><tspan fill="#8b949e">:~</tspan><tspan fill="#e6edf3"> $ </tspan></text>'
                f'<rect class="cur" x="{PX + (len(P) + 5) * CW + 2:.1f}" y="{y - FS + 2}" width="8" height="{FS + 2}" fill="#e6edf3"/></g>')
    H = int(y + 28)
    write("terminal.svg",
          f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Terminal: whoami, git stats, ls projects, cat stack.txt">'
          f'<style>{"".join(css)}</style><rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{CARD["bg"]}" stroke="{CARD["edge"]}"/>'
          f'<path d="M.5 10.5a10 10 0 0 1 10-10h{W - 21}a10 10 0 0 1 10 10V34H.5z" fill="{CARD["bar"]}"/><line x1=".5" y1="34" x2="{W - .5}" y2="34" stroke="{CARD["edge"]}"/>'
          f'<text class="ti" x="{W / 2}" y="22" text-anchor="middle" fill="{CARD["muted"]}">albis0 — zsh</text>{"".join(body)}</svg>\n')


# ------------------------------------------------------------------ stats card
def stats_card():
    W, H = 830, 214
    css = (f".l{{font:600 11px {SANS};letter-spacing:1.6px;fill:{CARD['muted']}}}.big{{font:700 46px {SANS};fill:{CARD['text']}}}"
           f".s{{font:500 13px {SANS};fill:{CARD['muted']}}}.n{{font:500 13px {SANS};fill:{CARD['text']}}}.c{{font:500 12px {SANS};fill:{CARD['muted']}}}"
           f".mo{{font:500 10px {SANS};fill:{CARD['muted']}}}"
           "@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}@keyframes slide{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
           ".bar{transform-box:fill-box;transform-origin:50% 100%;animation:grow .8s cubic-bezier(.2,.8,.2,1) both}"
           ".hb{transform-box:fill-box;transform-origin:0 50%;animation:slide .9s cubic-bezier(.2,.8,.2,1) both}"
           "@media (prefers-reduced-motion:reduce){.bar,.hb{animation:none}}")
    o = [f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{CARD["bg"]}" stroke="{CARD["edge"]}"/>',
         '<text class="l" x="28" y="34">COMMITS</text><text class="l" x="292" y="34">PER MONTH</text><text class="l" x="636" y="34">MOST ACTIVE PROJECTS</text>',
         f'<text class="big" x="26" y="92">{S["total"]:,}</text>',
         f'<text class="s" x="28" y="124">{S["active"]} active days</text>',
         f'<text class="s" x="28" y="146">best streak {S["longest"]} days</text>',
         f'<text class="s" x="28" y="168">busiest day {S["best"]} commits</text>']
    # last 12 calendar months
    months = []
    y_, m_ = TODAY.year, TODAY.month
    for _ in range(12):
        months.append((y_, m_)); m_ -= 1
        if m_ == 0: y_, m_ = y_ - 1, 12
    months.reverse()
    counts = [sum(v for k, v in DAYS.items() if (k.year, k.month) == ym) for ym in months]
    mx = max(counts) or 1
    for i, ((yy, mm), c) in enumerate(zip(months, counts)):
        x = 292 + i * 27
        h = max(2, 96 * c / mx)
        fill = CARD["accent"] if i == 11 else "#1f6feb"
        o.append(f'<rect class="bar" x="{x}" y="{174 - h:.1f}" width="18" height="{h:.1f}" rx="3" fill="{fill}" style="animation-delay:{i * .05:.2f}s"><title>{dt.date(yy, mm, 1):%b %Y}: {c}</title></rect>')
        o.append(f'<text class="mo" x="{x + 9}" y="192" text-anchor="middle">{dt.date(yy, mm, 1):%b}</text>')
    # top public, non-fork projects
    top = [r for r in A["repos"] if r["public"] and not r["fork"] and r["name"]][:4]
    mxr = top[0]["commits"] if top else 1
    for i, r in enumerate(top):
        y = 62 + i * 36
        name = r["name"].replace("_", "-").lower() if r["name"] != "Vavis" else "vavis"
        o.append(f'<text class="n" x="636" y="{y + 13}">{html.escape(name)}</text><text class="c" x="802" y="{y + 13}" text-anchor="end">{r["commits"]}</text>')
        o.append(f'<rect x="636" y="{y + 20}" width="166" height="4" rx="2" fill="#21262d"/>'
                 f'<rect class="hb" x="636" y="{y + 20}" width="{166 * r["commits"] / mxr:.1f}" height="4" rx="2" fill="{CARD["accent"]}" style="animation-delay:{.2 + i * .1:.1f}s"/>')
    write("stats.svg", f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
          f'aria-label="{S["total"]:,} commits, {S["active"]} active days, best streak {S["longest"]} days"><style>{css}</style>{"".join(o)}</svg>\n')


# ------------------------------------------------------------------ trophies
def trophies():
    W, CWD, GAPX, H = 830, 130, 10, 156
    GOLD, SILVER, BRONZE, NONE = "#e3b341", "#b1bac4", "#d08b52", "#484f58"
    items = [("COMMITS", S["total"], f'{S["total"]:,}', "all time", (1000, 500, 100)),
             ("ACTIVE DAYS", S["active"], str(S["active"]), "days with a commit", (150, 75, 30)),
             ("STREAK", S["longest"], f'{S["longest"]} days', "longest in a row", (14, 7, 3)),
             ("BUSIEST DAY", S["best"], str(S["best"]), f'commits on {S["best_day"]:%b %d}', (50, 25, 10)),
             ("PROJECTS", S["repos"], str(S["repos"]), "repos with commits", (20, 10, 5)),
             ("EXPERIENCE", S["months"], f'{S["months"]} mo', f'since {S["first"]:%b %Y}', (12, 6, 3))]
    css = (f".l{{font:600 10px {SANS};letter-spacing:1.5px;fill:{CARD['muted']}}}.v{{font:700 22px {SANS};fill:{CARD['text']}}}"
           f".c{{font:500 11px {SANS};fill:{CARD['muted']}}}.r{{font:700 11px {SANS}}}"
           "@keyframes up{from{transform:translateY(10px);opacity:0}to{transform:none;opacity:1}}.card{animation:up .6s cubic-bezier(.2,.8,.2,1) both}"
           "@keyframes glow{0%,100%{opacity:.10}50%{opacity:.2}}.glow{animation:glow 4s ease-in-out infinite}"
           "@media (prefers-reduced-motion:reduce){.card,.glow{animation:none}}")
    o = []
    for i, (label, val, shown, cap, (g, s, b)) in enumerate(items):
        col, rank = (GOLD, "S") if val >= g else (SILVER, "A") if val >= s else (BRONZE, "B") if val >= b else (NONE, "C")
        x = i * (CWD + GAPX)
        o.append(
            f'<g class="card" style="animation-delay:{i * .08:.2f}s" transform-origin="0 0"><g transform="translate({x},0)">'
            f'<rect x=".5" y=".5" width="{CWD - 1}" height="{H - 1}" rx="10" fill="{CARD["bg"]}" stroke="{CARD["edge"]}"/>'
            f'<text class="l" x="{CWD / 2}" y="26" text-anchor="middle">{label}</text>'
            f'<circle class="glow" cx="{CWD / 2}" cy="62" r="30" fill="{col}" style="animation-delay:{i * .4:.1f}s"/>'
            f'<g transform="translate({CWD / 2 - 20},42) scale(1)" fill="{col}">'
            f'<path d="M10 4h20v10a10 10 0 0 1-20 0z"/><path d="M10 7H4.5a5 5 0 0 0 5.5 8M30 7h5.5a5 5 0 0 1-5.5 8" fill="none" stroke="{col}" stroke-width="2.4" stroke-linecap="round"/>'
            f'<rect x="18" y="23" width="4" height="7"/><rect x="12" y="30" width="16" height="4" rx="1.5"/></g>'
            f'<text class="r" x="{CWD / 2}" y="57" text-anchor="middle" fill="{CARD["bg"]}">{rank}</text>'
            f'<text class="v" x="{CWD / 2}" y="112" text-anchor="middle">{html.escape(shown)}</text>'
            f'<text class="c" x="{CWD / 2}" y="134" text-anchor="middle">{html.escape(cap)}</text></g></g>')
    write("trophies.svg", f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
          f'aria-label="Trophies: {S["total"]:,} commits, {S["active"]} active days, {S["longest"]} day streak">'
          f'<style>{css}</style>{"".join(o)}</svg>\n')


# ------------------------------------------------------------------ snake
def snake():
    PITCH, CELL, BODY, DUR = 14, 11, 9, 30.0
    weeks = ((TODAY - S["start52"]).days // 7) + 1
    W, H, X0, Y0 = 830, 7 * PITCH + 72, (830 - weeks * PITCH) / 2, 34
    mx = max(S["win"].values())
    themes = {"dark": dict(base="#161b22", lv=("#0e4429", "#006d32", "#26a641", "#39d353"), body="#58a6ff", muted="#8b949e"),
              "light": dict(base="#eaeef2", lv=("#9be9a8", "#40c463", "#30a14e", "#216e39"), body="#0969da", muted="#656d76")}
    # path: column by column, down then up
    order, pts = {}, []
    for w in range(weeks):
        rows = range(7) if w % 2 == 0 else range(6, -1, -1)
        for r in rows:
            order[(w, r)] = len(pts)
            pts.append((X0 + w * PITCH + CELL / 2, Y0 + r * PITCH + CELL / 2))
    L = (len(pts) - 1) * PITCH
    B = BODY * PITCH
    total_t = DUR * (L + B) / L
    for theme, t in themes.items():
        css, cells = [], []
        css.append("@media (prefers-reduced-motion:reduce){.sn,.e{animation:none!important}}")
        for w in range(weeks):
            for r in range(7):
                day = S["start52"] + dt.timedelta(days=w * 7 + r)
                if day > TODAY: continue
                c = S["win"].get(day, 0)
                x, y = X0 + w * PITCH, Y0 + r * PITCH
                if c == 0:
                    cells.append(f'<rect x="{x:.1f}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{t["base"]}"/>'); continue
                lv = 0 if c / mx < .08 else 1 if c / mx < .22 else 2 if c / mx < .5 else 3
                k = order[(w, r)]
                tk = k * PITCH / (L + B) * total_t
                p0, p1 = tk / total_t * 100, min(99.2, tk / total_t * 100 + .5)
                css.append(f"@keyframes e{k}{{0%,{p0:.2f}%{{opacity:1;transform:scale(1)}}{p1:.2f}%,97%{{opacity:.12;transform:scale(.7)}}100%{{opacity:1;transform:scale(1)}}}}.e{k}{{animation:e{k} {total_t:.2f}s linear infinite;transform-box:fill-box;transform-origin:center}}")
                cells.append(f'<rect class="e e{k}" x="{x:.1f}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{t["lv"][lv]}"/>')
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        css.append(f"@keyframes mv{{from{{stroke-dashoffset:{B}}}to{{stroke-dashoffset:{-L}}}}}"
                   f".sn{{stroke-dasharray:{B} 999999;animation:mv {total_t:.2f}s linear infinite}}")
        css.append(f".m{{font:500 11px {SANS};fill:{t['muted']}}}")
        write(f"snake-{theme}.svg",
              f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="A snake eating this year\'s commit squares">'
              f'<style>{"".join(css)}</style>{"".join(cells)}'
              f'<path class="sn" d="{d}" fill="none" stroke="{t["body"]}" stroke-width="{CELL - 1}" stroke-linecap="round" stroke-linejoin="round"/>'
              f'<text class="m" x="{X0}" y="{H - 14}">{S["win_total"]:,} commits, last 12 months</text></svg>\n')


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    activity3d(); terminal()
