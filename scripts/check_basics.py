"""Independent, offline checks for the bounded qualitative guidance modules.

No producer import. Pins are acquisition facts, not refreshed from the register.
Raises ValueError on invalid input; returns True on success. Page content outside
marked sections is not checked here. Fiscal tables keep their own validators.
"""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
# id, public URL, original length/hash, stored envelope length/hash
PINS = (
    ("income-tax", "https://www.gov.uk/income-tax", 86695, "0d2891b45e0cb8f2776ba06d62e112c92e5bb2479c06f2e4c15bd39b42d99c39", 92743, "806eb118ad06aa332b60838e1f67d6882e8ed31a9e7c730570b358a3f46e123a"),
    ("national-insurance", "https://www.gov.uk/national-insurance", 95069, "54c01cdf6a363b583e16e6a13e11c1a0cbf9812b88ca5914f6291bf1f91f42ee", 101712, "0c44195957f6d7f3e9281ff5764f3577000aaee62f7578bfc3150d01ba193b1d"),
    ("paye-remitter", "https://www.gov.uk/paye-for-employers", 101690, "e51a38793ec86ec99d487ff1999380b7abb06511edd01a436cb33eb14bef8c0e", 108510, "1b9a98597cba8c2060e0ae2dcc113e24bb6e66f92581f079fd134ac29520e8be"),
    ("scottish-powers", "https://www.gov.scot/policies/taxes/income-tax/", 32915, "42617815a40e6b3014ed06b2db8aae082b4229c7055b3fd0216d9269b4705229", 34741, "4bae9e3f2115c3b09659b2c9a9b17c745f7127cfbe2b1055b957101e5823bbcb"),
    ("vat", "https://www.gov.uk/how-vat-works", 87451, "6fb25ac7e89c3489d0e48128c172db28a28f66e02ef641ce56bb9a19148d4156", 93798, "6ecad5ab8a92e05da0d61b5e7f1f01878491e0a26f7d5fac08218790d770cb5c"),
    ("welsh-income-tax", "https://www.gov.uk/welsh-income-tax", 72627, "10ff63cd8a504459a7c5b6611759ba9a2ab86f9eefabfb76732165ed276664ff", 77943, "d1e8632fb81204a8ff03a72ab376c885eae62d50f0bbf295bc1e5db01b930279"),
    ("corporation-tax", "https://www.gov.uk/corporation-tax", 79009, "fa9276683b8e1ac2a3ef3fc6bf6f0c39267bdb0a0caef763bc490f5eb7c30dc8", 84497, "19041a45f1e13e84d4d3f156a8d63fd57029dbd76d0e33f35fdd7eb86cf5e37a"),
)


def _pinned_register():
    """Exact acquisition register layout, independently specified, including LF."""
    rows = []
    for name, url, length, digest, stored_length, stored_digest in PINS:
        file = f"data/tax-basics/raw/basics-{name}.html.json"
        common = {
            "url": url, "bytes": length, "sha256": digest,
            "publication_or_update_date": None,
            "format_status": "unchanged original official HTTP response body",
            "date_note": "Living guidance; no visible publication date established. Retrieved 2026-10-30. Do not adopt current rates for 2023/24.",
            "file": file, "stored_bytes": stored_length,
            "stored_sha256": stored_digest,
            "storage": "Lossless original_response UTF8 in ASCII JSON; original bytes unchanged when decoded.",
        }
        if name == "corporation-tax":
            common = {
                "file": file, "url": url, "bytes": length, "sha256": digest,
                "publication_or_update_date": None,
                "date_note": "Living guidance retrieved2026-10-30; no publication date established; use no current rates.",
                "format_status": "Complete unchanged original official HTTP response body stored losslessly.",
                "stored_bytes": stored_length, "stored_sha256": stored_digest,
                "storage": "Lossless original_response UTF8 in ASCII JSON; original bytes unchanged when decoded.",
            }
        rows.append(common)
    return (json.dumps({"schema_version": 1, "retrieved_date_utc": "2026-10-30", "sources": rows}, indent=2) + "\n").encode("utf-8")


