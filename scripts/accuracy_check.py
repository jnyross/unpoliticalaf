#!/usr/bin/env python3
"""Random-sample accuracy check: trace figures on the pages back to the
publishers' own files, downloaded fresh from the publishers' websites.

Two steps:

  sample  (after `make build`, no network needed)
      Picks figures at random from the built pages, with a fixed seed, and
      writes docs/accuracy-check/sample.json: for each figure, the page, the
      text a reader sees, the value behind it, and every source cell it comes
      from (following calculations down to published cells).

  check   (needs network access to the publishers; the GitHub workflow runs it)
      Downloads every source file in the sample again from the publisher's URL
      (not the copy kept in this repository), reads each cell with readers
      written here (not the site builder's), redoes each calculation, and
      compares the result with the text on the page. Writes
      docs/accuracy-check/results.json.

Both steps take --dir FOLDER to use another folder than docs/accuracy-check,
and sample takes --ids FILE (figure ids, one per line) to check chosen figures
instead of a random draw. The rubric v3 fact-checker uses these
(docs/standins/README.md).

This file deliberately imports nothing from builder/, so a mistake in the
builder cannot hide itself.
"""
import csv
import hashlib
import io
import json
import random
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
OUT = ROOT / "docs" / "accuracy-check"
SEED = 20261102  # the date the sample was drawn; changing it draws a new sample
N_RANDOM = 40    # figures drawn from every figure shown on the site
N_HEADLINE = 10  # extra figures drawn from the headline pages
HEADLINE_PAGES = ["index.html", "spending.html", "taxes.html", "who-pays.html", "household-tax.html"]
UA = {"User-Agent": "Mozilla/5.0 (Unpolitical accuracy check; +https://github.com/jnyross/unpoliticalaf)"}

DATA_RE = re.compile(r'<data value="([^"]*)" data-fact="([^"]+)" data-kind="([^"]+)">([^<]*)</data>')


# --------------------------------------------------------------------- sample

def shown_figures():
    """Every figure a reader can see: (page, fact id, kind, text)."""
    seen = {}
    for path in sorted(SITE.rglob("*.html")):
        rel = path.relative_to(SITE).as_posix()
        if rel.startswith("figures/"):
            continue  # the trace records repeat figures; sample what readers read
        for _value, fid, kind, text in DATA_RE.findall(path.read_text(encoding="utf-8")):
            seen.setdefault(fid, []).append((rel, kind, text))
    return seen


def leaves(facts, fid, out=None):
    """The published cells a figure comes from, following calculations down."""
    out = [] if out is None else out
    f = facts[fid]
    if f["formula"] and f["inputs"]:
        for i in f["inputs"]:
            leaves(facts, i, out)
    elif f["id"] not in [x["id"] for x in out]:
        out.append({k: f[k] for k in ("id", "value", "unit", "period", "source", "locator", "scale", "status")})
    return out


