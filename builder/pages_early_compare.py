"""Comparison pages for pairs of years where at least one is before 2008.

Fewer official figures reach back before 2008, so these pages use only the longer
series in pages_history.LONG. A change is worked out only when both years have a
figure measured the same way; otherwise the page says which year is missing or
which definition changed, and why.
"""

from .data import YEARS, EARLY_YEARS
from .html import page, details_table, source_line, esc
from . import pages_life as L
from . import pages_history as H

ALL = EARLY_YEARS + YEARS

# The lead measure for each topic, in order of preference: the first that both
# years can compare is used in "In brief".
LEAD = {
    "work": [("work.rate", "The share of people aged 16 to 64 in work")],
    "earnings": [("earn.ft", "Median full-time weekly pay, after inflation,")],
    "housing": [
        ("house.lfs.private", "The share of households in England renting privately"),
        (
            "house.afford",
            "Median house prices compared with median full-time earnings in England and Wales",
        ),
    ],
    "holidays": [("hol.ips.per100", "Visits abroad for any purpose, per 100 UK residents,")],
    "schools": [("school.primary", "The average primary school class in England")],
}


def pairs():
    """Every pair of years with at least one before 2008."""
    return [(a, b) for a in EARLY_YEARS for b in ALL if b > a]


def _m8(m):
    return m[:8]


def _first(facts, m):
    return next((y for y in ALL if H._has(facts, m[3](y))), None)


def missing_reason(facts, m, y):
    """Why a long-run measure has no figure for year y, in plain words."""
    key, end = m[0], m[8]
    first = _first(facts, m)
    if first is not None and y < first:
        return f"these figures start in {first}"
    if end is not None and y > end:
        if key.startswith("house.lfs."):
            return "the Labour Force Survey tenure figures end in 2008, and later years come from a different survey (the English Housing Survey)"
        if key.startswith("hol.ips."):
            return (
                "this series of visits abroad stops at 2023, because a new method started in 2024"
            )
    if key.startswith("house.lfs.") and y < 1992:
        return "before 1992 tenure was measured only in 1981, 1984, 1988 and 1991"
    return f"there is no figure for {y} in the tables used here"


def status(facts, m, a, b):
    return L._status(facts, _m8(m), a, b)


def break_reason(m, a, b):
    return L.short_break(m[7], a, b)


def not_compared(facts, m, a, b):
    st = status(facts, m, a, b)
    if st == "break":
        return break_reason(m, a, b)
    y = next(y for y in (a, b) if not H._has(facts, m[3](y)))
    return f"No figure for {y}: {missing_reason(facts, m, y)}."


def nearest(facts, m, a, b):
    """The closest other pair of years that can be compared for this measure, if any."""
    have = [y for y in ALL if H._has(facts, m[3](y))]
    best = None
    for i, x in enumerate(have):
        for z in have[i + 1 :]:
            if (x, z) == (a, b) or status(facts, m, x, z) != "ok":
                continue
            dist = abs(x - a) + abs(z - b)
            if best is None or dist < best[0]:
                best = (dist, x, z)
    return None if best is None else best[1:]


def _near_link(facts, num, m, a, b, topic):
    return L.near_sentence(facts, num, _m8(m), nearest(facts, m, a, b), topic)


def lead_sentence(facts, num, topic, a, b):
    """One plain sentence for the topic's lead measure, or why it cannot be compared."""
    options = [(next(m for m in H.LONG if m[0] == k), subject) for k, subject in LEAD[topic]]
    m, subject = next(((m, s) for m, s in options if status(facts, m, a, b) == "ok"), options[0])
    fa, fb = m[3](a), m[3](b)
    if status(facts, m, a, b) == "ok":
        v, ch = L._change(facts, num, _m8(m), a, b)
        same = abs(v) < 0.05
        verb = "was about the same:" if same else ("went up from" if v > 0 else "went down from")
        return f"<p>{esc(subject)} {verb} {num(fa, m[4])} ({esc(m[6](a))}) {'and' if same else 'to'} {num(fb, m[4])} ({esc(m[6](b))})." f"{'' if same else ' Change: ' + ch + '.'}</p>" + L._pair_bars(
            facts, num, _m8(m), a, b
        ) + L.long_run(
            facts, num, _m8(m), b, f"../{topic}.html"
        )
    means = L.not_compared_means(topic, status(facts, m, a, b))
    return f"<p>{esc(subject.rstrip(','))}: <strong>not compared</strong>. {esc(not_compared(facts, m, a, b))}{esc(means)}{_near_link(facts, num, m, a, b, topic)}</p>"


