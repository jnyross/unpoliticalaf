# UnpoliticalAF — autonomous build handoff

## Mandate and current state
Help people understand where UK public money is spent and how taxes are raised, in plain, impartial English. Deliver a small, trustworthy product before extending coverage. This document prepares work; it does **not** create or start agents. Follow `AGENTS.md` for workflow, ownership, review and escalation. The sister project at `/home/john/projects/un-political` is read-only context, not an implementation mandate.

**Assumptions, not user decisions:** a locally runnable web experience is the first delivery target; no new stack is approved. Propose boring, reversible defaults with rationale and replacement cost; record decisions before implementation. Do not infer approval from historical sister-project technology. The exact first usable fiscal period remains undecided until source availability is reviewed.

## Roles and handoffs
- **Delivery lead:** maintain a bounded backlog, assign file ownership and dependencies, record assumptions/decisions, enforce gates and assemble completion evidence. Do not approve your own fiscal claims.
- **UK fiscal-data researcher:** select official sources, define the data contract and reconciliation, explain scope and uncertainty, and hand implementation a reproducible fixture plus source register.
- **Implementation:** consume the accepted contract, build the accessible mobile slice and automated checks, and document local run/test commands. Do not silently alter fiscal definitions to fit the UI.
- **Independent QA/data reviewer:** independently check source figures, transformations and explanatory claims; run the delivered app in a genuine browser and record findings. Must not be the author of the work reviewed. Return defects to their owner; unresolved material defects block completion.

## Gate 1 — research and data contract, before app implementation
Researcher proposes, and independent reviewer verifies, one common usable period covering **both expenditure and tax revenue**. Prefer official outturns when available, but do not invent a year or imply that estimates are actuals. Use official publishers (for example ONS, HM Treasury, HMRC and OBR); search/landing pages alone are not a data citation.

Publish a source register and machine-readable fixture/schema. Every displayed figure must resolve to:
- Official source URL, publication/release and retrieval dates, exact table/series identifier and row/column or equivalent locator; retained input/version and reproducible extraction steps.
- Period start/end and explicit fiscal-year, calendar-year or other basis; UK/geographic and public-sector coverage; accounting basis and exclusions.
- Unit and scale; nominal/current or real/constant prices, base year where applicable; status **actual / estimate / forecast** as described by the publisher (explain any mapping).
- Revision vintage, known provisional status, revision history/change policy and update procedure. Never silently replace historical figures; rerun validation and review changed claims.

Define headline totals, a manageable set of spending categories and tax categories, and their hierarchy. Explain borrowing/non-tax receipts separately where needed: tax revenue is not all receipts, spending is not necessarily matched by tax, and debt is a stock rather than annual spending. Never compare differently scoped totals as if equivalent. If bases differ, show a documented bridge with each adjustment and an explicit unreconciled remainder, or keep the totals visibly separate and explain why no valid bridge is available.

Set reconciliation rules before displaying charts: sum unrounded compatible components against the source total; distinguish scope adjustments, omitted categories and genuine residuals. Specify a numerical tolerance justified by source precision, fail unexplained differences beyond it, and disclose residuals rather than force-balancing them. Round only presentation values, label the rounding policy and warn that displayed rounded parts may not add exactly. Store source precision.

For any inflation-adjusted comparison, record the official deflator URL/series, vintage, base year, period alignment and formula (for example nominal × base index / period index). Label real and nominal values distinctly; do not mix them or silently substitute CPI for a fiscal deflator. If no defensible comparable series exists, omit that comparison and explain the limitation.

**Gate evidence:** reviewer sign-off on source register, fixture/schema, chosen period, sampled original-source values, reconciliation outputs and deflator method (or explicit no-comparison decision). Missing, conflicting or irreconcilable data stops implementation of the affected claim; escalate rather than fabricate.

## Gate 2 — first usable local slice
Build only after Gate 1. One locally runnable experience must explain a spending total and breakdown **and** tax revenue total and breakdown for the accepted period. Give plain-English definitions, source links, period/unit/prices/status labels, scope caveats and reconciliation explanations next to or directly reachable from figures. Clearly separate facts from interpretation; avoid partisan framing and misleading precision. No forecast presented as observed spending or revenue.

Use responsive mobile layouts, semantic headings/controls, keyboard operation, visible focus, sufficient contrast, meaningful accessible names, and text/table alternatives to charts; never rely on colour alone. Include loading/empty/error states and readable narrow-screen layouts. Keep data transformation separate from presentation and provide repeatable local start, test and data-rebuild commands. Additional years or features are out of scope until this slice passes review.

## Gate 3 — observable completion proof
Delivery lead collects an evidence index with actual commands, dates, results and artifact paths; proposed tests or screenshots alone are not passes:
- [ ] Data validation checks source identifiers, periods, units/prices/status, missing/duplicate values, category hierarchy and documented reconciliation tolerances; retained raw inputs reproduce the fixture.
- [ ] Independent fiscal review checks original official tables against both headline totals and sampled spending/tax categories, scope bridges/residuals, rounding, status/vintage and any real-terms calculations. Record discrepancies and their resolution.
- [ ] Automated unit/integration checks exercise transformations, invalid data and rounding/reconciliation edge cases; document exact rerunnable commands and passing output.
- [ ] Genuine browser end-to-end tests start the real local application and visit both spending and revenue views, follow source links, verify period/status labels and error states, and exercise keyboard navigation and a narrow mobile viewport. Record browser/version, commands, assertions and results; mocks, static HTML inspection or a claimed browser run are insufficient.
- [ ] Independent reviewer manually checks mobile readability, chart/table equivalence, focus flow and plain-language neutrality, with screenshots and findings; accessibility automation supplements rather than replaces this check.
- [ ] Fresh-checkout/local setup instructions work, known limitations are explicit, no material review defects remain, and the lead links reviewer approval to the exact reviewed version.

Completion means the bounded slice has this evidence and independent approval, not that the entire future product is complete. If a browser, source or reviewer is unavailable, report the missing proof as a blocker; do not mark the gate passed.

## Stop and approval boundaries
Routine local research, tests and reversible implementation within the agreed slice may proceed only once a real team is activated under `AGENTS.md`. This readiness task authorizes documentation only: no app implementation or live automation now. Stop for user approval before deployment/publication, paid services/subscriptions, installing or activating factory automation or schedules, remotes, commits, settings changes, destructive operations, or changes to the sister repository. Do not run opt-in bootstrap scripts implicitly. Escalate scope expansion, material fiscal ambiguity, missing independent review and any decision requiring new authority. Never imply that these instructions establish a running native team; activation is a separate user action.
