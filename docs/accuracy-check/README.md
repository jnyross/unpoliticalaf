# Accuracy check: 50 figures traced to the publishers' files

**Current operating note — 5 November 2026.** The dated assessment below is
preserved, not fresh acceptance evidence. Its instruction to run the
source-writing "Accuracy check" workflow is superseded: that writer is disabled.
Use a reviewed intentional accuracy-check run against fresh publisher files in
credential-free Boat; workflow activation needs independent exact-candidate
review and must not enable dormant schedules or commit results to main. Store
post-freeze reports on the non-deploying evidence branch with the audited source
SHA, following [the current procedure](../standins/README.md).

Checked on 2 November 2026 against the site built from main at `e1bc5ec`.

**Result: all 50 figures match the publishers' own files.** One problem was
found and fixed along the way: the two occupation sources (Annual Population
Survey by occupation, SOC2010 and SOC2020) linked to the bare Nomis dataset
address, which returns a different slice of data. A reader following the link
could not reproduce the figures. The source records now give the exact Nomis
query, and the figures from it match.

## How the sample was drawn

- The population is every figure a reader can see on the site: each
  `<data data-fact>` number on every page except the figure records, with
  "not published" gaps left out. That is 9,723 different figures.
- 40 figures were drawn at random from all of them, and 10 more at random from
  the 2,599 figures on the headline pages (home, spending, taxes, who pays,
  household tax), so the main answers are covered too. The seed is fixed
  (`20261102`), so anyone can redraw the same sample.
- 27 of the 50 are read straight from a table. 23 are calculations (shares,
  averages, figures after inflation, per household). For those, every input was
  traced, 94 cells in all, from 29 sources and 24 different downloads.

## How each figure was checked

`scripts/accuracy_check.py` does both steps and imports nothing from the site
builder, so a builder mistake cannot hide itself.

1. **Page.** The text on the page (for example "£44.2bn") must round correctly
   from the figure's value.
2. **Publisher's file.** The GitHub workflow `accuracy-check.yml` downloads each
   source again from the publisher's website, not from the copy kept in this
   repository. Cells are read with readers written for the check (including a
   separate OpenDocument reader). Rows in Nomis and ONS CSV files are found by
   their labels (date, place, group), not by line number, so a newer edition
   is still read at the right row.
3. **Calculation.** Calculations are redone from the fresh cells, using the
   formula shown on the site's figure record, and the result must round to the
   text on the page.

22 of the 24 downloads were byte-for-byte the same files the site uses. The
other 2 are the Nomis occupation queries described above, downloaded again with
the corrected query: the files differ in bytes but every value used matches.

