"""NATO's own UK defence figures: core defence expenditure as a share of real GDP (NATO table 3).

NATO's report is a PDF with no text layer, so its UK figures are kept as a transcription in
data/transcribed/nato-uk-core-defence-share.json, with the PDF's hash recorded in the source
registry. The transcription is checked against the PDF page by eye and by OCR when it is made.
NATO's definition is wider than the government's PESA defence figure: it counts military pensions.
"""
import json

from .data import Fact
from .readers import ROOT

SOURCE = "nato-uk-table3"
FILE = "data/transcribed/nato-uk-core-defence-share.json"


def build(facts):
    data = json.loads((ROOT / FILE).read_text())
    for year, value in data["values"].items():
        note = "NATO core defence, United Kingdom" + (" (NATO estimate)" if year in data["estimates"] else "")
        facts.add(Fact(f"nato.uk.core.{year}", float(value), "% of real GDP", year, SOURCE, f"year {year}", "published", note=note))
    return data["values"]
