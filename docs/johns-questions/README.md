# John's questions

Questions John has said the site must answer. Goal audits test the site against
every one of them, and any part the site can't answer yet becomes a gap, then a
ticket. The site keeps improving until it answers them all.

The questions live in [questions.json](questions.json).

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
