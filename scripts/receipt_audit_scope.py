"""Explicit receipt evidence scope, separate from the fixed spending audit.

These rectangles retain source headers, every data year, empty cells, notes and
number formats. They are evidence selections, not a fiscal series contract.
"""
from audit_scope import CATALOGUE_SHA256, SOURCE_MANIFEST_SHA256

SCOPE_ID = "obr-receipts-v1"
DIRECTORY = "data/audit/receipts"
SHEETS = {
    "obr_databank": {
        "Receipts (£bn)": ["B1:AH52"],
        "Aggregates (£bn)": ["B1:AH106"],
        "Aggregates (per cent of GDP)": ["B1:AG104"],
        "Glossary": ["B1:E24"],
    },
    "obr_hist": {
        "Receipts (£m)": ["A1:Z332"],
        "Receipts (per cent of GDP)": ["A1:Z332"],
        "Aggregates (£m)": ["A1:F331"],
        "Aggregates (per cent of GDP)": ["A1:F332"],
        "Contents": ["D4:D4", "A30:D74"],
    },
}


def filename(source, sheet):
    # Explicit ASCII names avoid conflating the £m and £bn series or units.
    titles = {
        "Receipts (£bn)": "receipts-gbp-bn",
        "Receipts (£m)": "receipts-gbp-m",
        "Receipts (per cent of GDP)": "receipts-pct-gdp",
        "Aggregates (£bn)": "aggregates-gbp-bn",
        "Aggregates (£m)": "aggregates-gbp-m",
        "Aggregates (per cent of GDP)": "aggregates-pct-gdp",
        "Glossary": "glossary",
        "Contents": "contents-notes",
    }
    return source + "--" + titles[sheet] + ".tsv"
