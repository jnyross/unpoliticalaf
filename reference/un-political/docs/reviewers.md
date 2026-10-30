# Independent impartiality reviews

This protocol prepares the human review evidence for Impartiality level 4 in
[the rubric](rubric.md). It does not record completed reviews or raise the score.
The public corrections log and every lower impartiality level are also required;
in particular, the current lack of party pages still limits level 3.

## Choose two reviewers

Invite two people who describe their own political leanings as opposing, for
example one broadly left-leaning and one broadly right-leaning. Ask each how
they would describe their leaning in a short phrase and confirm that the two
descriptions represent opposing views. Do not infer politics from identity,
voting records or social media. Two people from the same leaning do not meet
this requirement; disagreement about one policy alone is not enough.

Use people independent of writing, funding or running the site who are willing
to challenge its framing. Ask each to declare relevant party/campaign roles,
financial interests and prior involvement with the site. A party role need not
exclude someone, but disclose a relevant conflict so readers can assess it.
Record any payment or other incentive; do not make payment conditional on a
favourable review. Do not invent an affiliation or recruit on the assumption
that someone represents all people with that leaning.

Before review, obtain each person's agreement to publication of their comments,
self-described leaning, relevant conflicts and the site's responses. Offer
stable public codes R01 and R02 instead of names. Publish a name only with
explicit agreement. Keep contact details and private recruitment correspondence
out of the repository and website. If someone declines publication, retain no
private review material in public files and recruit another reviewer before
claiming the criterion. Do not contact anyone merely by creating this protocol.

| Reviewer code | Consented public attribution | Self-described leaning | Relevant conflicts / incentive | Publication consent date |
|---|---|---|---|---|
| R01 | Pending | Pending | Pending | Pending |
| R02 | Pending | Pending | Pending | Pending |

## Give both the same reading pack

Record the URL/build, evaluated commit supplied by the controller, data release,
invitation date and agreed return date. Freeze that version for both initial
reviews; later fixes must be identified separately. Give each reviewer:

- Every page of the evaluated site: currently [home](../site/index.html) and
  [methods](../site/methods.html), including all Quick answers, all three money
  views, chart tables, forecast/definition notes, About and Corrections. Include
  every party page and independent assessment if these exist in a later build.
- The methods explanation, linked official source files and open-data download,
  so they can trace any number or comparison they challenge.
- [The rubric](rubric.md), especially Impartiality levels 1–4 and Honest context,
  and this protocol explaining how comments and responses will be published.

| Review round | Site URL/build | Evaluated commit | Data release | Invitation date | Return date | Pack sent to both |
|---|---|---|---|---|---|---|
| Not started | | | | | | |

Ask them to read independently before seeing the other's comments. Use the same
brief for both:

> Please read the whole site, including its tables, source notes and methods.
> Identify wording, labels, omitted context, ordering, year choices or visual
> treatment that could favour a political side. Are actual figures and forecasts
> clear? Are the comparisons and definitions fair and equally applied? Where
> party plans are shown, are the fields, ordering and length limits the same,
> and are judgements attributed and linked to independent bodies? Identify the
> page/section, quote the passage or describe the chart, explain your concern,
> and suggest a change or evidence to check. Say which pages you read, any you
> could not review, and whether you found no concerns. You do not need to endorse
> the site or agree with the other reviewer. Your comments and our responses
> will be published with the version reviewed.

Do not ask for approval of the site's political position. A completed review
may be critical. Ask for missing page coverage rather than treating a partial
review as complete. Give both the same opportunity to clarify concerns.

## Record comments and responses

Assign each comment an id such as R01-C01. Preserve the reviewer's wording and
page/section reference, date, version reviewed and any suggested evidence.
Include favourable, critical and "no concerns" statements; do not publish only
selected praise. Label any reviewer-approved edit or necessary privacy redaction
and its reason. Do not silently rewrite criticism or publish private contact
information. Where publication consent is missing, mark the review pending.

For each comment, the site owner records a dated response and status:
accepted, partly accepted, declined with reason, or open. State the evidence
and reasoning, exact change/location and version where applicable. A declined
comment still needs a substantive response. Leave unresolved disagreements
visible. Link any factual correction to the existing
[corrections log](../site/methods.html#corrections); this protocol does not replace
that log.

Copy one row per comment, including a row for a completed "no concerns" review:

| Comment id | Reviewer code | Date / reviewed commit | Page / section | Reviewer comment (verbatim) | Site response / reason / date | Status | Change version / correction link / retest evidence |
|---|---|---|---|---|---|---|---|
| Pending | | | | No review received | No response yet | Open | |

Send the recorded comments and responses back to their author to check
attribution and transcription. Record their confirmation or corrections; do not
require them to agree with a declined response. When fixes affect framing or
figures, ask both reviewers to read the final changed sections and record any
follow-up comments against the new version. Keep the original review and all
responses. If one withdraws consent before publication, resolve that gap with
another opposing-leaning reviewer rather than claiming a completed pair.

## Publish and decide

Publish both complete reviews and the site's dated responses together in a
dedicated **Independent reviews** section of **methods.html**, with the planned
stable target **methods.html#independent-reviews**. That section does not exist
yet; adding it and publishing actual reviews is subsequent work, not a result
of this docs-only ticket.

The section must show the protocol link, dates, versions read, each reviewer's
consented attribution/code, self-described leaning and relevant disclosures,
coverage, complete comments and responses (including open/declined points),
correction links and follow-up history. Link to it from the methods page's
navigation or contents so it is discoverable. If a separate full transcript is
needed for length, link it there and retain a response for every comment.
Anonymous reviewer codes are sufficient; do not expose contact details.

Before recording completion, the owner checks that both opposing leanings are
documented, both reviews cover the same full initial build, follow-ups identify
changes, publication consent is recorded and every comment has a public
response. Read back the published methods section and correction links and
record the actual public URL, publication date and evaluated version below.

| Publication date | Actual public section URL | Published version | R01 coverage/consent checked | R02 coverage/consent checked | All comments/responses visible | Outstanding issues |
|---|---|---|---|---|---|---|
| Not published | — | — | Pending | Pending | No | Human reviews and publication not yet done |

Protocol status: **Not started.** Neither two invitations nor this document is
evidence of Impartiality 4. Record a later rubric row only when the published
reviews/responses, corrections log and all lower-level checks are evidenced.
