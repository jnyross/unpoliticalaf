# John's questions

Questions John has said the site must answer. Goal audits test the site against
every one of them, and any part the site can't answer yet becomes a gap, then a
ticket. The site keeps improving until it answers them all.

The questions live in [questions.json](questions.json).

The [baseline inventory](baseline.json) retains all 94 probe IDs, original probe
wording and John's unchanged `asked`/`also_asked` text from commit
`3e6e34f08a2233787d2a70e43a56fbaaa257501f` (84 with evidence, 10 open).
Tests reconcile the current population to it. Correcting an invalid premise
requires retaining the original probe wording and reason in `history`, not
silently dropping or easing the question. See the [evidence map](inventory.md).

## Adding a question

John asks in the project chat, for example: "New question: how does the UK
tax, debt and spending compare to other major nations?" A worker then adds an
entry to `questions.json`:

- `asked`: John's words, unchanged. When John later adds a part to the same
  question, it goes in `also_asked`, also unchanged, with new probes.
- `reading`: how the question is read, in one or two sentences, where it could
  mean more than one thing (for example, "major nations" read as the G7).
- `probes`: the multiple-choice questions a newcomer should be able to answer
  from the site if it really answers John's question. Write enough probes to
  cover every part of the question (here: tax, debt and spending).

Each probe is in one of two states:

- **Answered:** it has `options`, the correct `answer`, a `why`, and
  `evidence`, the exact sentences on the built site that give the answer. CI
  (`make test`) fails if the site stops saying them.
- **Open:** it has no `evidence` yet, and a one-sentence `gap` saying what the
  site is missing. The worker who closes the gap takes the answer from the
  official source, not from the site, then adds the options, answer and
  evidence.

An evidence-complete probe may give a precise, sourced limitation when retained
official evidence cannot support the requested statistic, with any nearest
measure clearly distinguished. That does not mean the statistic is measured.
In particular, J4.3 withdraws the unsupported household-tax aggregate rather than
replacing it with another percentage. This follows the current completion scope.

Probes are written by whoever adds the question, before anyone works on the
site, so the site is tested against the question rather than the other way
round. Never change John's wording, and never drop a probe because the site
can't answer it.

## Commands

    python scripts/johns_questions.py check   # answered probes still on the built site
    python scripts/johns_questions.py gaps    # one line per open probe
    python scripts/johns_questions.py pack    # answered probes as a reader question set

## How audits use them

See "John's questions" in [goal-rubric.md](../goal-rubric.md).

An evidence string check is not source verification, reachability or reader
comprehension. Source regressions and independent review supplement it. Final
reader success remains an independent same-candidate evaluation: five readers,
seven fresh grouped sessions each, every probe at least four of five correct.
No comprehension score or final acceptance is claimed by this inventory.
