# Manual accessibility pass

This protocol prepares the human keyboard and screen-reader checks for Access
level 4 in [the rubric](rubric.md). It records observed results, not a claim of
WCAG conformance. Automated checks and all lower rubric levels remain required.
No manual pass has been performed by creating this document.

## Run setup and coverage

Record the exact build before testing. Use tester codes, not personal details.

| Run | Evaluated commit (from controller) | Site URL/build | Date | Tester code | OS/device version | AT/version | Browser/version | Width/zoom | JavaScript on/off |
|---|---|---|---|---|---|---|---|---|---|
| To fill | | | | | | | | | |

Start a fresh session for each combination below. Record exact versions and
settings, including keyboard navigation and screen-reader verbosity. Run:

- Keyboard only, with the screen reader off, on Windows and macOS.
- NVDA on Windows with Firefox, or JAWS on Windows with Chrome/Edge. One Windows
  screen reader is required; record which was used.
- VoiceOver on macOS with Safari.
- VoiceOver on iOS with Safari, using touch as well as an external keyboard if
  available. A touch-only run must not depend on an Escape key.

Test **every HTML page** in the evaluated build, starting with the two current
pages below. Add any new page before calling a run complete. Test each applicable
element on each page, not a sample. Shared markup does not exempt an instance.
Repeat with JavaScript disabled, documenting unavailable enhanced controls as
described below. Include a 360 CSS-pixel-wide viewport and desktop layout, plus
200% text zoom and 400% browser zoom/reflow where supported. Record the actual
mobile settings rather than assuming desktop zoom applies to iOS.

| Page | Required inventory and locations |
|---|---|
| [index.html](../site/index.html) | Skip link to #main; all three view buttons and #view-label; all eight Quick answers summaries in #answers and their links; all chart/table groups listed below; every focusable number that opens #tip; all header, in-page, source, methods, footer, licence and JSON links. |
| [methods.html](../site/methods.html) | Skip link to #main; headings and definitions; Source files table and each spreadsheet link; About (#about), Corrections (#corrections); all data, source, licence and footer links. No view buttons, number-source buttons or disclosures are currently present: record those as N/A for this page, with reason. |

