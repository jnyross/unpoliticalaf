"""Housing and class sizes in Wales, Scotland and Northern Ireland, for the
everyday-life overview. Each nation measures these its own way, so figures are
shown side by side with what each one counts, and never added together."""
from .data import YEARS
from .html import table, details_table, esc

MISSING = "<span class='missing'>not published</span>"


def _val(facts, fid):
    f = facts.get(fid)
    return None if f is None else f.value


def _sy(y):
    return f"{y}-{str(y + 1)[2:]}"


def housing_nations_block(facts, num, d):
    n = d["nations"]
    eng = [y for y in YEARS if _val(facts, f"house.reg.private.england.{y}") is not None]
    b = min(eng[-1], n["wales"][-1], n["scotland"][-1])
    ni = n["ni"][-1]
    out = ["<h3 id='housing-nations'>Wales, Scotland and Northern Ireland</h3>"]
    out.append(f'<div class="answer"><p>Each nation runs and measures housing its own way, so these figures sit side by side but small gaps between them should not be read as real differences. '
               f'At 31 March {b}, an estimated {num(f"house.nat.private.wales.{b}", "pct0")} of homes in Wales and {num(f"house.nat.private.scotland.{b}", "pct0")} in Scotland were rented privately, '
               f'compared with {num(f"house.reg.private.england.{b}", "pct0")} in England. '
               f'Northern Ireland publishes a survey of households instead: in {_sy(ni)}, {num(f"house.nat.private.ni.{ni}", "pct0")} of households there rented privately '
               f'and {num(f"house.nat.owner.ni.{ni}", "pct0")} owned their home.</p></div>')
    rows = [
        ["England", "Homes, including empty ones", f"31 March {b}", num(f"house.reg.owner.england.{b}", "pct"), num(f"house.reg.private.england.{b}", "pct"), num(f"house.reg.social.england.{b}", "pct"), "None: empty homes are counted in their tenure"],
        ["Wales", "Homes, including empty ones", f"31 March {b}", num(f"house.nat.owner.wales.{b}", "pct"), num(f"house.nat.private.wales.{b}", "pct"), num(f"house.nat.social.wales.{b}", "pct"), "None: empty homes are counted in their tenure"],
        ["Scotland", "Homes, with empty private homes and second homes counted separately", f"31 March {b}", num(f"house.nat.owner.scotland.{b}", "pct"), num(f"house.nat.private.scotland.{b}", "pct"),
         num(f"house.nat.social.scotland.{b}", "pct"), f"Empty private homes and second homes: {num(f'house.nat.vacant.scotland.{b}', 'pct')}"],
        ["Northern Ireland", "Households (a survey of about 1,700 households a year)", _sy(ni), num(f"house.nat.owner.ni.{ni}", "pct0"), num(f"house.nat.private.ni.{ni}", "pct0"), num(f"house.nat.social.ni.{ni}", "pct0"),
         "Rounded to whole numbers, so may not add to 100"],
    ]
    out.append(table("Homes by tenure in each nation, latest year, %", ["Nation", "What is counted", "When", "Owner occupied", "Private rent", "Social rent", "Not in these columns"], rows))
    def cell(fid, kind="pct"):
        return num(fid, kind) if _val(facts, fid) is not None else MISSING
    rows = []
    for y in YEARS:
        scot = cell(f"house.nat.private.scotland.{y}")
        if y in (2020, 2021) and _val(facts, f"house.nat.private.scotland.{y}") is not None:
            scot += " (pandemic: not compared)"
        rows.append([str(y), cell(f"house.nat.private.wales.{y}"), scot,
                     _sy(y), cell(f"house.nat.private.ni.{y}", "pct0")])
    out.append(details_table("Show private renting in Wales, Scotland and Northern Ireland for every year", "Private renting by nation, % (homes at 31 March; Northern Ireland: households over a survey year)",
                             ["Year", "Wales (homes)", "Scotland (homes)", "Northern Ireland survey year", "Northern Ireland (households)"], rows))
    out.append('<p class="small">England’s figure for every year is in the regional table above. England, Wales and Scotland count homes (dwellings) at 31 March and split private homes between owners and renters using their own surveys. '
               'Wales counts shared ownership and other part-buy schemes as owner occupied; Wales’s figures for owners and private renters in 2024 and 2025 are provisional. '
               'Scotland counts empty private homes and second homes on their own, so its owner and private-rent shares are slightly lower than they would be on England’s basis. '
               'Scotland’s publisher advises against comparing its 2020 and 2021 owner and private-rent figures with other years, because the pandemic disrupted the survey behind them. '
               'Northern Ireland’s figures come from the Family Resources Survey, which interviews about 1,700 to 2,100 households a year (fewer in 2020-21), so year-to-year moves of a point or two may be sampling noise; '
               'its table starts in 2012-13. Social rent adds homes or households renting from councils and from housing associations (our calculation for England and Scotland). '
               'None of these figures is added up into a UK total.</p>')
    return out


def schools_nations_block(facts, num, d, wy, wales_table):
    """Wales, Scotland and Northern Ireland in one section: each nation's latest figure
    in view, its table and notes in the fold. wy is Wales's latest January census."""
    sy = sorted(d["nations"]["school_scotland"])
    a, b = sy[0], sy[-1]
    out = ["<h3 id='schools-nations'>Wales, Scotland and Northern Ireland</h3>"]
    out.append(f'<div class="answer"><p>In Wales, infant classes (reception to year 2) averaged {num(f"school.wales.infant.{wy}", "dp1")} pupils and junior classes (years 3 to 6) '
               f'{num(f"school.wales.junior.{wy}", "dp1")} in January {wy}. In Scotland the average primary class had {num(f"school.scotland.primary.{b}", "dp1")} pupils '
               f'at the September {b} pupil census, compared with {num(f"school.scotland.primary.{a}", "dp1")} in September {a}. '
               'Northern Ireland publishes no average class size.</p></div>')
    out.append("<h3>Wales</h3>")
    out.append(wales_table)
    out.append('<p class="small">Welsh infant and junior figures are not the same groups as England’s primary figure, so they are not compared with it.</p>')
    out.append("<h3>Scotland</h3>")
    out.append(details_table("Show Scotland’s primary class sizes for every year", "Average class size, primary schools (all stages, P1 to P7), Scotland, September census",
                             ["September census", "School year", "Primary, all stages"],
                             [[str(y), f"{y}/{str(y + 1)[2:]}", num(f"school.scotland.primary.{y}", "dp1")] for y in sy]))
    out.append('<p class="small">Scotland counts classes in September, at the start of the school year, while England and Wales count in January, '
               'and Scotland calculates its average in its own way, so its figures are not compared with England’s. '
               'The Scottish tables used here give no average for secondary classes. Classes in publicly funded schools.</p>')
    out.append("<h3>Northern Ireland</h3>")
    out.append('<p>The Department of Education in Northern Ireland publishes yearly school enrolment statistics, but they do not include an average class size, '
               'so there is no Northern Ireland figure to show here.</p>')
    return out
