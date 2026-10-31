# School source foundation

This increment reads only the five complete inputs declared in
`data/life/school-sources.json`. It returns a private projection in memory.
It creates no generated data file, page, public path or output configuration.

`scripts/school_projection.py` preserves all 176 national observations:
eleven academic years, four class types and four size bands. Each row supplies
period, January census anchor, geography, population, observation status, phase,
band, notes and original provenance for every nested measure. Published numeric
strings retain their full precision. Derived means, shares and signed
comparisons carry formulas and source operands. Display rounding uses Decimal
original strings and ROUND_HALF_UP, with one decimal for means. Class and pupil
shares use their respective published totals within the same phase.

`scripts/check_schools.py` independently reopens all five files and the manifest,
checks stored and recovered bytes, parses the original metadata and page notes,
validates the closed grid and recomputes every projected measure. It imports no
producer reader, metadata map or arithmetic helper. Its optional producer call
supplies the candidate only after reopening originals. Projection row order is
not a statistical identity; exact original hashes still pin source row order.
`scripts/verify.py` invokes this check through the existing `make verify`
interface. Existing checks and the eight public paths are preserved.

The API metadata has indicator labels, columns and decimal places, rather than a
separate unit field. The projection records this basis for classes, pupils and
pupils per class. Catalogue, API version, release and methodology dates remain
separate. The catalogue's generic footnote is retained verbatim with a caution;
it does not replace the specific one-teacher class population.

The catalogue preview includes a local-authority `z` and blank fields. These
remain separately scoped raw preview data; `z` is not applicable, never a
national zero. The release acquisition retains its reported 308 headers and
redirect alongside the returned final-page body, without claiming final 200
headers or interpreting Content-Length 64 as that body's length.

The January census rule is quoted from the methodology. The projection gives
January and its annual anchor, without claiming an individually reported date.
January 2021 is present. The current methodology includes primary and secondary
KS1/KS2 classes for all years; older release definitions are not spliced in.
Primary overlaps the Infant/KS2 views, so no cross-phase sum is produced.

## Retained source discrepancies

Three published class totals exceed the sum of their three size bands:

| Academic year | Phase | Published total minus band sum |
| --- | --- | --- |
| 2015/16 | Primary | 1 class |
| 2015/16 | Secondary | 3 classes |
| 2017/18 | Secondary | 2 classes |

The projection records all 88 phase/year/indicator residual calculations, keeps
published totals as denominators and never normalizes away these discrepancies.
It assigns no unsupported cause to them. Every national published mean is checked
against pupils divided by its own class count at metadata precision, including
total rows. This does not substitute an average of local or band means.

## Verification boundary

`tests/test_schools.py` adds positive and negative checks for custody, original
whitespace, envelope encoding, duplicate JSON keys, path traversal and symlinks,
metadata identity, complete row coverage, numerics, denominator/phase mistakes,
notes, quality markers, residuals, stale producers, signed comparisons and the
private output boundary. Synthetic in-memory mutations explicitly isolate the
semantic checker beneath its byte pins; they never replace retained sources.

No project program, test, build or network operation was executed by the model
worker. Independent review and all controller checks remain pending. The controller
must measure the full normal candidate payload, including the retained inputs,
code, metadata and review overhead, against the strict 1000000-byte cap. The five
stored inputs total 409925 bytes and recover 393595 original bytes; these source
figures alone do not prove candidate fit. The research-only full CSV is not read.

This increment supplies no public page parity, browser, manual accessibility,
human study, neutrality or v2 acceptance score. The controller owns exact-candidate
review, Boat checks, reproducibility, publication and live smoke verification.
