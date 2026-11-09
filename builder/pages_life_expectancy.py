"""PR #225's age-30 answer, with the period assumption beside the figures."""

from .html import source_line, table


def life_section(num, sources):
    return (
        "<h3 id='life-expectancy'>Life expectancy at 30</h3>"
        "<p>UK, single-year life tables: in 2024, period life expectancy at exact age 30 was "
        f'{num("life.ex30.male.2024", "dp1")} more years for men and '
        f'{num("life.ex30.female.2024", "dp1")} for women. Compared with 1994, that is '
        f'{num("life.ex30.male.change", "dp1")} more years for men and '
        f'{num("life.ex30.female.change", "dp1")} for women.</p>'
        '<div class="limit"><p><strong>Period figures, not a forecast for a person.</strong> '
        "They show how many more years someone aged 30 would live on average if the death rates "
        "at each age in that year stayed the same for the rest of their life. They do not "
        "predict how long today’s 30-year-olds will live. The latest year here is 2024, not 2026.</p></div>"
        + table(
            "Remaining years at exact age 30, UK, single-year period life tables",
            ["Sex", "1994", "2024", "Change (years, calculated)"],
            [
                [
                    label,
                    num(f"life.ex30.{sex}.1994", "dp1"),
                    num(f"life.ex30.{sex}.2024", "dp1"),
                    num(f"life.ex30.{sex}.change", "dp1"),
                ]
                for sex, label in (("male", "Men"), ("female", "Women"))
            ],
        )
        + "<p>ONS published these tables on 10 December 2025. Single-year tables vary more "
        "than three-year tables and are not accredited official statistics. ONS recommends using them "
        "alongside three-year tables for longer-term trends; this is a comparison of two single years. "
        "The figures are remaining years, not age at death; adding 30 would give a calculated "
        "age under the same fixed death-rate assumption, not a lifespan forecast.</p>"
        + source_line(sources, ["ons-single-year-life-tables-uk"], up="../")
    )
