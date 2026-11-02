"""Build the static site into site/.

Usage: python -m builder.build
"""
import json
import shutil
import sys
from collections import Counter

from .data import build_all, YEARS
from .html import Num, page
from .readers import ROOT
from .sources import all_sources, verify_hashes
from .explain import missing_quotes
from .rates import read_rates
from . import pages_money, pages_life, pages_home, glossary, trace, uncertainty

OUT = ROOT / "site"
MAX_PAGE_BYTES = 400_000


def render():
    sources = all_sources()
    problems = verify_hashes(sources)
    if problems:
        raise SystemExit("Source files changed:\n" + "\n".join(problems))
    problems = missing_quotes(sources)
    if problems:
        raise SystemExit("Quoted explanations do not match their sources:\n" + "\n".join(problems))
    facts, d = build_all()
    uncertainty.add_facts(facts, d)
    rates = read_rates(sources)
    pages_life.init(d)
    num = Num(facts)
    pages = {}
    # Order matters: pages that derive facts come before pages that use them.
    pages["spending.html"] = pages_money.spending_page(facts, d, num, sources)
    pages["taxes.html"] = pages_money.taxes_page(facts, d, num, sources)
    pages["who-pays.html"] = pages_money.who_pays_page(facts, d, num, sources)
    pages["household-tax.html"] = pages_money.household_tax_page(facts, d, num, sources, rates)
    pages["index.html"] = pages_home.home_page(facts, d, num, sources)
    pages["life/index.html"] = pages_life.life_index(facts, d, num, sources)
    for y in YEARS:
        pages[f"life/{y}.html"] = pages_life.year_page(facts, d, num, sources, y)
    for a in YEARS:
        for b in YEARS:
            if a < b:
                pages[f"life/compare/{a}-{b}.html"] = pages_life.compare_page(facts, d, num, sources, a, b)
    pages["life/compare/index.html"] = pages_life.compare_index(sources)
    # The old single life page moved to life/index.html; keep the address working.
    moved = page("life.html", "Everyday life, year by year", '<h1>This page has moved</h1><p><a href="life/index.html">Go to Everyday life, year by year</a>.</p>')
    pages["life.html"] = moved.replace("<head>", '<head>\n<meta http-equiv="refresh" content="0; url=life/index.html">', 1)
    used = Counter(facts[f].source for f in num.used)
    pages["methods.html"] = pages_home.methods_page(facts, sources, used)
    pages["uncertainty.html"] = uncertainty.uncertainty_page(facts, d, num, sources, YEARS[-1])
    pages["glossary.html"] = glossary.glossary_page()
    pages["corrections.html"] = trace.corrections_page()
    pages.update(trace.figure_pages(facts, sources, num.used))
    pages = {path: glossary.link_terms(html, path) for path, html in pages.items()}
    pages = {path: trace.add_trace(html, path, facts, sources) for path, html in pages.items()}
    return facts, sources, pages, num


def main():
    facts, sources, pages, num = render()
    if OUT.exists():
        shutil.rmtree(OUT)
    for path, html in pages.items():
        size = len(html.encode())
        if size > MAX_PAGE_BYTES:
            raise SystemExit(f"{path} is {size:,} bytes, over the {MAX_PAGE_BYTES:,} limit")
        p = OUT / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html, encoding="utf-8")
    (OUT / "data").mkdir(exist_ok=True)
    (OUT / "data/facts.json").write_text(json.dumps({"sources": sources, "facts": facts.to_json()}, ensure_ascii=False, indent=1), encoding="utf-8")
    shutil.copy(ROOT / "assets/icon.svg", OUT / "icon.svg")
    print(f"Built {len(pages)} pages, {len(facts):,} facts ({len(num.used):,} shown) into {OUT.relative_to(ROOT)}/")
    if num.absent:
        print(f"{len(num.absent)} requested figures do not exist and are shown as 'not available', e.g. {sorted(num.absent)[:8]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
