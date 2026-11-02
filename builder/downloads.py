"""A "Download this data (CSV)" link beside every chart and table.

page() calls add_links on each reading page before the page is folded. Each
table, chart and bar list gets a CSV file under csv/, holding the same figures
the page shows, written as they are shown (with their units). build.py writes
the files from FILES.

Charts carry their figures in their readout data (data-chart) or, for charts
without one, in a <!--csv:...--> comment that this module removes.
"""
import csv
import io
import json
import re
from html import unescape

DIR = "csv"
FILES = {}  # site path -> CSV text

LINK_TEXT = "Download this data (CSV)"

_COMMENT = re.compile(r"<!--csv:(.*?)-->", re.S)
_TABLE = re.compile(r'<div class="tablewrap"[^>]*><table>(.*?)</table></div>', re.S)
_FIGURE = re.compile(r"<figure\b[^>]*>(.*?)</figure>", re.S)
_LIST = re.compile(r'<ul class="(bars(?: change)?|cmp-list)">(.*?)</ul>', re.S)
_HEADING = re.compile(r"<h[2-4]\b[^>]*>(.*?)</h[2-4]>", re.S)


def chart_data(names, rows):
    """A comment that carries a chart's figures to its CSV file. Removed before the page is written."""
    text = json.dumps({"names": names, "rows": rows}, ensure_ascii=False, separators=(",", ":"))
    return "<!--csv:" + text.replace("--", "-\\u002d") + "-->"


def raw(v):
    """A number as plain text, without float noise; empty when there is no figure."""
    return "" if v is None else f"{v:.10g}"


def text(html):
    """Visible text of an HTML fragment, on one line."""
    html = re.sub(r'<span class="vh">.*?</span>', "", html, flags=re.S)
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", html)).split()).replace(" ,", ",").replace(" .", ".").replace("( ", "(").replace(" )", ")")


def slug(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:60].rstrip("-") or "data"


def to_csv(rows):
    out = io.StringIO()
    csv.writer(out, lineterminator="\r\n").writerows(rows)
    # A byte order mark, so spreadsheet programs read £ and – correctly
    return "﻿" + out.getvalue()


def table_rows(inner):
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", inner, re.S):
        rows.append([text(c) for c in re.findall(r"<t[hd]\b[^>]*>(.*?)</t[hd]>", tr, re.S)])
    return rows


def figure_rows(inner):
    m = re.search(r"data-chart='([^']*)'", inner)
    if m:
        d = json.loads(unescape(m.group(1)))
    else:
        c = _COMMENT.search(inner)
        if not c:
            return None
        d = json.loads(c.group(1))
    return [["Period"] + d["names"]] + [[str(r[0])] + [("" if v == "no figure" else v) for v in r[1:]] for r in d["rows"]]


def list_rows(kind, inner, caption=""):
    items = re.findall(r"<li>(.*?)</li>(?=<li>|$)", inner, re.S)
    if kind == "cmp-list":
        years = re.findall(r'<span class="cmp-y">(.*?)</span>', items[0], re.S)[:2] if items else []
        head = ["Measure"] + [text(y) for y in years] + ["Change"]
        rows = [head]
        for it in items:
            label = text((re.search(r'<p class="cmp-label">(.*?)</p>', it, re.S) or [None, ""])[1])
            vals = [text(v) for v in re.findall(r'<span class="cmp-v">(.*?)</span></div>', it, re.S)]
            ch = re.search(r'<p class="cmp-change">(.*?)</p>', it, re.S)
            change = re.sub(r"^Change:\s*", "", text(ch.group(1))) if ch else ""
            rows.append([label] + vals + [change])
        return rows
    rows = [["Group", caption or "Value"]]
    for it in items:
        lab = re.search(r'<div class="lab"><span>(.*?)</span><span>(.*?)</span></div>', it, re.S)
        if lab:
            sub = re.search(r'<div class="sub">(.*?)</div>', it, re.S)
            rows.append([text(lab.group(1)), text(lab.group(2))] + ([text(sub.group(1))] if sub else []))
    if any(len(r) == 3 for r in rows[1:]):
        rows[0].append("Note")
        rows = [rows[0]] + [r + [""] * (3 - len(r)) for r in rows[1:]]
    return rows


def add_links(body, path):
    """Add a CSV download beside every table, chart and bar list in a page body."""
    base = DIR + "/" + path[:-len(".html")]
    up = "../" * path.count("/")
    names = set()

    def link(title, rows):
        name = slug(title)
        k = 2
        while name in names:
            name = f"{slug(title)}-{k}"
            k += 1
        names.add(name)
        href = f"{base}/{name}.csv"
        FILES[href] = to_csv(rows)
        return f'<p class="dl"><a href="{up}{href}" download>{LINK_TEXT}</a></p>'

    def heading_before(pos):
        hs = list(_HEADING.finditer(body, 0, pos))
        return text(hs[-1].group(1)) if hs else "data"

    edits = []  # (element start, where the link goes, title, rows)
    for m in _TABLE.finditer(body):
        cap = re.search(r"<caption>(.*?)</caption>", m.group(1), re.S)
        rows = table_rows(m.group(1))
        if rows:
            edits.append((m.start(), m.end(), text(cap.group(1)) if cap else heading_before(m.start()), rows))
    figs = []
    for m in _FIGURE.finditer(body):
        figs.append((m.start(), m.end()))
        rows = figure_rows(m.group(1))
        if not rows:
            continue
        # Named after what the chart measures (the subtitle under a finding), which stays the same when figures are refreshed
        t = (re.search(r'<p class="csub"[^>]*>(.*?)</p>', m.group(1), re.S) or re.search(r'<p class="ctitle"[^>]*>(.*?)</p>', m.group(1), re.S)
             or re.search(r"<strong>(.*?)</strong>", m.group(1), re.S))
        title = text(t.group(1)) if t else heading_before(m.start())
        if rows[0][1:] == ["Value"]:
            rows[0][1] = title
        close = m.end() - len("</figure>")
        edits.append((m.start(), close, title, rows))
    for m in _LIST.finditer(body):
        if any(a <= m.start() < b for a, b in figs) or body[:m.start()].endswith('aria-hidden="true">'):
            continue  # part of a figure, or a decorative copy (home page cards) of a chart shown elsewhere
        before = body[max(0, m.start() - 1000):m.start()]
        cap = re.search(r'<p class="small">((?:(?!</p>).)*)</p>\s*$', before, re.S)
        rows = list_rows(m.group(1), m.group(2), text(cap.group(1)) if cap else "")
        if len(rows) > 1:
            edits.append((m.start(), m.end(), heading_before(m.start()), rows))
    # Names are given in page order; links are inserted from the end so earlier positions stay valid.
    links = [(at, link(title, rows)) for _, at, title, rows in sorted(edits, key=lambda e: e[0])]
    for at, new in sorted(links, key=lambda e: e[0], reverse=True):
        body = body[:at] + new + body[at:]
    return strip(body)


def strip(html):
    return _COMMENT.sub("", html)
