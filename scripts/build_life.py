"""Render the school-only life preview; the controller writes the returned HTML."""
import json
from decimal import Decimal, localcontext

from build_site import CSS, esc
from life_projection import PHASES, YEARS

BANDS = ("XdTUf", "zeoRF", "kxKDh", "u2cKo")


def _number(value, measure, refs="", comparison=None):
    attrs = f' data-comparison-id="{esc(comparison)}"' if comparison else ""
    return (f'<span data-measure="{esc(measure)}" data-value="{esc(value)}"'
            f' data-ref="{esc(refs)}"{attrs}>{esc(value)}</span>')


def _refs(measure):
    return " ".join(operand["source"]["locator"] for operand in measure["operands"])


def _short(period):
    left, right = period.split("/")
    return left + "/" + right[-2:]


def _scope():
    return ('<p class="small" data-pid="school-scope">England, by school location, not pupil residence. '
            'State-funded primary and secondary schools; classes taught by one teacher. '
            'These are observed January census counts, not forecasts. '
            'Class size is not pupil-teacher ratio or one child’s class. '
            'Primary overlaps Infant and KS2: do not add phases. '
            '<a href="#school-sources">DfE sources and notes</a>.</p>')


def _year_navigation(anchor):
    links = []
    for key, label in (("previous", "Previous year"), ("next", "Next year")):
        year = anchor[key]
        if year is None:
            links.append(f'<span>{label}: none</span>')
        else:
            links.append(f'<a data-year-step="{key}" href="#year-{year}">{label}: {year}</a>')
    return '<nav class="page-links" aria-label="Years beside ' + str(anchor["year"]) + '">' + "".join(links) + '</nav>'


def _year_section(anchor, indexed, phase_labels):
    year = anchor["year"]
    beginning = (f'<section id="year-{year}" data-life-year="{year}" data-anchor="{year}" tabindex="-1">'
                 f'<h2>Year {year}</h2>' + _year_navigation(anchor))
    if not anchor["available"]:
        return (beginning +
                '<p data-school-gap="true">Not in the selected DfE dataset. No retained school observation for this anchor. '
                'This gap is not zero. We do not fill it with a later value.</p>'
                f'<p>Nearest school observation: <a data-nearest-year="{anchor["nearest"]}" '
                f'href="#year-{anchor["nearest"]}">January {anchor["nearest"]}, '
                'academic year 2015/16</a>. This is not an observation for the selected year.</p>' + _scope() + '</section>')
    period = _short(anchor["period"])
    answer = [f'<p data-school-period="{year}">Academic year {esc(period)}; January {year} census.</p>']
    for phase in PHASES[:2]:
        row = indexed[(year, phase, "XdTUf")]
        mean = row["derived"]["mean"]
        answer.append(
            f'<p data-school-summary="{phase}" data-anchor="{year}">'
            f'{esc(phase_labels[phase])}: '
            + _number(mean["display"], "mean", _refs(mean)) + ' pupils per class.</p>')
    answer.append(_scope())
    rows = []
    for phase in PHASES:
        for band in BANDS:
            row = indexed[(year, phase, band)]
            values = []
            for indicator, measure in (("EAicq", "classes"), ("QtxWw", "pupils")):
                node = row["published"][indicator]
                values.append(_number(node["display"], measure, node["source"]["locator"]))
            for measure in ("mean", "class_share", "pupil_share"):
                node = row["derived"][measure]
                values.append(_number(node["display"], measure, _refs(node)))
            rows.append(
                f'<tr data-school-row="true" data-anchor="{year}" data-phase="{phase}" data-band="{band}">'
                f'<th scope="row">{esc(row["phase"])}</th><td>{esc(row["band"])}</td>'
                + "".join(f"<td>{value}</td>" for value in values) + "</tr>")
    heads = ("Phase", "Size band", "Classes", "Pupils", "Pupils per class", "Class share (%)", "Pupil share (%)")
    answer.append(
        '<details class="tbl"><summary>Show all school phases and size bands</summary>'
        f'<div class="table-scroll" role="region" aria-label="School numbers for {year}" tabindex="0">'
        f'<table id="school-table-{year}"><caption>England one-teacher classes, {esc(period)}; January {year}</caption>'
        '<thead><tr>' + "".join(f'<th scope="col">{head}</th>' for head in heads)
        + '</tr></thead><tbody>' + "".join(rows) + '</tbody></table></div>'
        '<p class="small">Shares use the published total for this phase and year. '
        'Class shares count classes; pupil shares count pupils. They are different wholes. '
        'Means use each row’s own pupils divided by its classes. Values are shown to one decimal.</p>'
        '</details>')
    return beginning + "".join(answer) + '</section>'