On the home page, apply the chart/table and source-note checks to #hundred,
#items (including #debt), #total, #decades and its five cards
(#decade-health, #decade-education, #decade-social, #decade-defence,
#decade-interest), and all ten cards in #areas (#area-social, #area-health,
#area-general, #area-education, #area-economic, #area-defence, #area-order,
#area-housing, #area-environment, #area-culture). Check every table, including
methods' Source files table. Check all three money views where applicable;
the decades charts keep their stated GDP basis.

For the current build, the home page has eight Quick answers disclosures and
19 table disclosures. Treat these as an inventory cross-check, not a substitute
for inspecting the evaluated build. Record each disclosure by page, enclosing
section id and summary text; distinguish numbers by section, nearby text,
table row/column or source-cell reference. Add coverage rows for each instance.
Hidden content must be opened before its controls and cells are checked.

## Keyboard-only checklist (screen reader off)

For each page and each inventory item, record pass, fail or N/A with a reason:

- [ ] From a reload, Tab reaches the visible Skip to content link; Enter moves to
  #main and subsequent navigation continues there. Headings/anchor destinations
  are visible below sticky controls.
- [ ] Tab and Shift+Tab reach every link, button, disclosure and enhanced source
  number in meaningful reading order. Focus is visible at desktop and narrow
  widths and zoom, with no trap, unexpected jump or obscured focused element.
  Record the effort of moving through the many source-number tab stops.
- [ ] Each of the three view buttons works using Enter and Space. Exactly one
  appears selected; the visible view label, chart units and values match it.
  Focus stays on the activating button. Repeat switching in both directions,
  including after opening tables and source notes.
- [ ] Each Quick answers summary and each table summary toggles with Enter and
  Space. Open content is reachable; closing removes hidden descendants from
  the tab order and leaves focus usable on the summary.
- [ ] Every source number can be focused and opens the correct table/cell note
  with Enter and Space without unwanted page scrolling. Check the first
  activation, a different number, and the same number again after dismissal.
  Escape dismisses #tip and leaves focus on the triggering number. The fixed
  note must not hide the focused item or prevent access to subsequent content.
- [ ] Every table can be reached, read and scrolled when necessary using the
  keyboard. Captions, row labels, units, years and footnotes remain visible or
  reachable; no data is clipped at narrow widths or zoom. Check forecast,
  negative and missing-value rows where present.
- [ ] Every navigation, in-page, source-file and download link has meaningful
  text and the expected destination. Browser Back returns to a usable position.
  Do not require a spreadsheet viewer to behave like an HTML page; verify the
  linked file is the intended source.
- [ ] With JavaScript off, both pages still expose all prose, figures, native
  answer/table disclosures, tables and source-file links. View buttons and
  enhanced number-source popovers are absent; the default inflation-adjusted
  charts and their units remain understandable. Do not count absent popovers
  as evidence of a keyboard fallback; check source-file access via methods.

## Windows screen-reader checklist (NVDA or JAWS)

Use the screen reader's normal browse mode for reading and focus mode when needed
for controls. Use heading/landmark navigation, the links list (NVDA Insert+F7,
or the JAWS equivalent), T to reach tables, and table cell navigation such as
Ctrl+Alt+arrow keys. Record any changed key bindings.

Apply every item on **both pages**, to **every applicable inventory instance**:

- [ ] Page title, language, main landmark, heading order and reading order identify
  the page and its sections. Skip link and all navigation links work without
  losing position; link text makes sense in the links list.
- [ ] View buttons announce their complete names and pressed/unpressed states.
  After each activation the selected basis and units can be discovered and
  match the content being read; hidden alternative chart values are not read.
- [ ] Each Quick answers/table summary announces its name and collapsed/expanded
  state. Activating it exposes the right content in reading order; closing it
  removes that content from reading and focus navigation.
- [ ] Each source-number button announces a meaningful number and usable context.
  Enter/Space reveals the correct source text, which is announced or readily
  discoverable without moving focus unpredictably. Reopening the same source,
  switching sources, Escape dismissal and continuing navigation all work.
  Record a failure if the status note is silent or cannot be found.
- [ ] Every table announces its caption and correct column and row headers while
  moving between cells. Read every row/column, including units, dates, forecast
  labels, missing values and negative values. Source buttons inside cells do
  not destroy the table context.
- [ ] Each chart's meaning and values can be obtained from adjacent text and its
  table. No task depends on seeing colour, a dashed line or an image. Forecast
  status and definition/series-break notes are available as text.
- [ ] Methods' source filenames, definitions, About, Corrections and all footer/
  download links are readable and operable. Repeat the reading, disclosure and
  table checks with JavaScript disabled.

## VoiceOver on macOS checklist

Enable Safari's keyboard navigation through all controls. Use Control+Option
(VO) with arrow keys to read, VO+Space to activate, and VO+U for the rotor.
Use the rotor for headings, links and tables, and interact with each table to
read its cells. Record any different VoiceOver settings or commands.

- [ ] Repeat the entire Windows checklist above on both pages, using VoiceOver
  commands, for every inventory instance and every applicable view/state.
- [ ] Rotor and sequential navigation both reach the main content, all headings,
  links, buttons, summaries and tables without skipped or duplicated content.
- [ ] Names, pressed states, expanded states, source-note updates and table
  headers are spoken correctly. Escape closes the source tip with a usable
  focus position; repeat activation of the same number is discoverable.
- [ ] Repeat with JavaScript off and at the recorded zoom/narrow settings.
  Check sticky controls and the source note do not obscure content or focus.

## VoiceOver on iOS checklist

Record iPhone/iPad model, iOS and Safari versions, orientation and text size.
Use swipe left/right for sequential reading, the rotor for headings, links and
controls where available, and double-tap to activate. Use table navigation
provided by the device, and also verify linear reading through every table.

- [ ] On both pages, reach all inventory instances by swipe/rotor navigation;
  headings, landmarks, links and reading order identify the content.
- [ ] Double-tap each view button and every answer/table summary. Correct names,
  selected/expanded states and newly visible content are spoken. Repeat all
  applicable views; orientation/text-size changes do not lose content.
- [ ] Double-tap every source number; its correct table/cell note is spoken or
  can be found. Reopen the same source and switch to another. Dismiss the note
  using touch alone and continue from a usable position. If dismissal requires
  a pointer, sight or unavailable key, record an issue; do not mark it N/A.
- [ ] Read every table with row/column context, caption, units, forecast labels
  and missing values. Obtain all chart information from text/tables.
- [ ] Activate navigation and source/download links; return to the page and
  continue reading. Repeat applicable reading/disclosure/table checks with
  JavaScript off. Check portrait/narrow layout, larger text and zoom supported
  by the device for clipping and overlays.

## Coverage, findings and retest record

Copy rows until every page/element and required environment/state is accounted
for. Do not mark unchecked work as passed. Use the coverage record to reference
detailed findings; a shared finding may cover multiple identified instances.

| Run | Page / section / element | Environment and JS/view/open state | Checklist item | Result (pass/fail/N/A) | Finding or N/A reason |
|---|---|---|---|---|---|
| Not run | | | | | |

Use the requested results table for both failures and completed passes. Include
the page, element, steps, expected/actual behaviour and coverage reference in
Issue. For a passing check write "None found" and its coverage reference. In Fix,
record pending work or the change and successful retest date/build/environment;
do not describe an untested change as fixed.

| Tester | Date | AT/browser | Issue | Fix |
|---|---|---|---|---|
| Not run | — | — | No human checks recorded | — |

Run decision: **Not run.** Complete only after every required coverage row is
recorded and every failure has a recorded fix and successful retest on the final
evaluated build. Keep failed observations and retest history. Publish or link the
anonymous results as evidence with the evaluated commit/date before claiming
Access 4; automated results alone cannot establish it.
