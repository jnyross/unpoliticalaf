"""Reproduce a bounded extraction of retained publications, never current coverage.

All execution belongs in credential-free Boat. Offsets refer to the ORIGINAL
26.01 retained extraction, not a newly normalised or silently replaced version.
Unknown publication days stay null. No independent review is asserted here.
"""
import re

from party_data import require, load_json
from party_source_audit import DEFAULT_INVENTORY, PREFIX, PinnedReader

OFFICIAL_DOMAINS = {"1": "allianceparty.org", "4": "conservatives.com", "7": "mydup.com",
                   "44": "greenparty.org.uk", "17": "libdems.org.uk", "22": "partyof.wales",
                   "1036": "reformparty.uk", "1117": "restorebritain.org.uk", "158": "tuv.org.uk"}


def pinned_source(key):
    reader = PinnedReader()
    info, content, _ = reader.source(key)
    documents = load_json(DEFAULT_INVENTORY.read_bytes())["documents"]
    document = next(d for d in documents if d["source_id"] == key)
    require(all(document[k] == v for k, v in info.items()), "inventory/source identity changed")
    require(document["published_on"] is None and document["publication_locator"] is None,
            "PDF publication day remains unverified; do not fabricate one")
    require(document["classification"] == ("dated_2026_publication" if key == "restore-economic-plan-pdf"
                                           else "historical_2024"), "publication classification changed")
    require(info["party_id"] is not None and document["classification"] in
            {"historical_2024", "dated_2026_publication"}, "not an eligible party publication")
    require(info["text_method"] == "retained_pdftotext_layout", "encoding/extraction not verified")
    require(key not in {"sdlp-2024", "uup-2024"}, "official landing provenance unresolved")
    extraction = reader.extractions[info["raw_path"][len(PREFIX):]]
    roster = load_json(reader.asset("commons-state-2026-10-30.json"))
    name = next(r["value"]["party"]["name"] for r in roster["items"]
                if str(r["value"]["party"]["id"]) == info["party_id"])
    return {"id": key, "kind": "party", "publisher": name, "party_id": info["party_id"],
            "url": info["url"], "published_on": document["published_on"],
            "publication_locator": document["publication_locator"],
            "retrieved_at": info["retrieved_at"], "snapshot_as_of": None,
            "path": PREFIX + extraction["output"], "sha256": info["text_sha256"],
            "raw_path": info["raw_path"], "raw_sha256": info["raw_sha256"]}, content


def missing(reason):
    return {"availability": "unavailable", "reason": reason, "items": []}


def ref(key, content, quote, start=0):
    offset = content.index(quote, start)
    return {"source_id": key, "start": offset, "end": offset + len(quote), "quote": quote}