def _comparison_result(pair, phase_labels):
    phase = phase_labels[pair["phase"]]
    if not pair["available"]:
        return (f'<p id="compare-result" role="status" data-available="false">{esc(phase)}: '
                f'{esc(pair["reason"])}</p>')
    left_refs = " ".join(o["source"]["locator"] for o in pair["operands"][2:])
    right_refs = " ".join(o["source"]["locator"] for o in pair["operands"][:2])
    return (f'<p id="compare-result" role="status" data-available="true">{esc(phase)}: '
            f'January {pair["from"]} (academic {esc(_short(pair["from_period"]))}): '
            + _number(pair["left"], "left", left_refs, comparison=pair["id"]) + ' pupils per class. '
            f'January {pair["to"]} (academic {esc(_short(pair["to_period"]))}): '
            + _number(pair["right"], "right", right_refs, comparison=pair["id"]) + ' pupils per class. '
            'Signed change (to minus from): '
            + _number(pair["display"], "change", right_refs + " " + left_refs, comparison=pair["id"]) + ' pupils per class.</p>')


def _phase_order(schools, indexed):
    year = max(row["anchor"] for row in schools["rows"])
    primary = indexed[(year, "5kyxd", "XdTUf")]
    secondary = indexed[(year, "tfHTE", "XdTUf")]
    difference = next(item for item in schools["comparisons"]
                      if item["id"] == f"primary_minus_secondary_{year}")
    with localcontext() as context:
        context.prec = 50
        primary_mean = Decimal(primary["published"]["QtxWw"]["raw"]) / Decimal(primary["published"]["EAicq"]["raw"])
        secondary_mean = Decimal(secondary["published"]["QtxWw"]["raw"]) / Decimal(secondary["published"]["EAicq"]["raw"])
    relation = "lower than" if secondary_mean < primary_mean else "higher than" if secondary_mean > primary_mean else "the same as"
    return (f'<p data-pid="school-phase-order" data-anchor="{year}">In January {year}, '
            f'Secondary had a mean {relation} Primary. Secondary: '
            + _number(secondary["derived"]["mean"]["display"], "secondary_mean", _refs(secondary["derived"]["mean"]))
            + ' pupils per class. Primary: '
            + _number(primary["derived"]["mean"]["display"], "primary_mean", _refs(primary["derived"]["mean"]))
            + ' pupils per class. Primary minus Secondary: '
            + _number(difference["display"], "primary_minus_secondary", _refs(difference))
            + ' pupils per class. <a href="#school-sources">DfE source and method</a>.</p>')


def _pairs(data, phase_labels):
    pieces = []
    heads = ("From anchor", "To anchor", "From mean", "To mean", "Signed change")
    for phase in PHASES:
        rows = []
        for pair in data["comparisons"]:
            if pair["phase"] != phase or not pair["available"] or pair["from"] >= pair["to"]:
                continue
            pid = pair["id"]
            refs = " ".join(o["source"]["locator"] for o in pair["operands"])
            left_refs = " ".join(o["source"]["locator"] for o in pair["operands"][2:])
            right_refs = " ".join(o["source"]["locator"] for o in pair["operands"][:2])
            rows.append(
                f'<tr data-school-pair="true" data-from="{pair["from"]}" data-to="{pair["to"]}" data-phase="{phase}">'
                f'<th scope="row">{pair["from"]} ({esc(_short(pair["from_period"]))})</th>'
                f'<td>{pair["to"]} ({esc(_short(pair["to_period"]))})</td>'
                '<td>' + _number(pair["left"], "left", left_refs, pid) + '</td>'
                '<td>' + _number(pair["right"], "right", right_refs, pid) + '</td>'
                '<td>' + _number(pair["display"], "change", refs, pid) + '</td></tr>')
        pieces.append(
            f'<section id="pairs-{phase}" tabindex="-1"><h3>{esc(phase_labels[phase])} year pairs</h3>'
            f'<details class="tbl"><summary>{esc(phase_labels[phase])}: all forward year pairs</summary>'
            f'<div class="table-scroll" role="region" aria-label="{esc(phase_labels[phase])} year pairs" tabindex="0">'
            f'<table id="pair-table-{phase}"><caption>{esc(phase_labels[phase])}, pupils per class; observed January census</caption>'
            '<thead><tr>' + "".join(f'<th scope="col">{head}</th>' for head in heads)
            + '</tr></thead><tbody>' + "".join(rows) + '</tbody></table></div></details></section>')
    return "".join(pieces)


