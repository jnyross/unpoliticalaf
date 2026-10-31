# Private work-data foundation

This foundation implements the [frozen work-data contract](life-work-data-source-contract.md)
without activating a public life story. It adds no generated data path, public
output, dependency or source acquisition. The original eight public files and
setup/build/verify interfaces remain unchanged.

## Source custody and projection

The closed input set is the 20 files in `data/life/work-data-sources.json`:
two complete annual calendar CSV responses and 18 complete SDMX definitions
and codelists. Six APS218 shared codelists are the adopted supplement recorded
in the frozen contract, not part of the original freeze. Research receipts,
rejected queries and the separate methods HTML are not hidden inputs.

`scripts/work_data_projection.py` reopens the pinned register and each source.
It checks regular files, canonical paths, links, complete directory membership,
stored hashes/lengths and byte-identical recovery of the UTF-8 envelopes. The
projection exists only in memory. It carries source locators, the full selected
definition/code entries and annotations, and every literal CSV field, physical
row number, bound query code and exact integer value. No derived data file is
written. Raw units are Persons; the presentation unit contract is people.

The source byte totals are 690,629 recovered original bytes and 749,071 stored
bytes. They are custody totals, **not** an actual candidate review measurement.
All whole sources remain normal review inputs. The controller must measure the
combined implementation, source diff and candidate metadata against the unchanged
1,000,000-byte limit. No stripping, splitting or generated-input reclassification
is introduced.

## Independent verification

`scripts/check_work_data.py` uses its own register reader, expected URLs,
semantic assertions and projection reconstruction. It does not import producer
parsers, constants or expected results as an oracle. With a supplied projection
it never calls the producer. With no supplied projection it also compares two
fresh producer projections for determinism, then audits against reopened bytes.

The checker requires the full 660/300 unique row grids: all 11/5 calendar
periods, total and nine occupation groups, all persons/males/females, and both
Value 20100 and Confidence 20701. It binds names to the correct dataset's codes,
including capitalised measures Description annotations while retaining their
lowercase descriptions. It requires UK geography, Count, normal/free source
status and exact nonnegative integer cells. Missing or noninteger cells fail.
Source hashes remain the authority for every published cell.

DATE_NAME and the requested calendar DATE bind the periods. The wrong APS210
2019 end annotation and APS218 2025 start annotation survive unchanged. APS210
2011-12 remains without annotations. Version 0, absent comments and dataset
update timestamps are not a complete correction or weighting-vintage audit.

The checker verifies that published totals cannot be treated as an exhaustive
sum of the occupation groups. It publishes no shares, deltas, SOC joins,
interpolation, ratios, uncertainty calculation, significance or causation.
Confidence 20701 stays literal and uninterpreted. Suppression and indicative
definitions remain separately unknown. Scope cautions identify the frozen
population and separate methods cross-check; they do not claim that these
CSV/SDMX files independently prove QMI or revision-notice wording. The RTI
period is kept separate from the Northern Ireland response adjustment, whose
start period is not stated in the retained notice.

## Checks and evidence boundary

`make verify` calls the work-data gate before public-output checks and includes
`tests/test_work_data.py` through existing unittest discovery. Focused fixtures
challenge both custody readers, projection mutations, raw semantic mutations
beneath custody, full grid closure, exact code/label binding, misleading scope,
nonfinite/duplicate JSON, unsafe paths and links, metadata repair, unexpected
public files and derived-file writes.

This implementation was prepared by file inspection and editing only. No
programs or tests were executed by the bounded worker. The independently
written checker and read-only code inspection do not replace exact-candidate
source/implementation reviews. The controller owns payload measurement,
credential-free Boat setup/build/verify twice, reproducibility, browser/HTTP
private-path checks, publication, deployment, exact eight live hashes and
cleanup. No passing gate, deployed state, v2 product score or human acceptance
evidence is claimed.
