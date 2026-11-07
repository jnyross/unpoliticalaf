"""Compare two spans of years (for example 2009 to 2011 with 2017 to 2019), and
choose default and suggested comparisons in which every topic has a figure.

A span's figure is the plain average of its yearly figures. It is calculated
only when every year in the span has a figure measured the same way: a span
with a missing year or a change of definition inside it gets no average, and
the page says why. Averages are recorded as calculated facts with their
formula, so the checks recalculate them like every other derived figure.
"""

from .data import Fact, YEARS
from .html import FOLD, page, details_table, source_line, esc
from . import pages_life as L

SPAN = 3  # years in each span
# The pandemic disrupted travel and several surveys in these years, so the
# default and suggested comparisons never start or end in them (or, for spans,
# include them). Readers can still choose them.
DISRUPTED = (2020, 2021)
# Already published as an average of three survey years, so averaging again
# would mix overlapping data; these stay on the single-year comparisons.
SKIP = ("house.crowd.",)
# Sources whose record page would grow too large with the averages added: the
# averages are recorded on a second page for the same file (sources.FETCHED_ALIASES).
AVG_SOURCE = {"nomis-ashe-places": "nomis-ashe-places-2"}


def spans():
    return [(s, s + SPAN - 1) for s in YEARS if s + SPAN - 1 <= YEARS[-1]]


def span_pairs():
    return [(a, b) for a in spans() for b in spans() if b[0] > a[1]]


def short(sp):
    """(2009, 2011) -> '2009–11'."""
    return f"{sp[0]}–{str(sp[1])[2:]}"


def long(sp):
    return f"{sp[0]} to {sp[1]}"


def slug(a, b):
    return f"{a[0]}-{a[1]}-and-{b[0]}-{b[1]}"


def avg_id(m, sp):
    return f"avg.{m[0]}.{sp[0]}-{sp[1]}"


def _years(sp):
    return range(sp[0], sp[1] + 1)


def ranged(m):
    return not m[0].startswith(SKIP)


def add_range_facts(facts):
    """Add the average for every measure and span where it can be calculated."""
    for m in L.MEAS:
        if not ranged(m):
            continue
        mkey, topic, label, fid, kind, style, period, group = m
        for sp in spans():
            ids = [fid(y) for y in _years(sp)]
            if any(L._val(facts, i) is None for i in ids):
                continue
            if group and len({group(y) for y in _years(sp)}) > 1:
                continue
            last = facts[ids[-1]]
            facts.add(
                Fact(
                    avg_id(m, sp),
                    sum(facts[i].value for i in ids) / len(ids),
                    last.unit,
                    f"average of {period(sp[0])} to {period(sp[1])}",
                    AVG_SOURCE.get(last.source, last.source),
                    ", ".join(facts[i].locator for i in ids),
                    "calculated",
                    formula=f"({' + '.join(ids)}) ÷ {len(ids)}",
                    inputs=ids,
                )
            )


def span_status(facts, m, a, b):
    """'ok', 'missing' or 'break' for one measure and two spans."""
    if not ranged(m) or avg_id(m, a) not in facts or avg_id(m, b) not in facts:
        return "missing"
    group = m[7]
    if group and group(a[0]) != group(b[0]):
        return "break"
    return "ok"


def span_reason(facts, m, sp):
    """Why a span has no average for this measure, in plain words."""
    if not ranged(m):
        return "it is already published as an average of three survey years, so it is compared only on the single-year pages"
    for y in _years(sp):
        if L._val(facts, m[3](y)) is None:
            return f"there is no figure for {y}: {L.missing_reason(m[0], y)}"
    return f"the definition changed within {long(sp)}. {L.BREAK_REASONS[m[7]]}"


# ------------------------------------------------------------ default pairs


def full_pair(facts, a, b):
    """True when every topic's lead figure can be compared between a and b (years or spans)."""
    for key, _, _ in L.TOPICS:
        m = next(x for x in L.MEAS if x[0] == L.KEY_MEASURES[key][0])
        st = span_status(facts, m, a, b) if isinstance(a, tuple) else L._status(facts, m, a, b)
        if st != "ok":
            return False
    return True


def default_years(facts):
    """The earliest and latest years in which every topic's lead figure can be compared."""
    ok = [y for y in YEARS if y not in DISRUPTED]
    pairs = [(a, b) for a in ok for b in ok if a < b and full_pair(facts, a, b)]
    return min(pairs, key=lambda p: (p[0] - p[1], p[0]))


def suggested_years(facts):
    """The default pair, then its latest year against 10 and 5 years before, where every topic is filled."""
    a, b = default_years(facts)
    out = [(a, b)]
    for gap in (10, 5):
        x = b - gap
        if x > a and x not in DISRUPTED and full_pair(facts, x, b):
            out.append((x, b))
    return out