The full sample is in [`sample.json`](sample.json) (with every cell and
formula) and the raw results in [`results.json`](results.json) (with each
download's SHA-256 hash). To repeat the check: `make build`, then
`python3 scripts/accuracy_check.py sample` and run the "Accuracy check" workflow.

## Results

"Publisher's value" is the value worked out from the fresh download, before
rounding for the page.

| # | On the page | Page | Period | Publisher | Cell(s) | How | Publisher's value | Result |
|---|---|---|---|---|---|---|---|---|
| 1 | 9.5% | [life/2021.html](https://unpoliticalaf.vercel.app/life/2021.html) | January to December 2021 | ONS (via Nomis) | `aps210-uk-calendar-annual.csv line 620`; `aps210-uk-calendar-annual.csv line 602` | calculated | 9.487 | Match |
| 2 | 65.5% | [life/compare/spans/2009-2011-and-2012-2014.html](https://unpoliticalaf.vercel.app/life/compare/spans/2009-2011-and-2012-2014.html) | average of Apr–Jun 2009 to Apr–Jun 2011 | ONS | `LF25 row '2009 Q2'`; `LF25 row '2010 Q2'` (+1 more) | calculated | 65.533 | Match |
| 3 | 5.9% | [taxes.html](https://unpoliticalaf.vercel.app/taxes.html) | 2014-15 | OBR | `Receipts (£bn)!C22`; `Aggregates (£bn)!AE76` | calculated | 5.888 | Match |
| 4 | 35.2% | [taxes.html](https://unpoliticalaf.vercel.app/taxes.html) | 1957-58 | OBR | `Aggregates (per cent of GDP)!D14` | read | 35.19 | Match |
| 5 | 38.1% | [household-tax.html](https://unpoliticalaf.vercel.app/household-tax.html) | 1977 | ONS | `1977!G51`; `1977!G78` (+1 more) | calculated | 38.073 | Match |
| 6 | £44.2bn | [spending.html](https://unpoliticalaf.vercel.app/spending.html) | 2022-23 | HM Treasury | `4_2!U11` | read | 44.2 | Match |
| 7 | 26.7 | [life/compare/spans/2008-2010-and-2011-2013.html](https://unpoliticalaf.vercel.app/life/compare/spans/2008-2010-and-2011-2013.html) | average of January 2011 to January 2013 | Department for Education | `Table 6b!O11`; `Table 6b!Q11` (+1 more) | calculated | 26.733 | Match |
| 8 | £25.9bn | [spending-history.html](https://unpoliticalaf.vercel.app/spending-history.html) | 1974-75 | OBR | `Spending (£m)!M281`; `Aggregates (£bn)!AH36` | calculated | 25.863 | Match |
| 9 | £37.4bn | [spending.html](https://unpoliticalaf.vercel.app/spending.html) | 2006-07 | HM Treasury | `4_2!E12` | read | 37.4 | Match |
| 10 | 2.8% | [tax-history.html](https://unpoliticalaf.vercel.app/tax-history.html) | 1953-54 | OBR | `Receipts (£m)!W260`; `Receipts (£m)!Y260` | calculated | 2.839 | Match |
| 11 | £488 | [life/earnings.html](https://unpoliticalaf.vercel.app/life/earnings.html) | April 2009 | ONS (via Nomis) | `ashe-resident-uk-weekly-percentiles.csv line 454` | read | 488.5 | Match |
| 12 | 10.3% | [spending-history.html](https://unpoliticalaf.vercel.app/spending-history.html) | 1996-97 | OBR | `Spending (per cent of GDP)!I303` | read | 10.291 | Match |
| 13 | 2.8% | [spending-history.html](https://unpoliticalaf.vercel.app/spending-history.html) | 1955-56 | OBR | `Spending (per cent of GDP)!H262` | read | 2.805 | Match |
| 14 | 79.1% | [life/2005.html](https://unpoliticalaf.vercel.app/life/2005.html) | April to June 2005 | ONS | `MGSV row '2005 Q2'` | read | 79.1 | Match |
| 15 | £90.6bn | [spending.html](https://unpoliticalaf.vercel.app/spending.html) | 2019-20 | HM Treasury | `4_2!R22` | read | 90.6 | Match |
| 16 | 7.3% | [life/2019.html](https://unpoliticalaf.vercel.app/life/2019.html) | January to December 2019 | ONS (via Nomis) | `aps210-uk-calendar-annual.csv line 496`; `aps210-uk-calendar-annual.csv line 482` | calculated | 7.278 | Match |
| 17 | £17.8bn | [spending.html](https://unpoliticalaf.vercel.app/spending.html) | 2024-25 | HM Treasury | `4_3!W18` | read | 17.8 | Match |
| 18 | 65.7% | [life/2009.html](https://unpoliticalaf.vercel.app/life/2009.html) | April to June 2009 | ONS | `LF25 row '2009 Q2'` | read | 65.7 | Match |
| 19 | 17.3% | [life/1989.html](https://unpoliticalaf.vercel.app/life/1989.html) | June 1989 | ONS | `WFJ SA!E50`; `WFJ SA!X50` | calculated | 17.322 | Match |
| 20 | 42.9% | [spending-history.html](https://unpoliticalaf.vercel.app/spending-history.html) | 1980-81 | OBR | `Spending (per cent of GDP)!D287` | read | 42.876 | Match |
| 21 | 80.0% | [life/2005.html](https://unpoliticalaf.vercel.app/life/2005.html) | April to June 2005 | ONS | `YBUG row '2005 Q2'` | read | 80 | Match |
| 22 | 7.8% | [tax-history.html](https://unpoliticalaf.vercel.app/tax-history.html) | 2010-11 | OBR | `Receipts (per cent of GDP)!Y317`; `Receipts (per cent of GDP)!C317` (+5 more) | calculated | 7.831 | Match |
| 23 | 32.9 million | [life/compare/spans/2008-2010-and-2021-2023.html](https://unpoliticalaf.vercel.app/life/compare/spans/2008-2010-and-2021-2023.html) | average of Apr–Jun 2021 to Apr–Jun 2023 | ONS | `MGRZ row '2021 Q2'`; `MGRZ row '2022 Q2'` (+1 more) | calculated | 32,923.333 | Match |
| 24 | £674 | [life/earnings.html](https://unpoliticalaf.vercel.app/life/earnings.html) | April 2016 | ONS, ONS (via Nomis) | `ashe-resident-nations-regions-ft-median-weekly.csv line 578`; `L522 row '2025 APR'` (+1 more) | calculated | 673.991 | Match |
| 25 | £235 | [life/2010.html](https://unpoliticalaf.vercel.app/life/2010.html) | April 2010 | ONS, ONS (via Nomis) | `ashe-resident-uk-median-weekly.csv line 82`; `L522 row '2025 APR'` (+1 more) | calculated | 235.423 | Match |
| 26 | ±3.8% | [life/2010.html](https://unpoliticalaf.vercel.app/life/2010.html) | 2010 | ONS | `3.17!F33` | read | 3.823 | Match |
| 27 | 28.8% | [tax-history.html](https://unpoliticalaf.vercel.app/tax-history.html) | 1974-75 | OBR | `Receipts (£m)!C281`; `Receipts (£m)!Y281` | calculated | 28.833 | Match |
| 28 | 18.6% | [tax-history.html](https://unpoliticalaf.vercel.app/tax-history.html) | 2014-15 | OBR | `Receipts (£m)!Q321`; `Receipts (£m)!Y321` | calculated | 18.58 | Match |
| 29 | 6.10 | [life/house-prices.html](https://unpoliticalaf.vercel.app/life/house-prices.html) | 2008 (prices for the year ending September; earnings in April) | ONS | `1c!N9` | read | 6.1 | Match |
| 30 | £795 | [life/compare/spans/2008-2010-and-2020-2022.html](https://unpoliticalaf.vercel.app/life/compare/spans/2008-2010-and-2020-2022.html) | average of April 2020 to April 2022 | ONS, ONS (via Nomis) | `ashe-resident-uk-median-weekly.csv line 164`; `L522 row '2025 APR'` (+5 more) | calculated | 795.043 | Match |
| 31 | £2,760 | [who-pays-age.html](https://unpoliticalaf.vercel.app/who-pays-age.html) | 2023 to 2024 | HM Revenue and Customs | `Table_3_2!G46` | read | 2,760 | Match |
| 32 | ±£4 | [life/2016.html](https://unpoliticalaf.vercel.app/life/2016.html) | April 2016 | ONS, ONS (via Nomis) | `ashe-resident-uk-median-weekly.csv line 130`; `L522 row '2025 APR'` (+2 more) | calculated | 3.867 | Match |
| 33 | 15.1% | [life/2023.html](https://unpoliticalaf.vercel.app/life/2023.html) | January to December 2023 | ONS (via Nomis) | `aps218-uk-calendar-annual.csv line 128`; `aps218-uk-calendar-annual.csv line 122` | calculated | 15.062 | Match |
| 34 | 62.2% | [life/2017.html](https://unpoliticalaf.vercel.app/life/2017.html) | April to June 2017 | ONS | `YBUD row '2017 Q2'` | read | 62.2 | Match |
| 35 | ±12% | [life/2018.html](https://unpoliticalaf.vercel.app/life/2018.html) | 2018 | ONS | `3.17!AD19` | read | 12.042 | Match |
| 36 | 1.6% | [spending.html](https://unpoliticalaf.vercel.app/spending.html) | 2015-16 | HM Treasury | `4_4!N11` | read | 1.6 | Match |
| 37 | 87.7% | [who-pays.html](https://unpoliticalaf.vercel.app/who-pays.html) | 2019/20 | ONS | `Table 16!F47` | read | 87.7 | Match |
| 38 | £502.7bn | [spending-history.html](https://unpoliticalaf.vercel.app/spending-history.html) | 1974-75 | OBR | `Spending (£m)!D281`; `Aggregates (£bn)!AH36` | calculated | 502.688 | Match |
| 39 | 35.6% | [tax-history.html](https://unpoliticalaf.vercel.app/tax-history.html) | 1956-57 | OBR | `Receipts (per cent of GDP)!Y263` | read | 35.573 | Match |
| 40 | £727 | [life/2013.html](https://unpoliticalaf.vercel.app/life/2013.html) | April 2013 | ONS, ONS (via Nomis) | `ashe-resident-uk-median-weekly.csv line 108`; `L522 row '2025 APR'` (+1 more) | calculated | 727 | Match |
| 41 | 26.8% | [who-pays.html](https://unpoliticalaf.vercel.app/who-pays.html) | 2025 to 2026 | HM Revenue and Customs | `2_4_Taxpayer_share_tax!K29` | read | 26.8 | Match |
| 42 | £8,878 | [spending.html](https://unpoliticalaf.vercel.app/spending.html) | 2025-26 | HM Treasury, ONS | `4_2!X20`; `5!B21` | calculated | 8,878.392 | Match |
| 43 | 4.8% | [spending.html](https://unpoliticalaf.vercel.app/spending.html) | 2010-11 | HM Treasury | `4_4!I6` | read | 4.8 | Match |
| 44 | 1.0% | [spending.html](https://unpoliticalaf.vercel.app/spending.html) | 2009-10 | HM Treasury | `4_4!H19` | read | 1 | Match |
| 45 | £29.8bn | [spending.html](https://unpoliticalaf.vercel.app/spending.html) | 2004-05 | HM Treasury | `4_2!C10` | read | 29.8 | Match |
| 46 | 38.7% | [household-tax.html](https://unpoliticalaf.vercel.app/household-tax.html) | 1987 | ONS | `1987!E55`; `1987!E83` (+1 more) | calculated | 38.686 | Match |
| 47 | 9.6% | [who-pays.html](https://unpoliticalaf.vercel.app/who-pays.html) | 2022 to 2023 | HM Revenue and Customs | `2_4_Taxpayer_share_tax!F26` | read | 9.6 | Match |
| 48 | £52.3bn | [spending.html](https://unpoliticalaf.vercel.app/spending.html) | 2005-06 | HM Treasury | `4_3!D10` | read | 52.3 | Match |
| 49 | 33.6% | [household-tax.html](https://unpoliticalaf.vercel.app/household-tax.html) | 2010/11 | ONS | `2010-11!F56`; `2010-11!F86` (+1 more) | calculated | 33.602 | Match |
| 50 | 39.7% | [taxes.html](https://unpoliticalaf.vercel.app/taxes.html) | 2005-06 | OBR | `Aggregates (per cent of GDP)!D62` | read | 39.699 | Match |

## Limits

- This checks that the site reproduces the published tables. It does not check
  whether a table was the right one to use, or how a figure is described. Those
  are covered by the side-by-side reviews in `docs/benchmark-comparison.md`.
- Figures 41 to 50 are a separate draw from the headline pages, so the sample
  over-represents them on purpose. The first 40 are a plain random sample.
- The check was run by the same project that built the site. The method and
  files are public so that someone outside the project can repeat it.
