# Design guide

How pages on Unpolitical should look and read. The goal asks for restrained
white-and-grey styling, phone first, answers before methods, and everything
working without JavaScript. All styles live in `CSS` in `builder/html.py`.

## Page order

1. **Question as the h1.** Use the reader's own question, not a topic name.
2. **Key figures** (`keyfigs()`): two or three big numbers with a plain
   sentence each, for the answer at a glance. The first is usually wide.
3. **Answer box** (`.answer`): the same answer in full sentences, with the
   period and population.
4. **On this page** (added by `page()` when a page has three or more `h2`
   headings with ids). Give every `h2` an id.
5. **Sections**, each in this order: question or finding as the `h2`, chart,
   "Show … as a table" (`details_table()`), limits (`.limit`), source line.

## Components

- **Bars** (`bars()`): shares and amounts for one year. Value at the right end
  of the label, so it is read before the bar.
- **Change bars** (`change_bars()`): rises go right and falls go left from a
  shared zero line. Always pass the before and after amounts as the note, so a
  big percentage on a small base is not mistaken for a big sum.
- **Line charts** (`line_chart()`): with two or three short series names the
  lines are named at their ends instead of in a key. Gaps and definition
  breaks are drawn as gaps and dashed lines, never joined. The visible title
  sits above the chart; the SVG's `aria-label` repeats it for screen readers.
- **Chart summaries** (`chart_summary()`): pass `kind` (and `ids` with `num`, so
  the numbers are traceable figures) to `line_chart()` and it writes "What the
  chart shows" under the chart: each line's first and latest values, the highest
  and lowest in between, and missing years. Each side of a definition break is
  read separately, even where the line is joined, and forecasts are given on
  their own. Write the facts only; never add a reason for a change.
- **Events vs breaks**: `breaks` are definition changes (amber dashed line).
  `events` are things that happened, such as Covid (grey dotted line, labelled
  at the foot of the chart); the summary says they show timing, not cause.
- **Readout**: charts with `kind` also get a small script (`CHART_JS`) that
  shows one year's values on tap, hover or arrow keys. It only adds to the
  chart; the summary and table work without it.
- **Year lists** (`.stats`): label, value and the value's own period, used on
  the year pages instead of three-column tables.
- **Source line** (`source_line()`): one or two sources are shown in full;
  more are folded into "Sources: publishers (N tables)" so they don't bury the
  page on a phone, but stay one tap away.
- **Scale line** (`scale_box()` in `pages_money.py`): a national total divided
  by the UK population, per year and per week. Always say it is an average
  across everyone, including children, and never call it a bill.
- **Glossary links** (`builder/glossary.py`): every word explained on
  `glossary.html` is linked, with a dotted underline, the first time it appears
  in ordinary text on each page (at most 12 per page). Headings, figures,
  tables, charts, existing links and text hidden from screen readers are left
  alone. To explain a new word, add it to `GROUPS` with the words that should
  link to it; don't write separate definitions on each page.
- **Illustrations** keep the dashed border and the "Illustration, not a
  statistic" tag. Don't restyle them to look like measured figures.

## Rules

- Colours: ink `#16191d`, greys, one link blue and one amber for limits and
  definition breaks. No party colours, no red and green for up and down.
- Text at least 15px in charts at phone width; touch targets at least 44px.
- The menu is one row. On phones it scrolls sideways inside itself; the page
  never does. `make a11y` checks 360px and 1100px.