def default_spans(facts):
    """The earliest and latest spans, clear of the pandemic years, in which every topic's lead figure can be compared."""
    ok = [sp for sp in spans() if not any(y in DISRUPTED for y in _years(sp))]
    pairs = [(a, b) for a in ok for b in ok if b[0] > a[1] and full_pair(facts, a, b)]
    return min(pairs, key=lambda p: (p[0][0] - p[1][0], p[0][0]))


def pair_context(a, b, brief=False):
    """Where a suggested pair sits in the economic cycle, so a reader knows what the
    two ends have in common. Said whatever the figures show."""
    notes = []
    if 2009 <= a <= 2012:
        notes.append(
            f"{a} came soon after the 2008-09 recession, when the employment rate was near its lowest for these years"
        )
    if b == 2019:
        notes.append(f"{b} was the last year before the pandemic")
    if not notes:
        return ""
    if brief:
        return (
            " Both years fall between the 2008-09 recession and the pandemic, so this pair shows that stretch only."
            if len(notes) == 2
            else " " + notes[0][:1].upper() + notes[0][1:] + "."
        )
    return (
        " "
        + "; ".join(notes)[:1].upper()
        + "; ".join(notes)[1:]
        + ". So this pair shows that stretch, not the whole period: "
        "each topic page has every year, and each comparison page gives the longer run."
    )


DEFAULT_RULE = (
    "Suggested comparisons are chosen by a fixed rule, not by what the figures show: the earliest and latest years "
    "in which all five topics have a comparable lead figure, leaving out 2020 and 2021, when the pandemic disrupted travel and several surveys."
)


# ------------------------------------------------------------------- pages


def _bars(facts, num, m, a, b):
    fa, fb = avg_id(m, a), avg_id(m, b)
    top = max(L._val(facts, fa), L._val(facts, fb)) or 1
    out = []
    for sp, f, cls in ((a, fa, "cmp-a"), (b, fb, "cmp-b")):
        w = max(0.0, 100 * L._val(facts, f) / top)
        out.append(
            f'<div class="cmp-bar cmp-span"><span class="cmp-y">{short(sp)}</span><span class="cmp-track" aria-hidden="true"><span class="cmp-fill {cls}" style="width:{w:.1f}%"></span></span>'
            f'<span class="cmp-v">{num(f, m[4])}</span></div>'
        )
    return "".join(out)


def _change(facts, num, m, a, b):
    fa, fb = avg_id(m, a), avg_id(m, b)
    va, vb = L._val(facts, fa), L._val(facts, fb)
    v = (vb - va) if m[5] in ("pp", "abs") else 100 * (vb / va - 1)
    return v, L.change_cell(facts, num, fa, fb, m[5], m[4])


def _periods(m, a, b):
    return f"{m[6](a[0])} to {m[6](a[1])}, and {m[6](b[0])} to {m[6](b[1])}"


def _not_compared(facts, m, a, b):
    if span_status(facts, m, a, b) == "break":
        return L.BREAK_REASONS[m[7]]
    for sp in (a, b):
        if avg_id(m, sp) not in facts or not ranged(m):
            return f"No average for {long(sp)}, because {span_reason(facts, m, sp)}"
    return ""


def key_sentence(facts, num, topic, a, b):
    mkey, subject = L.KEY_MEASURES[topic]
    m = next(x for x in L.MEAS if x[0] == mkey)
    if span_status(facts, m, a, b) == "ok":
        v, ch = _change(facts, num, m, a, b)
        verb = (
            "went up from"
            if v > 0.049
            else ("went down from" if v < -0.049 else "was about the same:")
        )
        sep = "and" if abs(v) < 0.05 else "to"
        return f"<p>{esc(subject)} {verb} an average of {num(avg_id(m, a), m[4])} in {long(a)} {sep} {num(avg_id(m, b), m[4])} in {long(b)}." f"{(' Change: ' + ch + '.') if abs(v) >= 0.05 else ''}</p>" + _bars(
            facts, num, m, a, b
        ) + L.long_run(
            facts, num, m, int(b[1]), f"../../{topic}.html"
        )
    means = L.not_compared_means(topic, span_status(facts, m, a, b))
    return f"<p>{esc(subject)}: <strong>not compared</strong>. {esc(_not_compared(facts, m, a, b))}{esc(means)}</p>"


