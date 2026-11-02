"""Explanations quoted word for word from official publications.

The site's own text describes figures and does not say why they changed. Where
an official body (ONS, HMRC, a government department) has published its own
explanation, we quote it here, clearly attributed and linked, next to the
figures it explains.

Each quote must appear word for word in the publication's page, kept under
data/fetched/ (downloaded byte for byte by scripts/fetch_sources.py). The build
and builder.check both confirm this, so a quote cannot drift from its source.
"""
import html as _html
import re

from .html import esc
from .readers import ROOT

# id: question shown above the quote, source id (see sources.FETCHED), the
# publication's title and date, the passages quoted (each must appear in the
# source, and they are shown in this order), where it is shown, and for life
# topics the years it applies to on the year pages.
EXPLANATIONS = {
    # filled in below
}

_text_cache = {}

QUOTE_MARKS = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', " ": " ", "–": "-", "—": "-"})


def norm(s):
    """Collapse whitespace and typographic quotes and dashes so a quote can be matched in page text."""
    return re.sub(r"\s+", " ", s.translate(QUOTE_MARKS)).strip()


def page_text(path):
    """Visible text of a fetched HTML page, normalised."""
    if path not in _text_cache:
        raw = (ROOT / path).read_text(encoding="utf-8", errors="replace")
        raw = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", raw)
        raw = re.sub(r"<[^>]+>", " ", raw)
        _text_cache[path] = norm(_html.unescape(raw))
    return _text_cache[path]


def missing_quotes(sources):
    """List every quoted passage that cannot be found in its source file."""
    problems = []
    for key, e in EXPLANATIONS.items():
        s = sources.get(e["source"])
        if not s:
            problems.append(f"explanation {key}: source {e['source']} is not in the source registry")
            continue
        text = page_text(s["file"])
        for q in e["quote"]:
            if norm(q) not in text:
                problems.append(f"explanation {key}: quote not found in {s['file']}: {q[:80]!r}")
    return problems


def box(key, sources, up="", heading=None):
    """An attributed quote with its source. heading: an <h3>/<h4> level, or None for a bold question line."""
    e = EXPLANATIONS[key]
    s = sources[e["source"]]
    q = " … ".join(esc(p) for p in e["quote"])
    title = esc(e["question"])
    head = f'<{heading} class="q">{title}</{heading}>' if heading else f'<p class="q"><strong>{title}</strong></p>'
    return f'''<aside class="explain" aria-label="{esc(e['publisher'])} explanation">
{head}
<p class="who">In the words of the {esc(e['publisher'])}:</p>
<blockquote cite="{esc(s['page'])}"><p>“{q}”</p></blockquote>
<p class="src">Quoted word for word from <a href="{esc(s['page'])}">{esc(e['title'])}</a> ({esc(e['date'])}). {esc(e.get('note', 'Figures inside the quote are as the publisher gave them at the time and may since have been revised.'))} <a href="{up}methods.html#src-{esc(e['source'])}">Source record</a>.</p>
</aside>'''


def for_page(page, sources, up=""):
    return [box(k, sources, up) for k, e in EXPLANATIONS.items() if page in e.get("pages", ())]


def for_year(topic, year, sources, up=""):
    return [box(k, sources, up) for k, e in EXPLANATIONS.items() if e.get("topic") == topic and year in e.get("years", ())]