def _sources(schools):
    publication = schools["publication"]
    release = publication["release"]
    dates = [
        ("api_published", "API version published", publication["api_published"]),
        ("published", "Release published", release["published"]),
        ("lastUpdated", "Release last updated", release["lastUpdated"]),
        ("methodology", "Method page published", publication["methodology"]["published"]),
    ]
    parts = [
        '<section id="school-sources"><h2>School sources and limits</h2>',
        '<p>Department for Education (DfE): ' + esc(publication["title"])
        + '. API version ' + esc(publication["version"]) + '.</p>',
        '<ul class="name">' + "".join(
            f'<li>{esc(label)}: <span data-school-date="{key}">{esc(value)}</span>.</li>'
            for key, label, value in dates) + '</ul>',
    ]
    residual_rows = []
    for record in schools["reconciliations"]:
        if Decimal(record["residual_total_minus_bands"]) == 0:
            continue
        residual_rows.append(
            f'<li data-school-residual="true" data-period="{esc(record["timePeriod"]["period"])}" '
            f'data-phase="{esc(record["phase"])}" data-indicator="{esc(record["indicator"])}">'
            f'{esc(record["phase"])}, {esc(_short(record["timePeriod"]["period"]))}: '
            + _number(record["residual_total_minus_bands"], "residual", _refs(record))
            + " " + esc(record["unit"]) + ".</li>")
    next_release = publication["nextReleaseDate"]
    if next_release:
        parts.append(f'<p>Next release announced: {next_release["year"]}-{next_release["month"]:02d} '
                     '(month only; no day is stated).</p>')
    else:
        parts.append('<p>No next release date is announced in these sources.</p>')
    parts.append(
        '<p>Each annual anchor names the academic year ending in that year. '
        'The census is in January. The third-Thursday rule comes from the method page; '
        'it is not a separately reported date for each row. '
        'All eleven years use this current release. January 2021 is present. '
        'No older release is joined to it.</p>'
        '<p>The one-decimal means are pupils divided by each row’s own classes. '
        'Changes subtract those unrounded means, then round once. '
        'We use decimal arithmetic with 50-digit precision and round halves up. '
        'Do not subtract rounded means to check a change.</p>'
        '<p>Some published totals differ from their three size bands. These are total minus band sum. '
        'We keep each published total as the share’s whole. '
        'We do not force band shares to sum to 100 or assign a cause.</p>'
        + '<ul>' + ''.join(residual_rows) + '</ul>'
        + '<p>All 176 national rows, source locators, full hashes, notes, formulas and operands are in '
        '<a href="data/life.json" download="life.json">Download life data (JSON)</a>. '
        'The local-authority catalogue preview is separate: its z means not applicable. '
        'A blank or z is never a national zero.</p>'
        '<details><summary>Official sources, hashes and exact notes</summary><ul class="name">')
    for filename, source in schools["sources"].items():
        parts.append(
            f'<li><a data-school-source="{esc(filename)}" href="{esc(source["url"])}">{esc(filename)}</a>'
            f'<br>Original SHA-256: <code data-source-hash="{esc(filename)}">{esc(source["sha256"])}</code>.</li>')
    parts.append('</ul>')
    for key, note in schools["notes"].items():
        parts.append(f'<blockquote data-school-note="{esc(key)}">{esc(note["text"])}</blockquote>'
                     f'<p class="small">Source locator: <code>{esc(note["source"]["locator"])}</code>. '
                     f'Original SHA-256: <code>{esc(note["source"]["sha256"])}</code>.</p>')
    parts.append('<p class="small">' + esc(publication["footnote_caution"]) + '</p>')
    for footnote in publication["catalogue_footnotes"]:
        # Footnotes are source structures, kept verbatim in the data download.
        parts.append('<p class="small"><code>' + esc(json.dumps(footnote, ensure_ascii=False, sort_keys=True)) + '</code></p>')
    parts.append('</details></section>')
    return "".join(parts)