def _rows(facts, num, topic, a, b):
    rows, ok = [], 0
    na = "<span class='missing'>no figure</span>"
    for m in H.LONG:
        if m[1] != topic:
            continue
        fa, fb = m[3](a), m[3](b)
        if not (H._has(facts, fa) or H._has(facts, fb)):
            continue
        st = status(facts, m, a, b)
        if st == "ok":
            ch = L.change_cell(facts, num, fa, fb, m[5], m[4])
            ok += 1
        elif st == "break":
            ch = f'<span class="missing">not comparable: definition changed ({esc(m[7](a))} → {esc(m[7](b))})</span>'
        else:
            why = not_compared(facts, m, a, b)[:-1]
            ch = f'<span class="missing">not compared: {esc(why[0].lower() + why[1:])}</span>'
        rows.append(
            [
                esc(m[2]),
                num(fa, m[4]) if H._has(facts, fa) else na,
                num(fb, m[4]) if H._has(facts, fb) else na,
                ch,
            ]
        )
    return rows, ok


def compare_page(facts, d, num, sources, a, b):
    up = "../../"
    body = [f"<h1>{a} compared with {b}</h1>"]
    body.append(
        f'<p><a href="../{a}.html">Everyday life in {a}</a> · <a href="../{b}.html">Everyday life in {b}</a> · <a href="index.html">Choose two other years</a></p>'
    )
    body.append(
        f'<div class="answer"><p>Fewer official figures reach back to {a}. This page compares those that do, and works out a change only where '
        f"both years were measured the same way. Where a figure is missing or its definition changed, it says so.</p></div>"
    )
    body.append('<h2 class="brief">In brief</h2>')
    body.append(
        '<p class="small">The same lead figure is shown for each topic, whichever way it moved. Each figure covers its own period, shown in brackets.</p>'
    )
    for key, title, _ in L.TOPICS:
        body.append(
            f'<div class="cmp-key"><h3>{esc(title)}</h3>{lead_sentence(facts, num, key, a, b)}</div>'
        )
    body.append(L.timing_note(sources, up, (str(a), [a]), (str(b), [b])))
    body.append(L.CAUSE)
    for key, title, _ in L.TOPICS:
        body.append(f'<h2 id="{key}">{esc(title)}</h2>')
        rows, ok = _rows(facts, num, key, a, b)
        ms = [m for m in H.LONG if m[1] == key]
        gap = next((y for y in (a, b) if not any(H._has(facts, m[3](y)) for m in ms)), None)
        if gap is not None:
            # One of the years has no figure at all for this topic: say why once, not row by row.
            m = next(m for m in ms if m[0] == LEAD[key][0][0])
            body.append(
                f'<p class="missing">Not available: no {esc(title.lower())} figure for {gap}, because {esc(missing_reason(facts, m, gap))}.</p>'
            )
            link = _near_link(facts, num, m, a, b, key)
            if link:
                body.append(f'<p class="small">{link.strip()}</p>')
        else:
            body.append(
                f'<p class="small">{ok} of {len(rows)} figures can be compared between {a} and {b}.</p>'
            )
            body.append(
                details_table(
                    f"Show the {esc(title.lower())} table",
                    f"{title}: {a} and {b}",
                    ["Measure", str(a), str(b), "Change"],
                    rows,
                )
            )
        body.append(
            f'<details class="limit"><summary>Limits of the {esc(title.lower())} figures before 2008</summary><p>{esc(H.LIMITS[key])}</p></details>'
        )
        body.append(
            f'<p class="small"><a href="../{key}.html#{H.ANCHOR}">{esc(title)} in every year since {H.FIRST_YEAR[key]}</a></p>'
        )
        body.append(source_line(sources, [s for s in H.SOURCES[key] if s in sources], up=up))
    body.append('<h2 id="other">Compare other years</h2>')
    body.append(L.compare_form("../", a, b))
    body.append(
        '<p class="small">Changes in percentages are shown in percentage points: a rise from 20% to 25% is +5 percentage points. Changes in money and counts are shown as a percentage of the earlier year. Class sizes change in pupils.</p>'
    )
    return page(
        f"life/compare/{a}-{b}.html",
        f"{a} compared with {b}",
        "\n".join(body),
        f"The official figures on work, pay, housing, travel abroad and class sizes that reach back to {a}, compared with {b} where they were measured the same way.",
        scripts=L.COMPARE_JS,
    )
