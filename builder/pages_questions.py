"""The questions page: every question page on the site in one list, linked from the main menu."""
from .html import page, esc, QUESTION_PAGES

# (page, question, one line on what the page shows). Questions are the same wording the home page uses.
GROUPS = [
    ("Public money", [
        ("spending.html", "Where does public money go?", "Total spending, its main purposes and how they have changed."),
        ("taxes.html", "Which taxes raise the money?", "Taxes, other receipts and borrowing."),
        ("who-pays.html", "Who pays?", "Income Tax and all taxes, by group of people."),
        ("household-tax.html", "How much household income goes on tax?", "Direct, indirect and combined taxes as a share of household income."),
        ("international.html", "How do UK taxes and spending compare with other countries?", "The UK beside the other OECD countries, as a share of GDP."),
        ("productivity.html", "How does UK productivity compare with other countries?", "Output per hour worked and per worker beside the other G7 countries."),
        ("borrowing.html", "How do UK debt and borrowing costs compare with other major countries?", "Debt, 10-year borrowing costs and debt interest beside the other G7 countries."),
        ("why-debt.html", "Why is UK government debt high?", "Debt and borrowing since 1900, the periods that raised them, and what the OBR and ONS say."),
        ("defence.html", "Why can't we afford to spend more on defence?", "UK defence spending in cash, after inflation and as a share of GDP, and what extra spending would cost."),
    ]),
    ("Tax, people and promises", [
        ("high-earners.html", "What if high earners left the UK?", "How much Income Tax the highest earners pay, and what the OBR has said about behaviour."),
        ("leaving-uk.html", "Are people leaving the UK?", "Official figures on emigration, and what they cannot show about why people leave."),
        ("manifesto.html", "Did Labour keep its 2024 manifesto?", "Ten pledges, each quoted, with what has happened and every reading the wording allows."),
        ("immigration.html", "Is immigration a good or a bad thing?", "What official evidence says about public money, public services and the economy, and where it cannot decide."),
    ]),
    ("Welfare, housing and generations", [
        ("welfare.html", "How has welfare spending changed?", "Social security spending over 50 years, after inflation, per person and as a share of GDP, and what each measure leaves out."),
        ("life/house-prices.html", "Have houses become harder to afford?", "House prices beside earnings and mortgage payments, by region, since 1997."),
        ("life/generations.html", "Did parents have it easier than this generation?", "Work, housing, university costs, pension age and class sizes for people of the same age, then and now."),
    ]),
]


assert {href for _, items in GROUPS for href, _, _ in items} == QUESTION_PAGES, "every question page is listed here"


def questions_page():
    body = ['<h1>Questions the site answers</h1>',
            '<p class="lead">Each question below has its own page. The page gives the answer first, then the official figures and what they cannot show.</p>']
    for title, items in GROUPS:
        body.append(f'<h2>{esc(title)}</h2>')
        body.append('<ul class="principles">')
        for href, question, line in items:
            body.append(f'<li><a href="{esc(href)}#answer"><strong>{esc(question)}</strong></a> {esc(line)}</li>')
        body.append('</ul>')
    body.append('<p>Want a single year rather than a question? See <a href="life/index.html">everyday life, year by year</a>.</p>')
    return page("questions.html", "Questions the site answers", "\n".join(body),
                description="Every question the site answers about UK public money, taxes, debt, defence, immigration and promises, with a link to each page.",
                contents=False)
