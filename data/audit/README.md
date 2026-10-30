# Pinned spending audit extracts

These are private review inputs, outside the public output allowlist. No raw
workbook or protected source file is changed. `pinned-source.json` is a byte-for-byte
copy of `reference/un-political/SOURCE.json`, SHA-256
`871a749fa925f4a4135ff09c2667019ae3101fddafc11c23456fb60ade0b0522`.
It lets bounded roles read the original file identities without protected-path access.

`index.json` binds each extract to its retained source ID, workbook path/hash,
publication, publication/retrieval dates, worksheet, exact selected ranges,
cell count, number formats and TSV hash. The unchanged `data/sources.json` owns
source URLs and publication metadata. An extraction is evidence of the retained
workbook, not independent confirmation of a publication date or fiscal meaning.

Each TSV line contains one original cell address, kind, JSON-encoded raw value,
number-format ID (into that sheet's index entry), and JSON-encoded formula.
Numeric values retain the original XML numeric text without rounding or scaling;
text resolves shared/inline strings. JSON `null`, numeric `"0"` and text `"-"`
remain distinct. Absent cells are explicit blanks. Excel number formats are
evidence about display precision, not proof of the statistical error of a series.
TSV follows normal CSV quoting: doubled quotes escape quotes inside a field;
JSON escapes preserve line breaks and tabs without splitting a source cell.
No fiscal transformation is needed to inspect these files in a text editor.

The fixed scope in `scripts/audit_scope.py` covers the existing spending product's
cells and reconciliation operands: PESA 4.1–4.4 and 5.2; OBR's public-finances
series; the historical spending sheet and its contents/notes/source bibliography.
It excludes unrelated receipt and aggregate worksheets, workbook graphics, empty
formatting tails and operational material. A test checks that every generated
`v`/`ref` pair has a readable extract cell. This is not evidence for future receipts
or other new product series; extend the fixed scope when those are implemented.

In a credential-free check environment:

```sh
.venv/bin/python scripts/extract_audit.py
.venv/bin/python scripts/check_audit.py
make build
make verify
```

The exporter reads ZIP/XML directly and refuses changed source hashes. The
checker separately reopens the original workbooks with openpyxl and checks every
selected cell, including labels, unit cells, literal dashes, formula caches and
stored number formats. It never saves a workbook. Regeneration must leave
the extracts byte-identical. All raw and source-manifest hashes remain pinned.

Important reading points (use the matching sheet's TSV and format IDs):

| Source | Exact cells | Evidence / open interpretation |
| --- | --- | --- |
| PESA chapter 4 | `4_1!B3` | Outturn through 2025-26. |
| PESA chapter 4 | `4_1!B51:B52` | 2025-26 prices, ONS 30 June 2026, OBR 3 March 2026, GDP forecasts from 2026-27. |
| PESA chapter 4 | `4_2!B4`, `4_3!B4`, `4_4!B4` | Outturn labels for the functional tables. |
| PESA chapter 4 | `4_2!X3`, `4_3!X3`, `4_4!X3` | Cash/real £ billion and GDP percentage unit labels; compare titles too. |
| PESA chapter 5 | `5_2!G3`, `C5:G6`, `G11`, `B137:B138` | £ million, year/outturn headers, a literal dash, debt definitions. Do not infer that dash means numeric zero. |
| OBR databank | `Public finances since 1900!B2:B3`, `B139:B148` | Conflicting forecast-vintage prose retained verbatim; B143 describes the numerator's 22 September 2026 update through 2025-26. |
| OBR history | `Contents!D31`, `D45:D59`, `D64`, `D67:D74` | Financial-year basis, joined sources, extrapolation, residuals, geography, bibliography. |
| OBR history | `Spending (per cent of GDP)!B4:N6` | Official labels, ONS codes, residual formulas; data dashes remain literal. |

The retained PESA tables do not provide an explicit prose definition for every
literal dash in this scope. Some Excel formats also render numeric zero as a
dash; those are distinct from literal text dashes in the raw cells. The seed
does not turn either missing values or text dashes into zero. Any stronger
table-specific interpretation must cite retained evidence and be reviewed.