def largest_changes(facts, num, a, b, n=3):
    titles = dict((t[0], t[1]) for t in L.TOPICS)
    ok = [m for m in L.MEAS if not m[0].endswith("cash") and span_status(facts, m, a, b) == "ok"]
    out = []
    for style, title in (
        ("pp", "Shares, in percentage points"),
        ("pct", "Money and numbers, in per cent"),
    ):
        ranked = sorted(
            (m for m in ok if m[5] == style), key=lambda m: -abs(_change(facts, num, m, a, b)[0])
        )[:n]
        items = []
        for m in ranked:
            _, ch = _change(facts, num, m, a, b)
            items.append(
                f'<li><a href="#{m[1]}">{esc(titles[m[1]])}</a>: {esc(m[2])}, {num(avg_id(m, a), m[4])} → {num(avg_id(m, b), m[4])} ({ch})</li>'
            )
        if items:
            out.append(f'<h3>{title}</h3><ol class="cmp-top">{"".join(items)}</ol>')
    return "".join(out)


def span_form(up, a=None, b=None):
    def opts(sel):
        return "".join(
            f'<option value="{sp[0]}"{" selected" if sp == sel else ""}>{long(sp)}</option>'
            for sp in spans()
        )

    return f"""<form class="pick" action="{up}index.html#all" method="get" data-compare-spans>
<label>First years <select name="from">{opts(a)}</select></label>
<label>Second years <select name="to">{opts(b)}</select></label>
<button type="submit">Compare</button>
<p class="small" role="status" data-span-msg></p></form>"""


SPAN_JS = f"""<script>
document.querySelectorAll('form[data-compare-spans]').forEach(function(f){{f.addEventListener('submit',function(e){{
var a=+f.elements.from.value,b=+f.elements.to.value,n={SPAN},lo=Math.min(a,b),hi=Math.max(a,b);
if(hi-lo<n){{e.preventDefault();f.querySelector('[data-span-msg]').textContent='Choose two sets of years that do not overlap.';return;}}
e.preventDefault();var base=f.getAttribute('action').replace(/index\\.html(#.*)?$/,'');
location.href=base+lo+'-'+(lo+n-1)+'-and-'+hi+'-'+(hi+n-1)+'.html';}});}});
</script>"""

SPAN_NOTE = (
    "Each figure is the average of the three yearly figures in that set of years. An average is worked out only when all three years "
    "have a figure measured the same way. Averaging several years smooths out one-off ups and downs and some sampling noise, "
    "but it can also hide a change that happened within those years."
)
MOE_NOTE = (
    "Margins of error are not shown for averages: these surveys interview some of the same people in neighbouring years, "
    "so a margin for an average cannot be worked out from the yearly margins that are published."
)


