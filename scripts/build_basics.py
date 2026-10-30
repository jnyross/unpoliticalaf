"""Small, static explanations. No rates, calculator, source embedding or I/O.

Insert tax_basics() near the first tax group, and payer_basics() before the
payer methodology. The payer seed must retain its own ONS assumptions and links.
Source assertions describe a synthesis, not an automated finding of equivalence.
"""
from html import escape

URLS = {
    "income": "https://www.gov.uk/income-tax",
    "ni": "https://www.gov.uk/national-insurance",
    "vat": "https://www.gov.uk/how-vat-works",
    "ct": "https://www.gov.uk/corporation-tax",
    "paye": "https://www.gov.uk/paye-for-employers",
    "scotland": "https://www.gov.scot/policies/taxes/income-tax/",
    "wales": "https://www.gov.uk/welsh-income-tax",
}

COPY = {
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

# Every derived qualitative claim has explicit retained-source anchors. Multiple
# anchors are a synthesis. OBR scope and ONS allocations still need their separate
# numeric-seed evidence. The separate CT group-scope paragraph points to that evidence.
source_assertions = {
    "income": {"field": "income", "source_ids": ["basics-income-tax"], "officialheading": "Overview", "quotedanchor": ["Income Tax is a tax you pay on your income.", "You do not have to pay tax on all types of income."]},
    "ni": {"field": "ni", "source_ids": ["basics-national-insurance"], "officialheading": "Overview; Who pays National Insurance; National Insurance classes", "quotedanchor": ["You pay National Insurance contributions to qualify for certain benefits and the State Pension.", "The type you pay depends on your employment status and how much you earn.", "Your contributions are treated as having been paid to protect your National Insurance record."]},
    "vat": {"field": "vat", "source_ids": ["basics-vat"], "officialheading": "Overview; What VAT is charged on; How much VAT you must charge", "quotedanchor": ["is a tax added to most products and services sold by VAT-registered businesses.", "goods or services that are exempt from VAT or are unaffected by VAT", "classed as reduced or zero-rated"]},
    "ct": {"field": "ct", "source_ids": ["basics-corporation-tax"], "officialheading": "Overview; Profits you pay Corporation Tax on", "quotedanchor": ["Corporation Tax is a tax your company or association pays to HM Revenue and Customs (HMRC) on profits", "Taxable profits for Corporation Tax include the money your company or association makes from:"]},
    "allowance": {"field": "allowance", "source_ids": ["basics-income-tax", "basics-vat"], "officialheading": "Income Tax allowances and reliefs; Overview", "quotedanchor": ["Most people in the UK get a Personal Allowance of tax-free income.", "is a tax added to most products and services sold by VAT-registered businesses."]},
    "ni-rules": {"field": "ni-rules", "source_ids": ["basics-national-insurance", "basics-income-tax"], "officialheading": "Who pays National Insurance; Income Tax allowances and reliefs", "quotedanchor": ["per week from one job", "a year", "The type you pay depends on your employment status and how much you earn.", "Most people in the UK get a Personal Allowance of tax-free income."]},
    "scotland": {"field": "scotland", "source_ids": ["basics-scottish-powers"], "officialheading": "Income Tax", "quotedanchor": ["set the tax band thresholds (excluding the personal allowance) as well as the rates.", "This applies to all non-savings, non-dividend income of Scottish taxpayers", "HMRC is responsible for the collection and management of Scottish Income Tax"]},
    "wales": {"field": "wales", "source_ids": ["basics-welsh-income-tax", "basics-scottish-powers"], "officialheading": "Income Tax in Wales; Who pays the Welsh rates; How you pay; Income Tax", "quotedanchor": ["You pay Welsh Income Tax rates if you live in Wales. These rates have been set by the Welsh Government.", "the same tax as the rest of the UK on dividends and savings interest.", "HMRC will add a ‘C’ to the start of your tax code", "This applies to all non-savings, non-dividend income of Scottish taxpayers"]},
    "paye": {"field": "paye", "source_ids": ["basics-paye-remitter"], "officialheading": "Deductions from their pay; Reporting pay and deductions; Paying HMRC", "quotedanchor": ["deduct tax and National Insurance for most employees.", "including an employer’s National Insurance contribution", "You then have to pay HMRC, usually every month."]},
    "net-vat": {"field": "net-vat", "source_ids": ["basics-vat"], "officialheading": "Your responsibilities as a VAT-registered business", "quotedanchor": ["If you’ve charged more VAT than you’ve paid, you must pay the difference to HMRC."]},
    "burden": {"field": "burden", "source_ids": ["basics-paye-remitter", "basics-vat"], "officialheading": "Introduction to PAYE; Your responsibilities as a VAT-registered business", "quotedanchor": ["system to collect Income Tax and National Insurance from employment.", "If you’ve charged more VAT than you’ve paid, you must pay the difference to HMRC."], "scope": "Collection guidance only; no ONS allocation or universal incidence claim."},
}
SOURCE_ASSERTIONS = source_assertions


def _link(source, label, fragment=""):
    return f'<a href="{escape(URLS[source] + fragment, quote=True)}">{escape(label)}</a>'


def _claim(field, links=""):
    return f'<p data-basics-claim="{field}">{escape(COPY[field])}{(" " + links) if links else ""}</p>'


def tax_basics():
    """Return one self-contained semantic section; use the host page's styles."""
    definitions = []
    for field, title, label in (
        ("income", "Income Tax", "Income Tax guidance: Overview"),
        ("ni", "National Insurance", "National Insurance guidance: Overview and Who pays"),
        ("vat", "VAT", "VAT guidance: Overview; What VAT is charged on; How much VAT you must charge"),
        ("ct", "Corporation Tax", "Corporation Tax guidance: Overview"),
    ):
        definitions.append(f'<dt>{title}</dt><dd>{_claim(field, _link(field, label))}</dd>')
    return '\n'.join([
        '<section data-basics="taxes" aria-labelledby="tax-basics-title">',
        '<h2 id="tax-basics-title">What are the main taxes?</h2>',
        '<dl>' + '\n'.join(definitions) + '</dl>',
        '<p data-basics-scope="ct">The OBR group also includes related charges. See the OBR group scope and source note. '
        '<a href="#tax-sources">OBR Receipts (£bn): U4 and note C42</a></p>',
        _claim("allowance", _link("income", "Personal Allowance: allowances and reliefs", "#income-tax-allowances-and-reliefs")),
        _claim("ni-rules", _link("ni", "National Insurance: Who pays", "#who-pays-national-insurance")),
        '<details><summary>Where you live can change the rules</summary>',
        _claim("scotland", _link("scotland", "Scottish Government: Income Tax powers")),
        _claim("wales", _link("wales", "Welsh rates: Who pays", "#who-pays-the-welsh-rates")),
        '<p>These are not personal tax calculations or a guide to every devolved tax.</p>',
        '</details>',
        _claim("age"),
        '</section>',
    ])


def payer_basics():
    """Collection only. Keep the separately sourced ONS module next to this aside."""
    return '\n'.join([
        '<aside data-basics="payers" aria-labelledby="payer-basics-title">',
        '<h3 id="payer-basics-title">How is the tax collected?</h3>',
        _claim("paye", _link("paye", "PAYE: deductions and paying HMRC", "#deductions-from-their-pay")),
        _claim("net-vat", _link("vat", "VAT: business responsibilities", "#your-responsibilities-as-a-vat-registered-business")),
        _claim("burden"),
        '<details><summary>What these sources can tell us</summary>',
        '<p>These sources explain how tax is sent. They do not model tax costs. Read the household analysis for the model\'s assumptions and limits. It has its own sources.</p>',
        _claim("age"),
        '</details>',
        '</aside>',
    ])
