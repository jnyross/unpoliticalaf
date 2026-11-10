"""Question routes must reach visible answers, not just strings in closed folds."""

from html.parser import HTMLParser

import pytest

from builder import html, pages_options, pages_questions, trace, uncertainty
from builder.build import render


class DefaultText(HTMLParser):
    """Collect text outside closed disclosures, styles and scripts."""

    def __init__(self, markup):
        super().__init__()
        self.details = []
        self.ignored = 0
        self.text = []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        if tag == "details":
            self.details.append("open" in dict(attrs))
        if tag in ("script", "style"):
            self.ignored += 1

    def handle_endtag(self, tag):
        if tag == "details":
            self.details.pop()
        if tag in ("script", "style"):
            self.ignored -= 1

    def handle_data(self, data):
        if not self.ignored and all(self.details):
            self.text.append(data)


@pytest.fixture(scope="module")
def pages():
    saved_margins, saved_info = dict(uncertainty.MARGINS), dict(uncertainty.INFO)
    try:
        _, _, result, _ = render()
        return result
    finally:
        uncertainty.MARGINS.clear()
        uncertainty.MARGINS.update(saved_margins)
        uncertainty.INFO.clear()
        uncertainty.INFO.update(saved_info)


@pytest.mark.parametrize(
    "limitation",
    [
        "The site does not estimate what a wealth tax or a change to Capital Gains Tax would raise each year",
        "The site does not show the share of all taxes paid by the top 1%, because the official survey covers Income Tax only",
    ],
)
def test_who_pays_scope_is_visible_without_opening_a_fold(pages, limitation):
    visible = " ".join(" ".join(DefaultText(pages["who-pays.html"]).text).split())
    assert limitation in visible


def test_questions_reach_economy_options_answer():
    assert "economy-options.html" in html.QUESTION_PAGES
    assert 'href="economy-options.html#answer"' in pages_questions.questions_page()
    markup = pages_options.options_page()
    assert '<div class="answer" id="answer">' in markup
    visible = " ".join(DefaultText(markup).text)
    for context in ("baseline potential GDP", "10 years", "25 years", "model"):
        assert context in visible


def test_withdrawal_correction_link_targets_the_entry(pages):
    href = "corrections.html#household-tax-withdrawal"
    assert f'href="{href}">Read the correction</a>' in pages["who-pays.html"]
    correction = trace.corrections_page()
    entry = correction.split('id="household-tax-withdrawal"', 1)[1].split("</section>", 1)[0]
    assert "6 November 2026" in entry
    assert "46.0%" in entry


def test_folded_fragments_get_shared_progressive_enhancement():
    body = '<h1>Test</h1><details><summary>More</summary><h3 id="target">Target</h3></details>'
    markup = html.page("life/example.html", "Test", body)
    assert html.OPEN_TARGET_JS in markup
    assert "hashchange" in html.OPEN_TARGET_JS
    assert "parentElement" in html.OPEN_TARGET_JS
    assert "<summary>More</summary>" in markup