PINNED_REGISTER_SHA256 = hashlib.sha256(_pinned_register()).hexdigest()

# Exact meaningful source-body quotes, NOT obtained from the producer mapping.
ANCHORS = {
    "income-tax": ("Overview", "Income Tax is a tax you pay on your income.", "You do not have to pay tax on all types of income.", "Income Tax allowances and reliefs", "Most people in the UK get a Personal Allowance of tax-free income."),
    "national-insurance": ("Overview", "You pay National Insurance contributions to qualify for certain benefits and the State Pension.", "Who pays National Insurance", "an employee earning more than £242 per week from one job", "self-employed and making a profit of more than £12,570 a year", "Your contributions are treated as having been paid to protect your National Insurance record.", "National Insurance classes", "The type you pay depends on your employment status and how much you earn."),
    "paye-remitter": ("Introduction to PAYE", "Deductions from their pay", "deduct tax and National Insurance for most employees.", "Reporting pay and deductions", "including an employer’s National Insurance contribution", "Paying HMRC", "You then have to pay HMRC, usually every month.", "system to collect Income Tax and National Insurance from employment."),
    "scottish-powers": ("Income Tax", "set the tax band thresholds (excluding the personal allowance) as well as the rates.", "This applies to all non-savings, non-dividend income of Scottish taxpayers", "HMRC is responsible for the collection and management of Scottish Income Tax"),
    "vat": ("Overview", "is a tax added to most products and services sold by VAT-registered businesses.", "Your responsibilities as a VAT-registered business", "If you’ve charged more VAT than you’ve paid, you must pay the difference to HMRC.", "What VAT is charged on", "goods or services that are exempt from VAT or are unaffected by VAT", "How much VAT you must charge", "classed as reduced or zero-rated"),
    "welsh-income-tax": ("Income Tax in Wales", "You pay Welsh Income Tax rates if you live in Wales. These rates have been set by the Welsh Government.", "Who pays the Welsh rates", "the same tax as the rest of the UK on dividends and savings interest.", "How you pay", "HMRC will add a ‘C’ to the start of your tax code"),
    "corporation-tax": ("Overview", "Corporation Tax is a tax your company or association pays to HM Revenue and Customs (HMRC) on profits", "Profits you pay Corporation Tax on", "Taxable profits for Corporation Tax include the money your company or association makes from:"),
}


# Actual visible heading identities, not strings found in prose/navigation. Some
# guide pages are retained only as URL-bound FAQ Question/Answer pairs below.
MAIN_HEADINGS = {
    "income-tax": (("h1", None, "Overview"), ("h2", "income-tax-allowances-and-reliefs", "Income Tax allowances and reliefs")),
    "national-insurance": (("h1", None, "Overview"), ("h2", "who-pays-national-insurance", "Who pays National Insurance"), ("h2", "national-insurance-classes", "National Insurance classes")),
    "paye-remitter": (("h1", None, "Introduction to PAYE"), ("h3", "deductions-from-their-pay", "Deductions from their pay"), ("h3", "reporting-pay-and-deductions", "Reporting pay and deductions"), ("h3", "paying-hmrc", "Paying HMRC")),
    "scottish-powers": (("h2", None, "Income Tax"),),
    "vat": (("h1", None, "Overview"), ("h2", "your-responsibilities-as-a-vat-registered-business", "Your responsibilities as a VAT-registered business")),
    "welsh-income-tax": (("h1", None, "Income Tax in Wales"), ("h2", "who-pays-the-welsh-rates", "Who pays the Welsh rates"), ("h2", "how-you-pay", "How you pay")),
    "corporation-tax": (("h1", None, "Overview"), ("h2", "profits-you-pay-corporation-tax-on", "Profits you pay Corporation Tax on")),
}
FAQ_HEADINGS = {
    "vat": (("What VAT is charged on", "https://www.gov.uk/how-vat-works/what-vat-charged-on", "goods or services that are exempt from VAT or are unaffected by VAT"),
            ("How much VAT you must charge", "https://www.gov.uk/how-vat-works/how-much-vat-you-must-charge", "classed as reduced or zero-rated")),
}
NI_PERIOD_QUOTES = (
    "an employee earning more than £242 per week from one job",
    "self-employed and making a profit of more than £12,570 a year",
)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _norm(text):
    return " ".join(text.split())