JS = r"""
(function(){
'use strict';
var yearSelect=document.getElementById('life-year-select');
var yearStatus=document.getElementById('life-year-status');
var sections=Array.from(document.querySelectorAll('section[data-life-year]'));
var supported=new Set(sections.map(function(s){return s.dataset.lifeYear;}));
function chooseYear(year,focus){
  if(!supported.has(String(year)))return;
  yearSelect.value=String(year);
  sections.forEach(function(s){
    if(s.dataset.lifeYear===String(year)){s.setAttribute('aria-current','true');if(focus)s.focus();}
    else s.removeAttribute('aria-current');
  });
  var target=document.getElementById('year-'+year);
  var period=target.querySelector('[data-school-period]');
  yearStatus.textContent=year+': '+(period?period.textContent:'No retained school observation. Nearest observation is January 2016.');
}
function fromHash(){
  if(!/^#year-\d{4}$/.test(location.hash))return false;
  var year=location.hash.slice(6);
  if(!supported.has(year))return false;
  chooseYear(year,true);
  return true;
}
window.addEventListener('hashchange',fromHash);
yearSelect.addEventListener('change',function(){
  var hash='#year-'+yearSelect.value;
  if(location.hash===hash)chooseYear(yearSelect.value,true);
  else location.hash=hash;
});
document.getElementById('life-year-controls').hidden=false;
if(!fromHash())chooseYear(DEFAULT_YEAR,false);

var from=document.getElementById('compare-from');
var to=document.getElementById('compare-to');
var phase=document.getElementById('compare-phase');
var result=document.getElementById('compare-result');
function number(value,measure,id,refs){
  var span=document.createElement('span');
  span.dataset.measure=measure;span.dataset.value=value;span.dataset.comparisonId=id;span.dataset.ref=refs;
  span.textContent=value;return span;
}
function text(value){return document.createTextNode(value);}
function short(period){return period.slice(0,5)+period.slice(-2);}
function compare(){
  var id=from.value+':'+to.value+':'+phase.value;
  var pair=PAIRS[id];
  if(!pair){
    result.dataset.available='false';
    result.replaceChildren(text(PHASE_LABELS[phase.value]+': No retained school observation for one or both anchors. '));
    var nearest=document.createElement('a');nearest.href='#year-2016';
    nearest.textContent='Nearest observation for a gap: January 2016 (academic 2015/16).';
    nearest.dataset.nearestYear='2016';result.append(nearest);return;
  }
  result.dataset.available='true';
  function meanRefs(year){
    var row=document.querySelector('tr[data-school-row][data-anchor="'+year+'"][data-phase="'+phase.value+'"][data-band="XdTUf"]');
    return row.querySelector('[data-measure="mean"]').dataset.ref;
  }
  var leftRefs=meanRefs(from.value),rightRefs=meanRefs(to.value);
  result.replaceChildren(
    text(PHASE_LABELS[phase.value]+': January '+from.value+' (academic '+short(pair[3])+'): '),
    number(pair[0],'left',id,leftRefs),text(' pupils per class. January '+to.value+' (academic '+short(pair[4])+'): '),
    number(pair[1],'right',id,rightRefs),text(' pupils per class. Signed change (to minus from): '),
    number(pair[2],'change',id,rightRefs+' '+leftRefs),text(' pupils per class.'));
}
[from,to,phase].forEach(function(select){select.addEventListener('change',compare);});
document.getElementById('compare-controls').hidden=false;
document.body.classList.remove('nojs');
})();
"""