def extend(data, manifest):
    parties = {p["id"]: p for p in data["parties"]}
    sources = {s["id"]: s for s in manifest["sources"]}
    texts = {}
    reader = PinnedReader()

    def source(key):
        if key not in sources:
            sources[key], texts[key] = pinned_source(key)
            manifest["sources"].append(sources[key])
            party = parties[sources[key]["party_id"]]
            party["publication_sources"].append(key)
            # CDN origins are permitted only by an exact immutable source binding.
            party["official_domain"] = OFFICIAL_DOMAINS[sources[key]["party_id"]]
        return texts[key]

    def add(key, slug, title, quote, *, costs=(), funding=(), year=None,
            basis="unspecified", baseline=None, geography="UK; individual services may have devolved remits.",
            amount_context=None):
        content = source(key)
        src = sources[key]
        evidence = ref(key, content, quote)
        page = content[:evidence["start"]].count("\f") + 1
        historical = key != "restore-economic-plan-pdf"
        scope = ("Historical 2024; current adoption unverified. " if historical else
                 "2026 philosophy paper; implementation/current coverage unverified. ")
        scope += f"Physical PDF page {page}; do not aggregate overlapping records."
        proposal_id = key + "-" + slug

        def amounts(values, label):
            if not values:
                return missing("No separate scalar " + label + " verified; quoted ranges/targets retained.")
            items = []
            for amount, unit, snippet in values:
                context_ref = ref(key, content, amount_context) if amount_context else evidence
                item_ref = ref(key, content, snippet, context_ref["start"])
                require(item_ref["end"] <= context_ref["end"], "amount must be inside declared context")
                items.append({"amount": amount, "unit": unit, "basis": basis, "evidence": item_ref})
            return {"availability": "available", "reason": None, "items": items}

        proposal = {"id": proposal_id, "title": title, "proposal_date": src["published_on"],
                    "fiscal_year": year, "fiscal_year_reason": None if year else
                    "No single fiscal year verified; retain the stated period in baseline and quotation.",
                    "baseline": baseline or "No quantified fiscal baseline or price basis verified in this passage.",
                    "scope": scope, "geography": geography, "status": "proposed", "evidence": evidence,
                    "costs_claimed": amounts(costs, "cost"), "funding_claimed": amounts(funding, "funding"),
                    "assessments": missing("No permitted independent assessment verified for this claim."),
                    "overlap_key": proposal_id, "overlaps_with": []}
        party = parties[src["party_id"]]
        party.update(coverage="recorded", unavailable_reason=None)
        party["proposals"].append(proposal)

    # Complete numbered fiscal rows 1–23, their explanatory notes, published totals
    # and the complete public-investment allocation. Not the unreadable plain text.
    key = "libdem-2024-costings"
    content = source(key)
    pages = content.split("\f")
    notes = {}
    for page_number in (4, 5, 7):
        page = pages[page_number - 1]
        starts = list(re.finditer(r"(?m)^\d+\. ", page))
        for i, match in enumerate(starts):
            note = page[match.start():starts[i + 1].start() if i + 1 < len(starts) else len(page)].strip()
            notes[int(note.split(".", 1)[0])] = note
    require(set(notes) == set(range(1, 24)), "all numbered fiscal notes required")
    labels = ["NHS and social care", "Unpaid carers", "Early years and childcare", "Schools",
              "Higher education and lifelong learning", "Welfare changes", "Farming and environment",
              "Transport", "International, defence and borders", "Other current spending", "Devolved allocations",
              "Asylum processing and employment", "Consultancy spending", "Bank taxes", "Capital gains tax",
              "Oil and gas windfall tax", "Digital services tax", "Share buyback tax", "Water company profit tax",
              "Tobacco company levy", "Private jet flight tax", "Aviation taxes", "Tax compliance"]
    for page_number, first, last, field in ((3, 1, 13, "costs"), (6, 14, 23, "funding")):
        table = pages[page_number - 1]
        for number in range(first, last + 1):
            matches = [block.strip() for block in table.split("\n\n")
                       if re.search(r"(?m)^\s*" + str(number) + r"\s+\S", block)]
            require(len(matches) == 1, "missing/ambiguous numbered Liberal Democrat fiscal row")
            quote = matches[0]
            numbers = re.findall(r"-?\d[\d,]*", quote)
            amount = numbers[-1].replace(",", "")
            # Use the source's numbered item as the neutral title; policy wording
            # remains a verbatim attributed quote, including evaluative language.
            add(key, "row-" + str(number), labels[number - 1] + " (2024)", notes[number],
                **{field: [(amount, "GBP million", quote)]}, year="2028-29", basis="annual",
                amount_context=quote,
                baseline="Additional current spending/revenue, £m 2028-29. Evidence pairs each numbered row with its complete policy note. Negative spending is claimed savings.")
    for label, page_number, total, field in (("Current spending", 3, "26800", "costs"),
                                            ("Revenue", 6, "26870", "funding")):
        page = pages[page_number - 1]
        quote = re.search(r"Total\s+[\d,]+", page).group()
        # Different page totals are explicitly located by their preceding heading.
        pos = sum(len(p) + 1 for p in pages[:page_number - 1]) + page.index(quote)
        evidence_quote = content[pos:pos + len(quote)]
        add(key, label.lower().replace(" ", "-") + "-total", label + " total (2024)", evidence_quote,
            **{field: [(total, "GBP million", quote)]}, year="2028-29", basis="annual",
            baseline="Published net table total; overlaps component records, do not add it to those rows.")
    capital = content[content.index("PUBLIC INVESTMENT\n"):].rstrip("\f\n")
    add(key, "capital", "Public investment allocation (2024)", capital,
        costs=[("19.7", "GBP billion", "additional £19.7 billion a year on average"),
               ("1.1", "GBP billion", "£1.1 billion of investment in hospitals"),
               ("1.9", "GBP billion", "£1.9 billion to build new schools"),
               ("8.4", "GBP billion", "£8.4 billion to tackle climate change"),
               ("1.2", "GBP billion", "£1.2 billion of investment in better transport"),
               ("6.2", "GBP billion", "£6.2 billion to support our target"),
               ("1.9", "GBP billion", "additional £1.9 billion would be made available")],
        funding=[("0.9", "GBP billion", "£0.9\n   billion of which will be funded by redirecting capital funding")], basis="annual",
        baseline="Average annual additional investment over the next Parliament. £0.9bn schools reallocation is included in the £1.9bn schools line. Devolved allocations must not be added twice.")

    # Entire historical funding and cost tables, with EACH line separately named
    # in evidence; all figures are the party's annualised five-year assumptions.
    key = "reform-2024-pdf"
    content = source(key)
    for heading, end, slug, field in (
        ("SAVINGS PLEDGES\n", "  EXTRA GROWTH ASSUMPTION", "savings", "funding"),
        ("  EXTRA GROWTH ASSUMPTION\n", "REFORM UK 2024", "growth", "funding"),
        ("  COST PLEDGES\n", "REFORM UK 2024", "costs", "costs")):
        start = content.index(heading)
        quote = content[start:content.index(end, start + len(heading))].strip()
        total = {"savings": "150", "growth": "10", "costs": "141"}[slug]
        token = {"savings": "£150 billion pa", "growth": "£10 billion pa of extra tax revenues", "costs": "£141 BILLION"}[slug]
        items = [(total, "GBP billion", token)]
        if slug in {"savings", "costs"}:
            # Every table row has one terminal £ amount. Exclude the prose
            # 'Save £5 in 100' rate and the already separately recorded total.
            for match in re.finditer(r"(?m)^\s*([^\n]*?)\s+£(\d+)\s*$", quote):
                row = match.group().strip()
                if "TOTAL" not in row.upper():
                    items.append((match.group(2), "GBP billion", row))
        add(key, slug, {"savings": "Annualised savings table (2024)", "growth": "Additional growth revenue assumption (2024)",
                       "costs": "Annualised cost table (2024)"}[slug], quote,
            **{field: items}, basis="annual",
            baseline="Annualised over five-year electoral term; no single fiscal year. Items include total AND components: never sum together. Growth is assumed revenue, not outturn. Party estimates, no endorsement.")

    # Restore's full executive-summary spending and tax package. Later detailed
    # chapters differ on some amounts; those differences are retained below.
    key = "restore-economic-plan-pdf"
    content = source(key)
    spans = [
        ("Fiscal Framework\n", "Our key spending measures", "framework", "Spending framework and savings target (2026)", [], [("178", "GBP billion", "around £178 billion")]),
        ("   ●\u200b Welfare:", "   ●\u200b QUANGOs:", "welfare", "Pension and working-age benefit changes (2026)", [], []),
        ("   ●\u200b QUANGOs:", "   ●\u200b Healthcare:", "quangos", "Public body budget freeze (2026)", [], []),
        ("   ●\u200b Healthcare:", "   ●\u200b Education:", "health", "Health charging and tax deductions (2026)", [], [("20", "GBP billion", "net annual\n      benefit of £20 billion")]),
        ("   ●\u200b Education:", "   ●\u200b Energy:", "education", "School funding and tax deductions (2026)", [], [("10", "GBP billion", "annual contribution of £10\n      billion")]),
        ("   ●\u200b Energy:", "   ●\u200b Budget Freeze:", "energy", "End net-zero public expenditure (2026)", [], []),
        ("   ●\u200b Budget Freeze:", "Tax Proposals\n", "freeze", "Departmental budget freeze (2026)", [], []),
        ("Tax Proposals\n", "   ●\u200b Income tax:", "tax-total", "Conditional tax reduction envelope (2026)", [("155", "GBP billion", "approximately £155 billion per annum")], []),
        ("   ●\u200b Income tax:", "   ●\u200b Corporation tax:", "income-tax", "Income tax changes: summary estimate (2026)", [("49", "GBP billion", "estimated cost £49 billion")], []),
        ("   ●\u200b Corporation tax:", "   ●\u200b Abolish small taxes:", "corporation-tax", "Corporation tax changes: summary estimate (2026)", [("41", "GBP billion", "estimated cost £41 billion")], []),
        ("   ●\u200b Abolish small taxes:", "   ●\u200b Capital gains tax:", "small-taxes", "Abolish named taxes: summary estimates (2026)", [], []),
        ("   ●\u200b Capital gains tax:", "   ●\u200b VAT:", "cgt", "Capital gains allowance: summary proposal (2026)", [("0.7", "GBP billion", "estimated cost £0.7 billion")], []),
        ("   ●\u200b VAT:", "While we do not assume", "vat", "VAT rate and threshold: summary estimate (2026)", [], []),
    ]
    for begin, end, slug, title, costs, funding in spans:
        start = content.index(begin)
        quote = content[start:content.index(end, start + len(begin))].strip()
        add(key, slug, title, quote, costs=costs, funding=funding,
            baseline="First Parliament, with no fixed fiscal year established. Rates/ranges and approximate figures are party claims. Detailed chapter differences remain unresolved; no summation or reconciliation asserted.")
    # No range is flattened to a midpoint or presented as an exact amount.
    # A range remains fully visible in the quotation even when no scalar exists.

    for begin, end, slug, title, amount, unit, token in [
        ("We propose to make work pay.\n", "Corporation Tax:", "income-detail", "Income tax changes: detailed estimate (2026)", "49.2", "GBP billion", "49.2"),
        ("We propose a major overhaul.", "Overall, we will be friendly", "corporation-detail", "Corporation tax changes: initial stage (2026)", "24", "GBP billion", "£24 billion"),
        ("Capital Gains Tax (CGT) – Increase the allowance", "       Figure 29:", "cgt-detail", "Capital gains allowance: detailed proposal (2026)", "700", "GBP million", "£700 million per\nannum"),
    ]:
        start = content.index(begin)
        quote = content[start:content.index(end, start)].strip()
        add(key, slug, title, quote, costs=[(amount, unit, token)],
            basis="annual" if slug == "cgt-detail" else "unspecified",
            baseline="Detailed chapter; differs from executive-summary scope or rounding. Income tax: summary £49bn, table £49.2bn, prose around £50bn. Corporation: initial £24bn at 19%, later cuts £4bn/point; summary £41bn. CGT: summary £20k–£40k allowance; detail £20k. Unresolved, not reconciled.")

    # Complete statistical appendix rows, all five source columns retained in
    # every row quote. Scalar fields explicitly refer ONLY to the final column.
    key = "green-2024"
    content = source(key)
    appendix = content[content.index("Statistical Appendix\n"):]
    column = next(line.index("Health and social care") for line in appendix.splitlines()
                  if "Health and social care" in line)
    baseline = ("OBR March 2024 baseline. Five columns: years ended March 2026–2030. Scalar ONLY for 2030 (2029-30); all years quoted. "
                "Ten-year programme; inflation/supply constraints; party estimates.")
    sections = [("Revenue spending\n", "Capital spending\n", "revenue", "costs"),
                ("Capital spending\n", "Taxation\n", "capital", "costs"),
                ("Taxation\n", "Deficit - funded", "tax", "funding"),
                ("Deficit - funded", "Notes\n", "borrowing", "funding")]
    for begin, end, slug, field in sections:
        start = appendix.index(begin)
        section = appendix[start:appendix.index(end, start + len(begin))]
        rows = [(line if line.startswith("Deficit - funded") else line[column:]).strip()
                for line in section.splitlines()
                if re.search(r"(?:-?\d+\.\d+\s+){4}-?\d+\.\d+\s*$", line)]
        require(rows, "missing Green appendix rows")
        for number, quote in enumerate(rows, 1):
            values = re.findall(r"-?\d+\.\d+", quote)
            title = re.sub(r"(?:-?\d+\.\d+\s*){5}$", "", quote).strip() or "Published subtotal"
            title = title.replace("Deficit - funded by additional debt", "Additional debt")
            add(key, slug + "-" + str(number), f"{slug.capitalize()}: {title} (2024)", quote,
                **{field: [(values[-1], "GBP billion", quote)]}, year="2029-30", basis="annual", baseline=baseline)
    notes = appendix[appendix.index("Notes\n"):appendix.index("Building A Fairer,")].strip()
    add(key, "appendix-notes", "Statistical appendix definitions and constraints (2024)", notes, baseline=baseline)

    # Whole bounded fiscal sections from other retained official manifestos.
    # Multi-column layout is preserved verbatim, never silently reordered.
    # Chunking is only at line boundaries and does not imply a policy is costed.
    sections = [
        ("alliance-2024", [(16, "We believe that UK Fiscal Rules should", "Significant climate and environmental"),
                           (17, "We would also like to see a tax on share", "Pensions"),
                           (19, "Alliance is committed to securing a base-lined", "Maximising Shared Island Funding")],
         "Fiscal rules, share buybacks and funding", "UK and Northern Ireland"),
        ("conservative-2024", [(16, "Our long-term ambition, when it is afordable", "This comes on top"),
                               (17, "1.   Continuing to uprate", "The Conservative and Unionist")],
         "National Insurance and pension uprating", "UK; devolved remits differ"),
        ("dup-2024", [(18, "In the next Parliament, DUP MPs will", "Building a Better Health Service")],
         "Needs-based funding framework", "Northern Ireland"),
        ("plaid-2024-pdf", [(8, "A Fair Funding Formula", "A Fairer Tax System")],
         "Needs-based replacement for Barnett", "Wales"),
        ("tuv-2024", [(15, "THE ECONOMY – PERSONAL", "                                     PAGE"),
                      (16, "• Abolish IR35", "                                       PAGE")],
         "Personal and business taxation", "UK, including Northern Ireland"),
    ]
    for key, extracts, title, geography in sections:
        content = source(key)
        pages = content.split("\f")
        for page_number, begin, end in extracts:
            page = pages[page_number - 1]
            start = page.index(begin)
            page = page[start:page.index(end, start + len(begin))].strip()
            parts = []
            while len(page) > 3500:
                split = page.rfind("\n", 0, 3500)
                parts.append(page[:split].strip())
                page = page[split:].strip()
            if page:
                parts.append(page)
            for index, quote in enumerate(parts, 1):
                add(key, f"fiscal-p{page_number}-{index}", f"{title}: extract {page_number}.{index} (2024)",
                    quote, geography=geography,
                    baseline="Historical fiscal extract; cost/funding not verified. Original columns retained. TUV quotes Reform 2024, not its 2026 plan.")

    for party in data["parties"]:
        party["proposals"].sort(key=lambda p: (p["title"].casefold(), p["id"]))
    # Explicit related groups; totals are also labelled as non-additive in scope.
    for party in data["parties"]:
        groups = {}
        for proposal in party["proposals"]:
            key = proposal["evidence"]["source_id"]
            if key == "libdem-2024-costings":
                match = re.search(r"Costing item (\d+)", proposal["title"])
                group = key + "-item-" + match.group(1) if match else proposal["id"]
                groups.setdefault(group, []).append(proposal)
            elif key == "restore-economic-plan-pdf":
                slug = proposal["id"][len(key) + 1:]
                group = {"income-detail": "income-tax", "corporation-detail": "corporation-tax", "cgt-detail": "cgt"}.get(slug, slug)
                groups.setdefault(key + "-" + group, []).append(proposal)
            elif key == "reform-2024-pdf":
                groups.setdefault(key, []).append(proposal)
        for key, proposals in groups.items():
            for proposal in proposals:
                proposal["overlap_key"] = key
                proposal["overlaps_with"] = sorted(p["id"] for p in proposals if p is not proposal)
