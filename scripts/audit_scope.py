"""Fixed, spending-only recovery evidence scope; no fiscal interpretation here."""
SOURCE_MANIFEST_SHA256 = "871a749fa925f4a4135ff09c2667019ae3101fddafc11c23456fb60ade0b0522"
CATALOGUE_SHA256 = "5e7ebb343bee091960052b1727bf7bff6997216e8a5bf7805d18770aa7d5914a"

# Include headers, all operands read by the existing spending reconciliations,
# explicit blanks/dashes, source notes and style/precision information. These are
# selected worksheets, not a dump of the four workbooks (e.g. receipts excluded).
SHEETS = {
    "pesa_ch4": {
        "4_1": ["B1:O53"],
        "4_2": ["A1:X35"],
        "4_3": ["A1:X36"],
        "4_4": ["A1:X36"],
    },
    "pesa_ch5": {"5_2": ["B1:G147"]},
    "obr_databank": {"Public finances since 1900": ["B1:F148"]},
    "obr_hist": {
        "Contents": ["D4:D4", "A30:D74"],
        "Spending (per cent of GDP)": ["A1:N329"],
    },
}


def filename(source, sheet):
    return source + "--" + sheet.replace(" ", "_").replace("(", "").replace(")", "") + ".tsv"