def render(data):
    schools = data["schools"]
    phase_labels = {option["id"]: option["label"]
                    for field in schools["definitions"]["filters"]
                    if field["id"] == "5cGdi" for option in field["options"]}
    indexed = {(row["anchor"], row["filters"]["5cGdi"], row["filters"]["cAd31"]): row
               for row in schools["rows"]}
    navigation = "".join(
        f'<a href="{target}"' + (' aria-current="page"' if target == 'life.html' else '') + f'>{label}</a>'
        for target, label in (("index.html", "Spending"), ("taxes.html", "Taxes"),
                              ("who-pays.html", "Who pays"), ("methods.html", "Methods"),
                              ("life.html", "Year by year")))
    options = "".join(f'<option value="{year}">{year}</option>' for year in YEARS)
    default_pair = next(pair for pair in data["comparisons"]
                        if pair["id"] == "2016:2026:5kyxd")
    from_options = options.replace('value="2016"', 'value="2016" selected')
    to_options = options.replace('value="2026"', 'value="2026" selected')
    phase_options = "".join(f'<option value="{code}">{esc(phase_labels[code])}</option>' for code in PHASES)
    body = (
        '<header><h1>Life, year by year</h1>'
        '<p data-pid="technical-preview"><strong>TECHNICAL PREVIEW — reader acceptance pending</strong></p>'
        '<p>This first view covers school class sizes in England. '
        'Other topics are not yet built. Work, earnings, housing and holidays are still to come.</p>'
        '<p data-pid="aggregate-disclaimer">These are totals for groups, not a tracked person, '
        'an observed family or a typical child. A change does not show what caused it.</p>'
        '<p><a href="index.html">Public spending</a> · <a href="taxes.html">Taxes and receipts</a> · '
        '<a href="who-pays.html">People and household taxes</a>. These use their own periods and sources.</p>'
        '</header><main id="main">'
        '<nav class="page-links" aria-label="On this page"><a href="#life-years">Choose a year</a>'
        '<a href="#compare">Compare school years</a><a href="#school-sources">Sources and limits</a></nav>'
        '<h2>School class sizes</h2><p>Choose any year from 2008 to 2026. '
        'School data here run from January 2016 to January 2026. Earlier anchors show a gap.</p>'
        + _scope()
        + '<nav class="page-links" id="life-years" aria-label="Annual anchors">'
        + "".join(f'<a href="#year-{year}">{year}</a>' for year in YEARS)
        + '</nav><div id="life-year-controls" class="life-controls" hidden>'
        '<label for="life-year-select">Jump to an annual anchor</label>'
        '<select id="life-year-select">' + to_options + '</select></div>'
        '<p id="life-year-status" role="status">All annual sections are below.</p>'
        + "".join(_year_section(anchor, indexed, phase_labels) for anchor in data["anchors"])
        + '<section id="compare"><h2>Compare school years</h2>'
        '<p>Choose two anchors and one phase. Each mean uses that phase’s own pupil and class counts. '
        'A positive change means a larger mean class; a negative change means a smaller mean class.</p>'
        + _scope()
        + '<div id="compare-controls" class="life-controls" hidden>'
        '<label for="compare-from">From anchor</label><select id="compare-from">' + from_options + '</select>'
        '<label for="compare-to">To anchor</label><select id="compare-to">' + to_options + '</select>'
        '<label for="compare-phase">School phase</label><select id="compare-phase">' + phase_options + '</select></div>'
        + _comparison_result(default_pair, phase_labels)
        + _phase_order(schools, indexed)
        + '<p class="small" data-pid="pair-method">Changes use to-year pupils / classes minus from-year pupils / classes, '
        'before rounding. Each result is in pupils per class, shown to one decimal. '
        '<a href="#school-sources">Source and method</a>.</p>'
        '<p data-pid="pair-mapping">The tables below give every forward pair for all four phases. '
        'For a reverse pair, swap the two means and reverse the sign of the shown change. '
        'For the same observed year, both means are that year’s mean and the change is +0.0. '
        'If either anchor is 2008–2015, the result is unavailable, even for the same year. '
        '<a href="#year-2016">The nearest observation for those gaps is January 2016 (2015/16)</a>. '
        'Missing values are never zero. All ordered choices are also in the data download.</p>'
        + '<nav class="page-links" aria-label="School phase pair tables">'
        + "".join(f'<a href="#pairs-{code}">{esc(phase_labels[code])} pairs</a>' for code in PHASES)
        + '</nav>' + _pairs(data, phase_labels) + '</section>'
        + _sources(schools) + '</main>')
    source = next(value for key, value in schools["sources"].items()
                  if key == "official-pages-crawl-3.html.json")
    footer = (
        '<footer><p class="name">School data: Department for Education, '
        f'<a href="{esc(source["url"])}">Schools, pupils and their characteristics</a>. '
        'Contains public sector information licensed under the '
        '<a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">'
        'Open Government Licence v3.0</a>.</p>'
        '<p><a href="index.html">Spending</a> · <a href="taxes.html">Taxes</a> · '
        '<a href="who-pays.html">Who pays</a> · <a href="methods.html">Methods</a> · '
        '<a href="life.html">Year by year</a> · <a href="methods.html#about">About</a> · '
        '<a href="methods.html#corrections">Corrections</a> · '
        '<a href="data/life.json">Download life data (JSON)</a></p></footer>')
    pairs = {pair["id"]: [pair["left"], pair["right"], pair["display"],
                          pair["from_period"], pair["to_period"]] if pair["available"] else None
             for pair in data["comparisons"]}
    compact = lambda value: json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c")
    script = ('var DEFAULT_YEAR=' + str(data["default_anchor"]) + ';var PHASE_LABELS='
              + compact(phase_labels) + ';var PAIRS=' + compact(pairs) + ';' + JS)
    result = (
        '<!doctype html><html lang="en-GB"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Life, year by year | UnpoliticalAF</title><link rel="icon" href="icon.svg">'
        '<style>' + CSS + '</style></head><body class="nojs">'
        '<a class="skip" href="#main">Skip to content</a>'
        '<nav class="site-nav" aria-label="Primary" data-pid="primary-nav">'
        '<span class="brand">UnpoliticalAF</span>' + navigation + '</nav>'
        + body + footer + '<script>' + script + '</script></body></html>\n')
    if len(result.encode("utf-8")) >= 500000:
        raise ValueError("Life page must be strictly below 500000 bytes")
    return result


build = render
