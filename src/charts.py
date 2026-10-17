"""Render article visuals from small JSON specs embedded in the Markdown.

An article includes a visual with a fenced block:

    ```chart
    {"type": "bars", "title": "...", ...}
    ```

Types:
  bars    vertical bars, one or more series      categories, series[{name, values}], format
  ranges  horizontal low-high bars (timelines)   rows[{label, from, to, text}], max, unit
  matrix  options x situations                   columns[], rows[{label, cells[]}]
          cell: "yes", "no", "yes:note", "no:note", "=plain text", anything else = "it depends"
  steps   a numbered plan in stages              steps[{when, title, items[]}]

Every figure takes "title", "caption" (optional) and "source" (optional).
Colors come from the site stylesheet (classes prefixed "ch-").
"""
import html
import json

E = html.escape


def _fmt(v, fmt):
    if fmt == "usd":
        return f"${v:,.0f}"
    if fmt == "usdk":
        return f"${v/1000:,.0f}K"
    if fmt == "years":
        return f"{v:g} yrs"
    if fmt == "pct":
        return f"{v:g}%"
    return f"{v:,.0f}" if isinstance(v, (int, float)) and abs(v) >= 1000 else f"{v:g}"


def _figure(spec, inner, wide=False):
    cap = ""
    if spec.get("caption") or spec.get("source"):
        bits = []
        if spec.get("caption"):
            bits.append(E(spec["caption"]))
        if spec.get("source"):
            bits.append(f'<span class="chart-source">Source: {E(spec["source"])}</span>')
        cap = f"<figcaption>{' '.join(bits)}</figcaption>"
    cls = "chart" + (" chart-wide" if wide else "")
    return (f'<figure class="{cls}">\n<p class="chart-title">{E(spec["title"])}</p>\n'
            f"{inner}\n{cap}\n</figure>")


def bars(spec):
    cats, series, fmt = spec["categories"], spec["series"], spec.get("format", "")
    W, H, top, bottom, left, right = 720, 340, 36, 56, 16, 16
    plot_h = H - top - bottom
    vmax = max(v for s in series for v in s["values"]) * 1.12
    group_w = (W - left - right) / len(cats)
    n = len(series)
    bar_w = min(88, group_w * 0.7 / n)
    gap = 8 if n > 1 else 0
    parts = [f'<line class="ch-axis" x1="{left}" x2="{W-right}" y1="{top+plot_h}" y2="{top+plot_h}"/>']
    for ci, cat in enumerate(cats):
        cx = left + group_w * (ci + .5)
        total = n * bar_w + (n - 1) * gap
        for si, s in enumerate(series):
            v = s["values"][ci]
            h = plot_h * v / vmax
            x = cx - total / 2 + si * (bar_w + gap)
            y = top + plot_h - h
            parts.append(f'<rect class="ch-bar ch-s{si}" x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="3"/>')
            parts.append(f'<text class="ch-val" x="{x+bar_w/2:.1f}" y="{y-8:.1f}" text-anchor="middle">{E(_fmt(v, fmt))}</text>')
        parts.append(f'<text class="ch-cat" x="{cx:.1f}" y="{top+plot_h+26}" text-anchor="middle">{E(cat)}</text>')
    legend = ""
    if n > 1:
        legend = '<ul class="chart-legend">' + "".join(
            f'<li><span class="ch-key ch-s{i}"></span>{E(s["name"])}</li>' for i, s in enumerate(series)) + "</ul>"
    label = spec["title"] + ": " + "; ".join(
        f'{c} ' + ", ".join(f'{s["name"]} {_fmt(s["values"][i], fmt)}' for s in series) for i, c in enumerate(cats))
    svg = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{E(label)}" preserveAspectRatio="xMidYMid meet">'
           + "".join(parts) + "</svg>")
    return _figure(spec, legend + svg)


def ranges(spec):
    rows, vmax, unit = spec["rows"], spec["max"], spec.get("unit", "")
    W, row_h, left, right, top = 720, 54, 150, 24, 8
    H = top + row_h * len(rows) + 40
    plot_w = W - left - right
    x = lambda v: left + plot_w * v / vmax
    parts = []
    step = spec.get("tick", 6)
    t = 0
    while t <= vmax:
        parts.append(f'<line class="ch-grid" x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{top}" y2="{H-34}"/>')
        parts.append(f'<text class="ch-tick" x="{x(t):.1f}" y="{H-14}" text-anchor="middle">{t}</text>')
        t += step
    parts.append(f'<text class="ch-tick" x="{W-right}" y="{H-0}" text-anchor="end">{E(unit)}</text>')
    for i, r in enumerate(rows):
        y = top + i * row_h + 10
        parts.append(f'<text class="ch-cat" x="{left-14}" y="{y+21}" text-anchor="end">{E(r["label"])}</text>')
        x0, x1 = x(r["from"]), x(r["to"])
        parts.append(f'<rect class="ch-bar ch-s{i % 3}" x="{x0:.1f}" y="{y}" width="{max(x1-x0, 6):.1f}" height="30" rx="15"/>')
        tx = x1 + 10
        anchor = "start"
        if tx > W - 120:
            tx, anchor = x0 - 10, "end"
        parts.append(f'<text class="ch-val" x="{tx:.1f}" y="{y+21}" text-anchor="{anchor}">{E(r["text"])}</text>')
    label = spec["title"] + ": " + "; ".join(f'{r["label"]} {r["text"]}' for r in rows)
    svg = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{E(label)}" preserveAspectRatio="xMidYMid meet">'
           + "".join(parts) + "</svg>")
    return _figure(spec, svg)


def matrix(spec):
    icon = {"yes": ('<span class="mx mx-yes" aria-hidden="true">&#10003;</span>', "Yes"),
            "no": ('<span class="mx mx-no" aria-hidden="true">&#10005;</span>', "No")}
    head = "".join(f"<th scope=\"col\">{E(c)}</th>" for c in spec["columns"])
    body = []
    for r in spec["rows"]:
        cells = []
        for c in r["cells"]:
            key, _, note = c.partition(":")
            if c.startswith("="):
                txt = f'<span class="mx-text">{E(c[1:])}</span>'
            elif key in icon:
                mark, word = icon[key]
                txt = f'{mark}<span class="mx-word">{word}</span>' + (f' <span class="mx-note">{E(note)}</span>' if note else "")
            else:
                txt = f'<span class="mx mx-maybe" aria-hidden="true">~</span> <span class="mx-note">{E(c)}</span>'
            cells.append(f"<td>{txt}</td>")
        body.append(f'<tr><th scope="row">{E(r["label"])}</th>{"".join(cells)}</tr>')
    table = (f'<div class="table-wrap"><table class="matrix"><thead><tr><th></th>{head}</tr></thead>'
             f'<tbody>{"".join(body)}</tbody></table></div>')
    return _figure(spec, table)


def steps(spec):
    cols = []
    for i, s in enumerate(spec["steps"], 1):
        items = "".join(f"<li>{E(it)}</li>" for it in s["items"])
        cols.append(f'<li class="step-col"><span class="step-num">{i}</span>'
                    f'<p class="step-when">{E(s["when"])}</p><p class="step-title">{E(s["title"])}</p>'
                    f"<ul>{items}</ul></li>")
    return _figure(spec, f'<ol class="step-cols">{"".join(cols)}</ol>', wide=True)


RENDER = {"bars": bars, "ranges": ranges, "matrix": matrix, "steps": steps}


def render(block_text):
    spec = json.loads(block_text)
    return RENDER[spec["type"]](spec)
