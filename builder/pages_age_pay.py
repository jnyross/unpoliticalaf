"""Pay around the age of 30 and job security at 25 to 34, for the generations page.

Pay is shown for each April on its own ASHE basis, with changes after inflation only within
one basis (data_age_pay.RUNS). The job security section shows the nearest official measures
under their own names and says why none of them is job security since 1992.
"""

from .data_age_pay import BASE_YEAR, RED02_FIRST, RUNS, TABLE6, change_fid, pay_fid, real_fid
from .html import FOLD, source_line, table

FIRST, LAST = min(TABLE6), max(TABLE6)
WORK_FIRST = 1992  # the first year of the quarterly Labour Force Survey, for the age-group rates


def pay_answer(num):
    """One sentence for the page's short answer."""
    return (
        f"Full-time employees aged 30 to 39 had median pay of {num(pay_fid(FIRST), 'pounds')} a week in April {FIRST} "
        f"({num(real_fid(FIRST), 'pounds')} in April {BASE_YEAR} prices) and {num(pay_fid(LAST), 'pounds')} in April {LAST}; "
        "the survey changed its methods in between, so no single change is worked out. "
        "No official measure of job security at 25 to 34 goes back to 1992. "
    )


def _runs_text(num):
    return "; ".join(f"April {a} to April {b}: {num(change_fid(a, b), 'pct')}" for a, b in RUNS)


def pay_section(num, sources):
    return "\n".join(
        [
            "<h2 id='pay-at-30'>Pay around the age of 30, after inflation</h2>",
            f"<p>The nearest measure is full-time employees aged 30 to 39, not people aged exactly 30. Their median pay was "
            f"{num(pay_fid(FIRST), 'pounds')} a week before tax in April {FIRST}, which is {num(real_fid(FIRST), 'pounds')} in April {BASE_YEAR} prices, "
            f"and {num(pay_fid(LAST), 'pounds')} in April {LAST}. The survey’s methods changed in between, so no change from {FIRST} to {LAST} is worked out.</p>",
            FOLD,
            '<div class="limit"><p><strong>Not people aged exactly 30.</strong> ONS’s Annual Survey of Hours and Earnings '
            "(Table 6) groups employees by age in ten-year bands, so these figures are for everyone aged 30 to 39 in full-time jobs. "
            "The only ONS estimates by single year of age that the site holds cover ages 16 to 25. "
            f"<strong>No change from {FIRST} to {LAST} is worked out.</strong> ONS says changes to its methods broke the series in 2004, "
            "2006 and 2011, and job coding changed again in 2021, so pay is compared only between years measured the same way. "
            f"After inflation, pay in this age group changed by: {_runs_text(num)}. "
            "ONS’s figures for 2020 and 2021 include employees who were furloughed.</p></div>",
            table(
                "Median weekly pay before tax, full-time employees aged 30 to 39, United Kingdom, April",
                ["April", "Survey basis", "Cash", f"In April {BASE_YEAR} prices"],
                [
                    [str(y), basis, num(pay_fid(y), "pounds"), num(real_fid(y), "pounds")]
                    for y, (_, _, _, basis) in sorted(TABLE6.items())
                ],
            ),
            table(
                "Change in pay after inflation, full-time employees aged 30 to 39, within years measured the same way",
                ["From", "To", "Change after inflation"],
                [[f"April {a}", f"April {b}", num(change_fid(a, b), "pct")] for a, b in RUNS],
            ),
            "<p>Employees on adult rates whose pay was not affected by absence. Prices are adjusted with CPIH, "
            'the index the site uses for real pay. <a href="earnings.html">Pay for all full-time employees, every year</a>.</p>',
            source_line(
                sources,
                [sid for sid, _, _, _ in TABLE6.values()]
                + ["ons-ashe-age-single-year-adhoc", "ons-ashe-qmi", "ons-l522"],
                up="../",
            ),
        ]
    )


def security_section(num, sources):
    rate = f"redund.age.25_34.{BASE_YEAR}"
    return "\n".join(
        [
            "<h2 id='job-security'>Job security at 25 to 34</h2>",
            f"<p>The site has no measure of job security for people aged 25 to 34 going back to {WORK_FIRST}. "
            "The nearest figures are the share in work and, from 2009, the redundancy rate. Neither is job security on its own, so each is given under its own name.</p>",
            FOLD,
            "<ul>"
            f'<li><strong>In work:</strong> {num(f"work.age.25_34.{BASE_YEAR}", "pct")} of people aged 25 to 34 were in work in April to June {BASE_YEAR}, '
            f'against {num(f"work.age.25_34.{WORK_FIRST}", "pct")} in April to June {WORK_FIRST}. This is the share in work of any kind, not how secure that work is.</li>'
            f"<li><strong>Redundancy:</strong> in April to June {BASE_YEAR}, {num(rate, 'dp1')} in every 1,000 employees aged 25 to 34 were made redundant "
            "(redundancies in the quarter, for every 1,000 employees in the previous quarter). "
            f"ONS’s figures by age start in {RED02_FIRST.replace('Jan-Mar', 'January to March')}, so there is no {WORK_FIRST} figure.</li>"
            "<li><strong>Temporary work:</strong> ONS’s table of temporary employees (EMP07) is split by sex and by full-time or part-time work, "
            "not by age, so it cannot show temporary work at 25 to 34.</li>"
            "<li><strong>Time in one job:</strong> the site holds no official table of how long people aged 25 to 34 stay in a job since "
            f"{WORK_FIRST}.</li>"
            "</ul>",
            '<div class="limit"><p><strong>Not a measure of job security.</strong> A higher share in work does not mean the work is more secure, '
            "and a redundancy rate counts only one way of losing a job. ONS publishes the redundancy figures as official statistics in development; "
            "it reweighted them from January to March 2019, causing a step change, so the site does not compare them across 2019 or with earlier years.</p></div>",
            table(
                "Nearest figures for people aged 25 to 34, United Kingdom",
                ["Measure", "Period", "Figure"],
                [
                    [
                        "Share in work (employment rate)",
                        f"April to June {WORK_FIRST}",
                        num(f"work.age.25_34.{WORK_FIRST}", "pct"),
                    ],
                    [
                        "Share in work (employment rate)",
                        f"April to June {BASE_YEAR}",
                        num(f"work.age.25_34.{BASE_YEAR}", "pct"),
                    ],
                    [
                        "Made redundant, per 1,000 employees",
                        f"April to June {BASE_YEAR}",
                        num(rate, "dp1"),
                    ],
                ],
            ),
            source_line(sources, ["ons-ybug", "ons-red02", "ons-emp07"], up="../"),
        ]
    )