def span_page(facts, d, num, sources, a, b):
    up = "../../../"
    h = f"{long(a)} compared with {long(b)}"
    body = [f"<h1>{h}</h1>"]
    body.append(
        '<p><a href="index.html">Choose other years</a> · <a href="../index.html">Compare two single years</a></p>'
    )
    body.append('<h2 class="brief">In brief</h2>')
    body.append(
        '<p class="small">The same lead figure is shown for each topic on every comparison page, whichever way it moved.</p>'
    )
    for key, title, _ in L.TOPICS:
        body.append(
            f'<div class="cmp-key"><h3>{esc(title)}</h3>{key_sentence(facts, num, key, a, b)}</div>'
        )
    body.append(f'<p class="small">{esc(SPAN_NOTE)}</p>')
    top = largest_changes(facts, num, a, b)
    if top:
        body.append(f'<h2 id="largest">Largest changes between {long(a)} and {long(b)}</h2>')
        body.append(
            '<p class="small">Every average on this page that can be compared, ranked by the size of its change. Shares and amounts are ranked separately, because percentage points and per cent are different measures. Cash figures are left out, because the after-inflation figures are the like-for-like ones.</p>'
        )
        body.append(top)
    body.append(
        L.timing_note(
            sources,
            up,
            (long(a), range(int(a[0]), int(a[1]) + 1)),
            (long(b), range(int(b[0]), int(b[1]) + 1)),
        )
    )
    body.append(L.CAUSE)
    for key, title, scope in L.TOPICS:
        body.append(f'<h2 id="{key}">{esc(title)}</h2>')
        body.append(FOLD)
        body.append(f'<p class="small">{esc(scope)}</p>')
        ms = [m for m in L.MEAS if m[1] == key]
        ok = [m for m in ms if span_status(facts, m, a, b) == "ok" and not m[0].endswith("cash")]
        cards = []
        for m in ok:
            _, ch = _change(facts, num, m, a, b)
            cards.append(
                f'<li><p class="cmp-label">{esc(m[2])}</p>{_bars(facts, num, m, a, b)}'
                f'<p class="cmp-change">Change in the average: {ch} <span class="small">({esc(_periods(m, a, b))})</span></p></li>'
            )
        if cards:
            body.append(f'<ul class="cmp-list">{"".join(cards)}</ul>')
        notes = {}
        for m in ms:
            if span_status(facts, m, a, b) != "ok":
                notes.setdefault(_not_compared(facts, m, a, b), []).append(m)
        if notes:
            items = "".join(
                f'<li><p>{esc(reason)}.</p><p class="small">Not compared: {L._join_labels([m[2] for m in group])}.</p></li>'
                for reason, group in notes.items()
            )
            body.append(f'<h3>Not compared</h3><ul class="cmp-notes">{items}</ul>')
        rows = []
        na = '<span class="missing">no average</span>'
        for m in ms:
            fa, fb = avg_id(m, a), avg_id(m, b)
            st = span_status(facts, m, a, b)
            if st == "ok":
                ch = L.change_cell(facts, num, fa, fb, m[5], m[4])
            elif st == "break":
                ch = f'<span class="missing">not comparable: definition changed ({esc(m[7](a[0]))} → {esc(m[7](b[0]))})</span>'
            else:
                ch = '<span class="missing">not compared</span>'
            rows.append(
                [
                    esc(m[2]),
                    num(fa, m[4]) if fa in facts else na,
                    num(fb, m[4]) if fb in facts else na,
                    ch,
                ]
            )
        body.append(
            details_table(
                f"Show the full {esc(title.lower())} table",
                f"{title}: average of {long(a)} and of {long(b)}",
                ["Measure", long(a), long(b), "Change"],
                rows,
            )
        )
        body.append(
            f'<details class="limit"><summary>Limits of the {esc(title.lower())} figures</summary><p>{esc(L.TOPIC_LIMITS[key])}</p></details>'
        )
        ids = [s for s in L.TOPIC_SOURCES[key] if s in sources]
        ids += [AVG_SOURCE[s] for s in ids if AVG_SOURCE.get(s) in sources]
        body.append(source_line(sources, ids, up=up))
    body.append('<h2 id="other">Compare other years</h2>')
    body.append(span_form("", a, b))
    body.append(
        f'<p class="small">{esc(MOE_NOTE)} Changes in percentages are shown in percentage points; changes in money and counts as a percentage of the earlier average; class sizes in pupils. '
        f'To see margins of error, compare <a href="../{a[0]}-{b[1]}.html">{a[0]} with {b[1]}</a> or other single years.</p>'
    )
    return page(
        f"life/compare/spans/{slug(a, b)}.html",
        h,
        "\n".join(body),
        f"Average work, pay, housing, holidays and class sizes in {long(a)} compared with {long(b)}.",
        scripts=SPAN_JS,
    )


def span_index(facts):
    a, b = default_spans(facts)
    body = [
        "<h1>Compare two sets of years</h1>",
        f"<p>Compare the average of three years with the average of three other years, for example {long(a)} with {long(b)}. "
        "Averages smooth out one-off ups and downs in a single year.</p>",
        span_form("", a, b),
        '<p class="small">Without JavaScript the button opens the list of every comparison below.</p>',
        f'<div class="answer"><p><a href="{slug(a, b)}.html">Start with {long(a)} compared with {long(b)}</a>: '
        "the earliest and latest sets of years in which all five topics can be compared.</p>"
        '<p class="small">This suggestion is chosen by a fixed rule, not by what the figures show: the earliest and latest sets of years in which all five topics '
        "have a comparable lead figure, leaving out sets that include 2020 or 2021, when the pandemic disrupted travel and several surveys. "
        "Sets of years that include 2024 or later cannot be compared for holidays abroad, because the survey changed in 2024.</p></div>",
        f'<p class="small">{esc(SPAN_NOTE)}</p>',
        "<h2 id='all'>All comparisons</h2>",
        '<p class="small">Comparisons marked “all five topics” have a comparable lead figure for every topic.</p>',
    ]
    for x in spans():
        links = []
        for y in spans():
            if y[0] > x[1]:
                tag = (
                    ' <span class="small">(all five topics)</span>'
                    if full_pair(facts, x, y)
                    else ""
                )
                links.append(f'<li><a href="{slug(x, y)}.html">{long(y)}</a>{tag}</li>')
        if links:
            body.append(f'<h3>{long(x)} with…</h3><ul class="spanlist">{"".join(links)}</ul>')
    body.append(L.CAUSE)
    return page(
        "life/compare/spans/index.html",
        "Compare two sets of years",
        "\n".join(body),
        "Compare average work, pay, housing, holidays and class sizes in the UK between two sets of years.",
        scripts=SPAN_JS,
    )
