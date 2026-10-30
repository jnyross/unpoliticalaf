# Payer source acquisition seed

This is source preparation, not an accepted extraction or a deployed feature.
The source register is `data/payers/sources.json`. Each original official response
is retained in full. Binary workbooks are unchanged. HTML is stored in a lossless
ASCII JSON envelope to avoid changing upstream whitespace or weakening repository
whitespace checks. Read `original_response`, encode it as UTF-8, then verify the
original `sha256` and `bytes`. Verify `stored_sha256` on the envelope as well.
No source bytes were trimmed. The source snapshots stay private and must never
be copied wholesale into `site/`.

The research methods/corrections documents give a broader exploration than this
seed. Only register-listed sources are present. Do not cite other research-only
files as retained here. In particular, the collated HMRC workbook and supporting
HTML are not included. Do not display the 36.7-million taxpayer count from this
seed: it needs a separately retained source cell. The small Table 2.4 ODS supports
percentile shares and income breakpoints.

Intended first public scope:
- HMRC 2023/24 estimated outturn Income Tax liability shares for positive-liability
  taxpayers. Bottom50%, top10%, top1% overlap; they are not shares of all UK taxes.
- ONS Table8 published quintile direct/indirect/combined percentages of gross
  income, with row22 indirect tax as a share of expenditure beside the income
  measure. Use published total row15, not sums of rounded components.
- Separate populations and years: UK individual Income Tax liabilities versus
  UK people in private households ranked by size-adjusted household disposable
  income. Five equal-person groups, not equal-household groups.
- Clear model limits: remitter is not economic burden; ONS allocates indirect
  taxes under assumptions, includes student-loan repayments in direct taxes and
  does not allocate Corporation Tax to households. Employee NI is direct,
  employer NI is allocated indirect. Neither panel gives complete all-tax incidence.
- Deferred lump-sum payments, temporary low income, sampling/measurement issues
  and alternative incidence assumptions must be visible near low-income results.
- No decile UI, no trend, no projections and no personal tax calculator initially.

All3 independent council reviewers accepted this narrow evidence interpretation
with limits, not the implementation. Reviewers could not reopen binary workbooks
or check hashes with their read-only tool. The implementation therefore still
needs independently reopened raw-cell verification, hash checks, negative tests,
source-note retention and exact-candidate product/browser/accessibility review.
A renderer must not ship on these preparation notes alone.
