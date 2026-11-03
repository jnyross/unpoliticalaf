# Prompt: impartiality judge

---

Two critics have each listed examples where they think a website about UK
public money leans politically, one arguing it leans left and one right. You
are a neutral judge. You did not build the site.

Inputs: AUDIT_DIR/impartiality/critic-left.md, critic-right.md, and the
written rule in docs/standins/impartiality-rule.md. Check every example
against the built page in `site/` yourself.

For each example, rule:

- **upheld, material**: the page breaks the rule or would mislead a newcomer
  towards one side, as defined in the rule;
- **upheld, minor**: a real but small imbalance;
- **rejected**: the page follows the rule and the example does not show bias,
  with one sentence why.

Then check, across the main pages, the start years of every comparison, the
scales of the charts and the order of groups against the rule, and list any
breach you find that the critics missed.

Write AUDIT_DIR/impartiality/judgement.md: a table of rulings, the breaches you
found, and a last line "Open material findings: N".
