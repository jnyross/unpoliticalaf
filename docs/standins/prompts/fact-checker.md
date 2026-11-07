# Prompt: adversarial fact-checker

---

Your job is to find factual errors on a website about UK public money and
everyday life. You did not build it and owe it nothing: a mistake you find is
a success. Read the built pages in `site/` (HTML files; the main ones are
`index.html`, `spending.html`, `taxes.html`, `who-pays.html`,
`household-tax.html`, `life/index.html` and the topic pages under `life/`).
Do not read the code in `builder/` or any review of the site.

1. Pick the **30 headline claims** most likely to be wrong or most important to
   a reader: the big numbers at the top of each page, every "largest" or
   "highest" claim, figures after inflation, shares and per-household figures.
   Prefer ones that are calculated over ones copied from a table.
2. Each number on a page is marked up as `<data value="..." data-fact="ID">`.
   Write the 30 ids, one per line, to AUDIT_DIR/fact-check/ids.txt.
3. In AUDIT_DIR/fact-check/claims.md, list each claim as the page states it,
   the page, and anything about the claim that a number check cannot catch:
   wrong period, wrong population or place, wrong units, a "largest" that is
   not the largest, a comparison across a break. Check those against the
   figure records in `site/figures/` and the official source each one links to.
4. Record each problem as **material** (a reader would come away believing
   something false) or **minor**, with the evidence.

The auditor then performs a reviewed intentional accuracy-check run on your ids,
downloading sources again from publishers and comparing them with this exact
candidate. The source-writing workflow stays disabled unless its exact
implementation is independently reviewed for intentional activation; no dormant
schedule or evidence push to main is authorised. Save results on the non-deploying
evidence branch with the audited source SHA. Thirty claims are a sample, not
proof that every headline was checked.