class _Official(HTMLParser):
    """Read visible main content and retained official structured article text."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.main = False
        self.script = None
        self.parts = []
        self.canonicals = []
        self.structured = []
        self.content = _Text()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "main":
            self.main = True
        if tag == "link" and a.get("rel") == "canonical":
            self.canonicals.append(a.get("href"))
        if tag == "script":
            self.script = [a.get("type"), []]
        if self.main and self.script is None:
            self.content.handle_starttag(tag, attrs)
        if self.main and tag in {"p", "h1", "h2", "h3", "li", "td", "th", "div"}:
            self.parts.append(" ")

    def handle_data(self, data):
        if self.script is not None:
            self.script[1].append(data)
        elif self.main:
            self.parts.append(data)
            self.content.handle_data(data)

    def handle_endtag(self, tag):
        if self.main and self.script is None:
            self.content.handle_endtag(tag)
        if tag == "script" and self.script is not None:
            if self.script[0] == "application/ld+json":
                self.structured.append(json.loads("".join(self.script[1])))
            self.script = None
        if self.main and tag in {"p", "h1", "h2", "h3", "li", "td", "th", "div"}:
            self.parts.append(" ")
        if tag == "main":
            self.main = False


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.headings, self.items = [], [], []
        self.heading, self.item = None, None

    def handle_data(self, data):
        self.parts.append(data)
        if self.heading is not None:
            self.heading[2].append(data)
        if self.item is not None:
            self.item.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in {"h1", "h2", "h3"}:
            self.heading = [tag, dict(attrs).get("id"), []]
        if tag == "li":
            self.item = []
        if tag in {"p", "li", "h1", "h2", "h3", "div", "td", "th"}:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if self.heading is not None and tag == self.heading[0]:
            level, ident, parts = self.heading
            self.headings.append((level, ident, _norm("".join(parts))))
            self.heading = None
        if tag == "li" and self.item is not None:
            self.items.append(_norm("".join(self.item)))
            self.item = None
        if tag in {"p", "li", "h1", "h2", "h3", "div", "td", "th"}:
            self.parts.append(" ")


def _article_parts(node):
    # GOV.UK retains complete guide-page text in FAQ acceptedAnswer blocks.
    if isinstance(node, dict):
        for key, value in node.items():
            if key in {"articleBody", "text"} and isinstance(value, str) and "<p" in value:
                parser = _Text()
                parser.feed(value)
                yield "".join(parser.parts)
            elif key not in {"description", "publisher", "about", "isPartOf"}:
                yield from _article_parts(value)
    elif isinstance(node, list):
        for value in node:
            yield from _article_parts(value)


def _faq_questions(node):
    if isinstance(node, list):
        for child in node:
            yield from _faq_questions(child)
    elif isinstance(node, dict):
        if node.get("@type") == "FAQPage":
            for question in node.get("mainEntity", []):
                if isinstance(question, dict) and question.get("@type") == "Question":
                    yield question
        # Do not accept arbitrary nested names, article metadata or descriptions.
        if "@graph" in node:
            yield from _faq_questions(node["@graph"])


def _validate_official(name, url, html):
    parser = _Official()
    parser.feed(html)
    parser.close()
    _require(parser.canonicals == [url], f"official canonical mismatch: {name}")
    for heading in MAIN_HEADINGS[name]:
        _require(parser.content.headings.count(heading) == 1,
                 f"missing or duplicate official heading: {name}: {heading}")
    for title, page_url, quote in FAQ_HEADINGS.get(name, ()):
        questions = [q for q in _faq_questions(parser.structured)
                     if q.get("name") == title and q.get("url") == page_url]
        _require(len(questions) == 1, f"missing or duplicate official FAQ heading: {name}: {title}")
        answer = questions[0].get("acceptedAnswer", {})
        _require(isinstance(answer, dict) and answer.get("@type") == "Answer"
                 and answer.get("url") == page_url and isinstance(answer.get("text"), str),
                 f"wrong official FAQ answer binding: {name}: {title}")
        content = _Text()
        content.feed(answer["text"])
        _require(quote in _norm("".join(content.parts)), f"missing official FAQ quote: {name}: {title}")
    if name == "national-insurance":
        for quote in NI_PERIOD_QUOTES:
            _require(parser.content.items.count(quote) == 1,
                     f"missing or duplicate official NI period quotation: {quote}")
    text = _norm(" ".join(parser.parts) + " " + " ".join(_article_parts(parser.structured)))
    for anchor in ANCHORS[name]:
        _require(anchor in text, f"missing official heading/quote: {name}: {anchor}")


def validate_sources(root=ROOT):
    root = Path(root)
    raw_register = (root / "data/tax-basics/sources.json").read_bytes()
    _require(hashlib.sha256(raw_register).hexdigest() == PINNED_REGISTER_SHA256, "source register hash changed")
    register = json.loads(raw_register)
    _require(register["retrieved_date_utc"] == "2026-10-30" and len(register["sources"]) == 7, "source register scope changed")
    for pin, entry in zip(PINS, register["sources"]):
        name, url, size, digest, stored_size, stored_digest = pin
        path = root / f"data/tax-basics/raw/basics-{name}.html.json"
        stored = path.read_bytes()
        _require(len(stored) == stored_size and hashlib.sha256(stored).hexdigest() == stored_digest, f"envelope changed: {name}")
        envelope = json.loads(stored)
        _require(envelope.get("encoding") == "utf-8" and isinstance(envelope.get("original_response"), str), f"invalid envelope: {name}")
        body = envelope["original_response"].encode("utf-8")
        _require(len(body) == size and hashlib.sha256(body).hexdigest() == digest, f"original response changed: {name}")
        _require(entry["url"] == url, f"official URL changed: {name}")
        _validate_official(name, url, body.decode("utf-8"))
    return True


# A separate copy contract. Exact equality disallows retained correct text followed
# by an added contradictory statement. Whitespace and HTML quoting remain flexible.
EXPECTED = {
    "income": "Income Tax applies to taxable income. Not all income is taxable.",
    "ni": "National Insurance has its own rules for work and self-employment. Contributions help you qualify for certain benefits and the State Pension. They are not a personal savings pot.",
    "vat": "VAT is a tax in many purchase prices, not all. Goods and services can have different rates, be zero-rated or be exempt.",
    "ct": "Corporation Tax applies to taxable company or association profits.",
    "allowance": "The Personal Allowance applies to Income Tax, not every tax. You can owe no Income Tax and still pay VAT through purchases.",
    "ni-rules": "National Insurance has its own rules and payment periods. Being below the annual Income Tax allowance does not by itself mean you owe no National Insurance.",
    "scotland": "Scotland sets Income Tax rates and bands on non-savings, non-dividend income of Scottish taxpayers. Those powers exclude the Personal Allowance; HMRC collects the tax.",
    "wales": "Wales also has devolved Income Tax rates. Where you live matters; HMRC collects the tax. Savings and dividends follow UK rules, outside these devolved rate powers.",
    "paye": "Employers normally deduct Income Tax from employees' pay. They also deduct National Insurance. They send this money to HMRC. They can also owe employer National Insurance.",
    "net-vat": "VAT-registered businesses normally pay HMRC the difference between VAT charged to customers and VAT paid to suppliers. They do not send the whole purchase price as VAT.",
    "burden": "Who sends the tax is not the same question as who bears its cost. These rules explain how tax is sent. They do not tell us who bears the cost.",
    "age": "Current official guidance retrieved 30 October 2026. No publication date is established. No rates are used here. This guidance is not the 2023/24 distribution data. The next guidance update is unknown.",
}
# Bind each claim to its own URL AND human-readable source locator.
LINKS = {
    "income": ("https://www.gov.uk/income-tax", "Income Tax guidance: Overview"),
    "ni": ("https://www.gov.uk/national-insurance", "National Insurance guidance: Overview and Who pays"),
    "vat": ("https://www.gov.uk/how-vat-works", "VAT guidance: Overview; What VAT is charged on; How much VAT you must charge"),
    "ct": ("https://www.gov.uk/corporation-tax", "Corporation Tax guidance: Overview"),
    "allowance": ("https://www.gov.uk/income-tax#income-tax-allowances-and-reliefs", "Personal Allowance: allowances and reliefs"),
    "ni-rules": ("https://www.gov.uk/national-insurance#who-pays-national-insurance", "National Insurance: Who pays"),
    "scotland": ("https://www.gov.scot/policies/taxes/income-tax/", "Scottish Government: Income Tax powers"),
    "wales": ("https://www.gov.uk/welsh-income-tax#who-pays-the-welsh-rates", "Welsh rates: Who pays"),
    "paye": ("https://www.gov.uk/paye-for-employers#deductions-from-their-pay", "PAYE: deductions and paying HMRC"),
    "net-vat": ("https://www.gov.uk/how-vat-works#your-responsibilities-as-a-vat-registered-business", "VAT: business responsibilities"),
}
# This claim is not GOV.UK guidance. check_taxes independently binds its OBR
# group explanation, source label U4 and inclusion note C42 at this destination.
CT_SCOPE = "The OBR group also includes related charges. See the OBR group scope and source note."
CT_SCOPE_LINK = ("#tax-sources", "OBR Receipts (£bn): U4 and note C42")
TAX_FIELDS = ("income", "ni", "vat", "ct", "scope:ct", "allowance", "ni-rules", "scotland", "wales", "age")
PAYER_FIELDS = ("paye", "net-vat", "burden", "age")


class _Fragment(HTMLParser):
    def __init__(self, scope, tag):
        super().__init__(convert_charrefs=True)
        self.scope, self.tag = scope, tag
        self.stack, self.claims, self.links = [], {}, {}
        self.text, self.outside_claim = [], []
        self.current, self.link = None, None
        self.count = self.details = self.summaries = self.headings = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        # Check the root BEFORE its early return. Reject every attribute outside
        # this bounded contract, including native concealment/access blockers.
        if self.stack or a.get("data-basics") == self.scope:
            allowed = {"data-basics", "aria-labelledby", "id", "data-basics-claim",
                       "data-basics-scope", "href", "open"}
            _require(all(k in allowed for k, _ in attrs), "hidden or active basics content")
        if a.get("data-basics") == self.scope:
            _require(not self.stack and tag == self.tag, "wrong or nested basics container")
            self.count += 1
            self.stack.append(tag)
            return
        if not self.stack:
            return
        _require(tag in {"h2", "h3", "dl", "dt", "dd", "p", "a", "details", "summary"}, "unexpected element in basics")
        if tag in {"h2", "h3"}:
            expected_tag, expected_id = (("h2", "tax-basics-title") if self.scope == "taxes"
                                         else ("h3", "payer-basics-title"))
            _require(tag == expected_tag and self.stack == [self.tag] and a.get("id") == expected_id,
                     "wrong basics heading level or position")
            self.headings += 1
        self.stack.append(tag)
        markers = [key for key in ("data-basics-claim", "data-basics-scope") if key in a]
        if markers:
            _require(len(markers) == 1, "mixed guidance and scope claim")
            marker = markers[0]
            field = a[marker]
            if marker == "data-basics-scope":
                _require(self.scope == "taxes" and field == "ct" and self.stack == ["section", "p"],
                         "wrong or misplaced OBR scope marker")
                field = "scope:ct"
            else:
                _require(field in EXPECTED, "unknown guidance claim")
            _require(tag == "p" and self.current is None and field not in self.claims, "duplicate or nested claim")
            self.current = field
            self.claims[field], self.links[field] = [], []
        if tag == "a":
            _require(self.current is not None and self.link is None, "unscoped source link")
            self.link = [a.get("href"), []]
        if tag == "details":
            self.details += 1
        if tag == "summary":
            self.summaries += 1

    def handle_data(self, data):
        if not self.stack:
            return
        self.text.append(data)
        if self.current is not None:
            self.claims[self.current].append(data)
        else:
            self.outside_claim.append(data)
        if self.link is not None:
            self.link[1].append(data)

    def handle_endtag(self, tag):
        if not self.stack:
            return
        _require(self.stack[-1] == tag, "unbalanced basics HTML")
        if tag == "a":
            self.links[self.current].append((self.link[0], _norm("".join(self.link[1]))))
            self.link = None
        if tag == "p":
            self.current = None
        self.stack.pop()
        self.text.append(" ")
        if self.current is None:
            self.outside_claim.append(" ")

    def handle_comment(self, data):
        _require(not self.stack, "unexpected basics comment")


def _validate_fragment(html, scope, tag, fields, extra):
    parser = _Fragment(scope, tag)
    parser.feed(html)
    parser.close()
    _require(parser.count == 1 and not parser.stack, f"missing, duplicate or unclosed {scope} fragment")
    _require(tuple(parser.claims) == fields, f"missing or reordered {scope} claims")
    _require(parser.details == parser.summaries == 1, f"missing native details in {scope}")
    _require(parser.headings == 1, f"missing or duplicate {scope} heading")
    _require(_norm("".join(parser.outside_claim)) == extra, f"changed {scope} headings or added unverified copy")
    for field in fields:
        if field == "scope:ct":
            _require(parser.links[field] == [CT_SCOPE_LINK], "wrong OBR scope URL/locator")
            _require(_norm("".join(parser.claims[field])) == CT_SCOPE + " " + CT_SCOPE_LINK[1],
                     "changed OBR scope meaning")
            continue
        links = [LINKS[field]] if field in LINKS else []
        _require(parser.links[field] == links, f"wrong source URL/locator for {field}")
        expected = EXPECTED[field] + (" " + LINKS[field][1] if links else "")
        _require(_norm("".join(parser.claims[field])) == expected, f"changed meaning for {field}")
    # Scoped only: values elsewhere on the page remain valid fiscal data.
    text = _norm(" ".join(parser.text))
    _require(not re.search(r"(?:£\s*\d|\d\s*(?:%|per cent))", text), "numeric rate or personal example in basics")
    _require(not any(word in text for word in ("original_response", "datePublished", "stored_sha256", "csrf-token", "publication_or_update_date")), "raw source/publication metadata leak")


def validate_fragments(tax_html, payer_html, root=ROOT):
    validate_sources(root)
    _validate_fragment(tax_html, "taxes", "section", TAX_FIELDS,
        "What are the main taxes? Income Tax National Insurance VAT Corporation Tax Where you live can change the rules These are not personal tax calculations or a guide to every devolved tax.")
    _validate_fragment(payer_html, "payers", "aside", PAYER_FIELDS,
        "How is the tax collected? What these sources can tell us These sources explain how tax is sent. They do not model tax costs. Read the household analysis for the model's assumptions and limits. It has its own sources.")
    return True
