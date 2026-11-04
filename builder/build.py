"""Build the static site into site/.

Usage: python -m builder.build
"""
import hashlib
import json
import shutil
import sys
from collections import Counter

from .data import build_all, YEARS, EARLY_YEARS
from .html import Num, page
from .readers import ROOT
from .sources import all_sources, verify_hashes
from .explain import missing_quotes
from .rates import read_rates
from . import pages_money_extra, pages_generations, pages_manifesto, version
from . import pages_options, downloads, pages_money, pages_top_earners, pages_spendhist, pages_taxmixhist, pages_life, pages_history, pages_early_compare, pages_home, pages_ranges, pages_intl, pages_borrow, pages_debt, pages_defence, pages_immigration, glossary, trace, uncertainty

OUT = ROOT / "site"
# The product spec requires every page to be under 500,000 bytes. Reading pages
# (everything except the figure records) have a tighter limit so they stay quick
# on a phone; a page that grows past it should be split, as the life explorer was.
MAX_PAGE_BYTES = 400_000
MAX_READING_PAGE_BYTES = 260_000


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
    pages_ranges.add_range_facts(facts)
    pages_life.DEFAULT_PAIR[:] = pages_ranges.default_years(facts)
    pages_life.SUGGESTED[:] = pages_ranges.suggested_years(facts)
    num = Num(facts)
    pages = {}
    # Order matters: pages that derive facts come before pages that use them.
    pages["spending.html"] = pages_money.spending_page(facts, d, num, sources)
    pages["spending-areas.html"] = pages_money.spending_areas_page(facts, d, num, sources)
    pages["spending-history.html"] = pages_spendhist.spending_history_page(facts, d, num, sources)
    pages["taxes.html"] = pages_money.taxes_page(facts, d, num, sources)
    pages["tax-history.html"] = pages_taxmixhist.tax_history_page(facts, d, num, sources)
    pages["international.html"] = pages_intl.international_page(facts, d, num, sources)
    pages["borrowing.html"] = pages_borrow.borrowing_page(facts, d, num, sources)
    pages["why-debt.html"] = pages_debt.why_debt_page(facts, d, num, sources)
    pages["manifesto.html"] = pages_manifesto.manifesto_page()
    pages["defence.html"] = pages_defence.defence_page(facts, d, num, sources)
    pages["immigration.html"] = pages_immigration.immigration_page(facts, d, num, sources)
    pages["economy-options.html"] = pages_options.options_page()
    pages["who-pays.html"] = pages_money.who_pays_page(facts, d, num, sources)
    pages["who-pays-age.html"] = pages_money_extra.income_tax_age_page(facts, d, num, sources)
    pages["who-pays-households.html"] = pages_money_extra.households_page(facts, d, num, sources)
    pages["high-earners.html"] = pages_top_earners.high_earners_page(facts, d, num, sources)
    pages["household-tax.html"] = pages_money.household_tax_page(facts, d, num, sources, rates)
    pages["index.html"] = pages_home.home_page(facts, d, num, sources)
    pages["life/index.html"] = pages_life.life_index(facts, d, num, sources)
    for key, _, _ in pages_life.TOPICS:
        pages[f"life/{key}.html"] = pages_life.topic_page(facts, d, num, sources, key)
    pages["life/jobs-by-industry.html"] = pages_life.industry_page(facts, d, num, sources)
    pages["life/house-prices.html"] = pages_life.afford_page(facts, d, num, sources)
    pages["life/housing-places.html"] = pages_life.places_page(facts, d, num, sources)
    pages[pages_generations.PAGE] = pages_generations.generations_page(facts, d, num, sources)
    for y in YEARS:
        pages[f"life/{y}.html"] = pages_life.year_page(facts, d, num, sources, y)
    for y in EARLY_YEARS:
        pages[f"life/{y}.html"] = pages_history.early_year_page(facts, d, num, sources, y)
    for a in YEARS:
        for b in YEARS:
            if a < b:
                pages[f"life/compare/{a}-{b}.html"] = pages_life.compare_page(facts, d, num, sources, a, b)
    for a, b in pages_early_compare.pairs():
        pages[f"life/compare/{a}-{b}.html"] = pages_early_compare.compare_page(facts, d, num, sources, a, b)
    pages["life/compare/index.html"] = pages_life.compare_index(sources)
    for a, b in pages_ranges.span_pairs():
        pages[f"life/compare/spans/{pages_ranges.slug(a, b)}.html"] = pages_ranges.span_page(facts, d, num, sources, a, b)
    pages["life/compare/spans/index.html"] = pages_ranges.span_index(facts)
    # The old single life page moved to life/index.html; keep the address working.
    moved = page("life.html", "Everyday life, year by year", '<h1>This page has moved</h1><p><a href="life/index.html">Go to Everyday life, year by year</a>.</p>')
    pages["life.html"] = moved.replace("<head>", '<head>\n<meta http-equiv="refresh" content="0; url=life/index.html">', 1)
    used = Counter(facts[f].source for f in num.used)
    pages["methods.html"] = pages_home.methods_page(facts, sources, used)
    pages["sources.html"] = pages_home.sources_page(sources, used)
    pages["uncertainty.html"] = uncertainty.uncertainty_page(facts, d, num, sources, YEARS[-1])
    pages["glossary.html"] = glossary.glossary_page()
    pages["corrections.html"] = trace.corrections_page()
    pages.update(trace.figure_pages(facts, sources, num.used))
    pages = {path: glossary.link_terms(html, path) for path, html in pages.items()}
    pages = {path: trace.add_trace(html, path, facts, sources) for path, html in pages.items()}
    return facts, sources, pages, num


BUILD_RECORD = "build.json"


def write_build_record():
    """Write site/build.json: the commit built and a SHA-256 for every file served.

    scripts/check_live.py compares this with the live site to show whether the
    live pages are exactly the latest build.
    """
    files = {}
    for p in sorted(OUT.rglob("*")):
        rel = p.relative_to(OUT).as_posix()
        if p.is_file() and rel != BUILD_RECORD:
            files[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    record = {"commit": version.commit(), "files": files}
    (OUT / BUILD_RECORD).write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")


def main():
    facts, sources, pages, num = render()
    if OUT.exists():
        shutil.rmtree(OUT)
    for path, html in pages.items():
        size = len(html.encode())
        limit = MAX_PAGE_BYTES if path.startswith(trace.FIG_DIR + "/") else MAX_READING_PAGE_BYTES
        if size > limit:
            raise SystemExit(f"{path} is {size:,} bytes, over the {limit:,} limit")
        p = OUT / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html, encoding="utf-8")
    for path, text in downloads.FILES.items():
        p = OUT / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="")
    (OUT / "data").mkdir(exist_ok=True)
    (OUT / "data/facts.json").write_text(json.dumps({"sources": sources, "facts": facts.to_json()}, ensure_ascii=False, indent=1), encoding="utf-8")
    shutil.copy(ROOT / "assets/icon.svg", OUT / "icon.svg")
    write_build_record()
    print(f"Built {len(pages)} pages, {len(downloads.FILES):,} CSV downloads, {len(facts):,} facts ({len(num.used):,} shown) into {OUT.relative_to(ROOT)}/")
    if num.absent:
        print(f"{len(num.absent)} requested figures do not exist and are shown as 'not available', e.g. {sorted(num.absent)[:8]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
