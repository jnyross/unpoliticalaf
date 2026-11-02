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
6. **Folding** (`fold()`, run by `page()`): on a phone each section shows its
   heading, its answer and its main chart, and everything after that (other
   charts, tables, limits, official words, sources) goes into one "More on …"
   disclosure that names what it holds. The main chart is the first chart
   (`<figure>`, `.bars` or `.cmp-list`) that is not already inside a
   disclosure or aside; `keep_chart()` moves it, with a caption paragraph
   straight before it, up under the answer. A long comparison list keeps its
   first `KEEP_ROWS` rows in view. Put `<!--keepfold-->` in a section to stop
   this. The answer is everything up to the end of the section's
   first `.answer` box, or everything before a `FOLD` marker. Put `FOLD` right
   after the chart or sentences that answer the section's question, and keep
   anything needed to read that answer correctly (an illustration's label, a
   definition the answer depends on) above it. `NOFOLD` keeps a section open;
   sections with neither an answer box nor a marker stay open too.
   `<details>` works without JavaScript.

## Components

- `spark()` (html.py) and `year_spark()` (pages_life.py): a small dot chart of
  one measure for every year. The chosen year is a large dark dot, missing years
  get no dot, and a dashed line marks a definition change (dots either side are
  not joined). The scale fits the data, so the caption states its range and
  that it does not start at zero. Year pages show one under each answer; the
  home page cards use it without a caption, explained once above the cards.

- **Bars** (`bars()`): shares and amounts for one year. Value at the right end
  of the label, so it is read before the bar.
- **Change bars** (`change_bars()`): rises go right and falls go left from a
  shared zero line. Always pass the before and after amounts as the note, so a
  big percentage on a small base is not mistaken for a big sum.
- **Line charts** (`line_chart()`): with two or three short series names the
  lines are named at their ends instead of in a key. Gaps and definition
  breaks are drawn as gaps and dashed lines, never joined. The visible title
  sits above the chart; the SVG's `aria-label` repeats it for screen readers.
- **Small multiples** (`small_multiples()`, or `groups_chart()` in
  `pages_life.py`): when more than three groups matter (age groups, job types,
  tenures, nations, regions), draw one small panel per group instead of a
  crowded line chart. Every panel uses the same scale, names its group above
  it, writes its latest value at the line's end and shows the other groups as
  faint grey lines for context. One summary covers every group (first and
  latest values, missing years, each side of a break read separately) and one
  readout marks the chosen year in every panel. Two columns on phones, three
  on wider screens. Keep groups in their official order, not ranked.
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
- **Tracing figures** (`builder/trace.py`): every page gets the records of the
  figures it shows, and tapping a number opens a panel with its source, period
  and cell or calculation. Each source line links to `figures/<source>.html`,
  a record of every figure used from that source. Nothing to do per page: wrap
  numbers with `num()` as usual. When a published mistake is fixed, add it to
  `CORRECTIONS` so it appears on `corrections.html`.
- **Margins of error** (`builder/uncertainty.py`): survey figures carry their
  95% margin of error after the number (`pm()`, grey `±`), but only where the
  publisher gives one: ONS A11 for the latest LFS employment rate, Nomis APS
  for nations and regions, Nomis ASHE coefficients of variation (margin =
  1.96 × CV × figure) and ONS travel intervals. Never invent one; where a
  source gives none, say so (see `uncertainty.html`). Each life topic gets a
  "How sure?" line (`topic_line()`), and comparisons say whether a change is
  bigger than the two margins combined, √(a² + b²) (`check_sentence()`), which
  `make check` recalculates.
- **Illustrations** keep the dashed border and the "Illustration, not a
  statistic" tag. Don't restyle them to look like measured figures.

## Rules

- Colours: ink `#16191d`, greys, one link blue and one amber for limits and
  definition breaks. No party colours, no red and green for up and down.
- Text at least 15px in charts at phone width; touch targets at least 44px.
- The menu is one row on wide screens. Below 48rem it becomes a grid of two
  rows of four, so every section is visible without scrolling; the page never
  scrolls sideways. `make a11y` checks 360px and 1100px.