def sample(ids=None, out=None):
    """ids: figure ids chosen by hand (the v3 fact-checker's headline claims)
    instead of the random draw. out: folder for sample.json, default OUT."""
    out = out or OUT
    data = json.loads((SITE / "data/facts.json").read_text())
    facts = {f["id"]: f for f in data["facts"]}
    sources = data["sources"]
    receipts = json.loads((ROOT / "data/fetched/receipts.json").read_text())
    shown = shown_figures()
    population = sorted(fid for fid in shown if fid in facts and facts[fid]["status"] != "missing")
    rng = random.Random(SEED)
    headline = []
    if ids:
        unknown = [i for i in ids if i not in population]
        if unknown:
            sys.exit(f"not figures shown on the site: {', '.join(unknown)}")
        picked, picked_h = list(dict.fromkeys(ids)), []
    else:
        picked = rng.sample(population, N_RANDOM)
        headline = sorted({fid for fid, uses in shown.items() if fid in population and fid not in picked
                           and any(p in HEADLINE_PAGES for p, _, _ in uses)})
        picked_h = rng.sample(headline, N_HEADLINE)
    items = []
    for n, fid in enumerate(picked + picked_h, 1):
        f = facts[fid]
        uses = shown[fid]
        page, kind, text = next(((p, k, t) for p, k, t in uses if p in HEADLINE_PAGES), uses[0])
        cells = leaves(facts, fid)
        calc, todo = {}, [fid]
        while todo:  # every calculation between the figure and its cells
            g = facts[todo.pop()]
            if g["formula"] and g["inputs"] and g["id"] not in calc:
                calc[g["id"]] = {"formula": g["formula"], "inputs": g["inputs"], "value": g["value"]}
                todo.extend(g["inputs"])
        for c in cells:
            s = sources[c["source"]]
            rec = next((r for r in receipts.values() if "data/fetched/" + r["file"] == s["file"]), None)
            c["url"] = rec["url"] if rec else s["url"]
            c["file"] = s["file"]
            c["sha256"] = s.get("sha256") or (rec or {}).get("sha256")
            c["publisher"] = s["publisher"]
            c["title"] = s["title"]
        items.append({"n": n, "group": "chosen" if ids else ("random" if n <= N_RANDOM else "headline"), "id": fid, "page": page,
                      "pages": len(uses), "kind": kind, "text": text, "value": f["value"], "unit": f["unit"],
                      "period": f["period"], "status": f["status"], "formula": f["formula"], "calc": calc, "cells": cells})
    out.mkdir(parents=True, exist_ok=True)
    meta = {"seed": None if ids else SEED, "population": len(population), "headline_population": len(headline),
            "commit": json.loads((SITE / "build.json").read_text()).get("commit") if (SITE / "build.json").exists() else None}
    (out / "sample.json").write_text(json.dumps({"meta": meta, "items": items}, indent=1, ensure_ascii=False) + "\n")
    print(f"chose {len(items)} of {len(population)} figures shown" if ids else
          f"sampled {len(items)} of {len(population)} figures shown ({len(headline)} on headline pages)")


# ---------------------------------------------------------------- page check

MULT = {"millions": 1 / 1000, "millions_people": 1 / 1000, "millions_raw": 1 / 1_000_000}


def page_matches(item):
    """Does the text on the page round correctly from the figure's value?"""
    text = item["text"].replace(",", "").replace("−", "-")
    m = re.search(r"[-+]?\d+(?:\.(\d+))?", text)
    if not m or item["value"] is None:
        return False, "no number in the text"
    shown = float(m.group(0))
    places = len(m.group(1) or "")
    v = item["value"] * MULT.get(item["kind"], 1)
    ok = abs(abs(v) - abs(shown)) <= 0.5 * 10 ** -places + 1e-9
    return ok, f"{v:.6g} shown as {item['text']!r}"


# --------------------------------------------------------------------- check

def get(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(5 * 2 ** attempt)


def col_index(letters):
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def split_ref(locator):
    sheet, ref = locator.rsplit("!", 1)
    m = re.fullmatch(r"\$?([A-Z]+)\$?(\d+)", ref)
    return sheet.strip("'"), int(m.group(2)) - 1, col_index(m.group(1))


def ods_rows(body, sheet):
    """Rows of one sheet of an OpenDocument spreadsheet, repeats expanded."""
    ns = {"table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
          "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
          "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0"}
    T, O = "{%s}" % ns["table"], "{%s}" % ns["office"]
    root = ElementTree.fromstring(zipfile.ZipFile(io.BytesIO(body)).read("content.xml"))
    for t in root.iter(T + "table"):
        if t.get(T + "name") != sheet:
            continue
        rows = []
        for r in t.iter(T + "table-row"):
            cells = []
            for c in r:
                if c.tag not in (T + "table-cell", T + "covered-table-cell"):
                    continue
                v = c.get(O + "value")
                if v is None:
                    v = "\n".join("".join(p.itertext()) for p in c.findall("text:p", ns)) or None
                cells.extend([v] * min(int(c.get(T + "number-columns-repeated", "1")), 1000))
            rows.extend([cells] * min(int(r.get(T + "number-rows-repeated", "1")), 1000))
        return rows
    raise KeyError(sheet)


def read_cell(body, file, locator, retained=None):
    """Read one value from a freshly downloaded file. `retained` is the copy in
    the repository, used only to find which row a 'line N' locator means, so
    that a newer edition with extra rows is still read at the right row."""
    ext = file.rsplit(".", 1)[-1]
    if ext == "xlsx":
        import openpyxl
        sheet, r, c = split_ref(locator)
        ws = openpyxl.load_workbook(io.BytesIO(body), data_only=True, read_only=True)[sheet]
        for row in ws.iter_rows(min_row=r + 1, max_row=r + 1, min_col=c + 1, max_col=c + 1, values_only=True):
            return row[0]
        return None
    if ext == "xls":
        import xlrd
        sheet, r, c = split_ref(locator)
        return xlrd.open_workbook(file_contents=body).sheet_by_name(sheet).cell_value(r, c)
    if ext == "ods":
        sheet, r, c = split_ref(locator)
        rows = ods_rows(body, sheet)
        return rows[r][c] if r < len(rows) and c < len(rows[r]) else None
    if ext == "csv":
        rows = list(csv.reader(io.StringIO(body.decode("utf-8-sig"))))
        m = re.search(r" line (\d+)$", locator)
        if m:
            head = rows[0]
            vcol = head.index("OBS_VALUE" if "OBS_VALUE" in head else "Data values")
            old = list(csv.reader(io.StringIO(retained.decode("utf-8-sig")))) if retained else rows
            want = old[int(m.group(1)) - 1]
            ohead = old[0]
            keys = [h for h in ohead if h not in ("OBS_VALUE", "Data values", "OBS_STATUS", "OBS_STATUS_NAME", "RECORD_OFFSET", "RECORD_COUNT")]
            label = {h: want[ohead.index(h)] for h in keys if h in head}
            hits = [r for r in rows[1:] if all(r[head.index(h)] == v for h, v in label.items())]
            if len(hits) != 1:
                raise ValueError(f"{len(hits)} rows match {label}")
            return hits[0][vcol]
        m = re.fullmatch(r"CDID (\w+) row '(.+)'", locator)
        if m:
            col = next(r for r in rows if r and r[0] == "CDID").index(m.group(1))
            return next((r[col] for r in rows if r and r[0] == m.group(2)), None)
        m = re.fullmatch(r"\w+ row '(.+)'", locator)
        if m:
            return next((r[1] for r in rows if r and r[0] == m.group(1)), None)
    if ext == "json":
        data = json.loads(body)
        m = re.fullmatch(r"value\[(\d+)\]", locator)
        if m:
            return data["value"].get(m.group(1))
        m = re.fullmatch(r"results\[(\d+)\] values\.(\w+)", locator)
        if m:
            return data["results"][int(m.group(1))]["values"][m.group(2)]
    if ext == "pdf":
        from pypdf import PdfReader
        m = re.fullmatch(r"p(\d+) after '(.+)' line '(.+)' number (\d+)", locator)
        text = PdfReader(io.BytesIO(body)).pages[int(m.group(1)) - 1].extract_text()
        after = text[text.index(m.group(2)) + len(m.group(2)):]
        line = after[after.index(m.group(3)) + len(m.group(3)):].split("\n", 1)[0]
        return re.findall(r"-?[\d,]+(?:\.\d+)?", line)[int(m.group(4)) - 1].replace(",", "")
    raise ValueError(f"no reader for {file} at {locator}")


def as_float(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "").lstrip("±").strip()
    try:
        return float(s)
    except ValueError:
        return None


def evaluate(formula, values, inputs=()):
    """Redo a calculation written as text, e.g. '100 × a ÷ b'."""
    expr = formula
    # Some formulas end with their period, e.g. '100 × a ÷ b, 2025-26', and name
    # their inputs without it, so 'a' stands for the input 'a.2025-26'.
    label = re.search(r",\s*(\d{4}-\d{2})$", expr)
    if label:
        period = label.group(1)
        expr = expr[:label.start()]
        values = {**values, **{fid[:-len(period) - 1]: v for fid, v in values.items()
                               if fid.endswith("." + period)}}
    m = re.fullmatch(r"(\S+) − sum of the (?:\w+ )?named \w+", formula)
    if m:  # 'total − sum of the named groups': the first input less all the others
        expr = " − ".join([m.group(1)] + [i for i in inputs if i != m.group(1)])
    for fid in sorted(values, key=len, reverse=True):
        expr = expr.replace(fid, f"({values[fid]!r})")
    expr = expr.replace("×", "*").replace("÷", "/").replace("−", "-")
    if not re.fullmatch(r"[\d\s.()+\-*/e]+", expr):
        raise ValueError(f"cannot evaluate {expr!r}")
    return eval(expr, {"__builtins__": {}})  # only digits and arithmetic remain


def check(local=False, out=None):
    """local=True reads the repository's copies instead of downloading: a dry
    run of the readers, not the check itself."""
    out = out or OUT
    plan = json.loads((out / "sample.json").read_text())
    downloads = {}
    for item in plan["items"]:
        for c in item["cells"]:
            url = c["url"]
            if url in downloads:
                continue
            if not local:
                time.sleep(2)  # be polite to the publishers' servers
            try:
                body = (ROOT / item_file(plan, url)).read_bytes() if local else get(url)
                downloads[url] = {"body": body, "sha256": hashlib.sha256(body).hexdigest(), "error": None}
            except Exception as e:
                downloads[url] = {"body": None, "sha256": None, "error": str(e)[:200]}
            print("got " if downloads[url]["body"] else "FAIL", url[:110])
    results = []
    for item in plan["items"]:
        cells = []
        for c in item["cells"]:
            d = downloads[c["url"]]
            row = {"id": c["id"], "url": c["url"], "locator": c["locator"], "recorded": c["value"],
                   "same_file": d["sha256"] == c["sha256"], "fresh": None, "error": d["error"]}
            if d["body"] is not None and c["locator"] not in ("", "not published"):
                try:
                    retained = (ROOT / c["file"]).read_bytes() if (ROOT / c["file"]).exists() else None
                    raw = as_float(read_cell(d["body"], c["file"], c["locator"], retained))
                    row["fresh"] = None if raw is None else raw * c["scale"]
                except Exception as e:
                    row["error"] = f"{type(e).__name__}: {e}"[:200]
            if row["fresh"] is not None and c["value"] is not None:
                row["match"] = abs(row["fresh"] - c["value"]) <= 1e-9 * max(1, abs(c["value"]))
            else:
                row["match"] = None
            cells.append(row)
        fresh_value = None
        if all(r["fresh"] is not None for r in cells):
            if item["formula"]:
                vals = {r["id"]: r["fresh"] for r in cells}
                fresh_value = recompute(item["id"], item["calc"], vals)
            elif len(cells) == 1:
                fresh_value = cells[0]["fresh"]
        page_ok, page_note = page_matches(item)
        if fresh_value is not None:
            fresh_ok, _ = page_matches({**item, "value": fresh_value})
        else:
            fresh_ok = None
        results.append({"n": item["n"], "id": item["id"], "page": item["page"], "text": item["text"],
                        "value": item["value"], "fresh_value": fresh_value, "page_rounds_from_value": page_ok,
                        "page_matches_fresh_source": fresh_ok, "note": page_note, "cells": cells})
    meta = {"checked": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "seed": plan["meta"]["seed"],
            "downloads": {u: {"sha256": d["sha256"], "error": d["error"]} for u, d in downloads.items()}}
    (out / "results.json").write_text(json.dumps({"meta": meta, "results": results}, indent=1, ensure_ascii=False) + "\n")
    good = sum(1 for r in results if r["page_matches_fresh_source"])
    where = "the repository's copies" if local else "the publishers' files downloaded today"
    print(f"{good} of {len(results)} figures match {where}")


def item_file(plan, url):
    return next(c["file"] for i in plan["items"] for c in i["cells"] if c["url"] == url)


def recompute(fid, calc, leaf_values):
    """Redo a figure's calculation from fresh cell values, through any
    intermediate calculations, using the formulas recorded in the sample."""
    if fid not in calc:
        return leaf_values[fid]
    vals = {i: recompute(i, calc, leaf_values) for i in calc[fid]["inputs"]}
    return evaluate(calc[fid]["formula"], vals, calc[fid]["inputs"])


if __name__ == "__main__":
    args = sys.argv[1:]
    cmd = args[0] if args else "sample"
    opt = lambda name: Path(args[args.index(name) + 1]) if name in args else None
    out = ROOT / opt("--dir") if opt("--dir") else None
    if cmd == "sample":
        ids_file = opt("--ids")
        ids = [x.strip() for x in ids_file.read_text().splitlines() if x.strip()] if ids_file else None
        sample(ids, out)
    else:
        check(local="--local" in args, out=out)
