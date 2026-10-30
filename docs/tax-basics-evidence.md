# Retained qualitative tax-guidance evidence

## Scope and versions

Only the 7 official guidance responses listed below belong to this guidance seed.
`data/tax-basics/sources.json` records retrieval on **30 October 2026**, original
response hashes and lossless-envelope hashes. Each file is an ASCII JSON envelope:
decode `original_response` as UTF-8 to recover the unchanged original response.
No publication date is established for these living pages. The next update is
unknown. Do not apply their current rates to the payer distribution year or turn
these definitions into personal tax examples.

The locators below are source headings, not invented reading-text line numbers.
GOV.UK guide responses can retain linked guide-part text in structured article
content. The independent source checker must verify meaningful heading elements
and the companion body text in the retained response. A heading word elsewhere
in the page is not sufficient evidence.

## The 7 retained responses

1. **Income Tax** — https://www.gov.uk/income-tax
   - Envelope: `data/tax-basics/raw/basics-income-tax.html.json`.
   - Headings: **Overview**; **Income Tax allowances and reliefs**.
   - Evidence: Income Tax is a tax on income; not all income is taxable. Most
     people get a Personal Allowance of tax-free income.
   - Limit: this allowance concerns Income Tax, not exemption from every tax.

2. **National Insurance** — https://www.gov.uk/national-insurance
   - Envelope: `data/tax-basics/raw/basics-national-insurance.html.json`.
   - Headings: **Overview**; **Who pays National Insurance**;
     **National Insurance classes**.
   - Evidence: contributions qualify people for certain benefits and the State
     Pension. The type depends on employment status and earnings. The retained
     Who pays section distinguishes employment earnings per week from one job
     and self-employed profits per year; its full clauses, not isolated time
     words, support the different-rules and payment-period explanation.
   - Limit: it is not a personal savings account. Do not infer that a person
     below the annual Income Tax allowance can never owe National Insurance.

3. **PAYE for employers** — https://www.gov.uk/paye-for-employers
   - Envelope: `data/tax-basics/raw/basics-paye-remitter.html.json`.
   - Headings: **Introduction to PAYE**; **Deductions from their pay**;
     **Reporting pay and deductions**; **Paying HMRC**.
   - Evidence: PAYE collects Income Tax and National Insurance from employment.
     Employers deduct these from most employees' pay, report deductions and pay
     HMRC. Employers can also owe employer National Insurance.
   - Limit: collection duties do not establish ultimate economic burden.

4. **Scottish Government Income Tax** — https://www.gov.scot/policies/taxes/income-tax/
   - Envelope: `data/tax-basics/raw/basics-scottish-powers.html.json`.
   - Heading: **Income Tax**.
   - Evidence: Scottish powers cover rates and band thresholds, excluding the
     Personal Allowance, for non-savings, non-dividend income of Scottish
     taxpayers. HMRC collects and manages Scottish Income Tax.
   - Limit: this does not supply a Welsh rule or a universal UK rate example.
     The separate GOV.UK Scottish Income Tax response is not retained here.

5. **How VAT works** — https://www.gov.uk/how-vat-works
   - Envelope: `data/tax-basics/raw/basics-vat.html.json`.
   - Headings: **Overview**; **Your responsibilities as a VAT-registered business**;
     **What VAT is charged on**; **How much VAT you must charge**.
   - Evidence: VAT is added to most products and services sold by VAT-registered
     businesses. If charged VAT exceeds paid VAT, the business pays the difference
     to HMRC. Some goods and services are exempt, unaffected, reduced-rated or
     zero-rated.
   - Limit: not every purchase attracts VAT. The remittance is not the entire
     VAT-inclusive sale price or necessarily every VAT amount charged.

6. **Welsh Income Tax** — https://www.gov.uk/welsh-income-tax
   - Envelope: `data/tax-basics/raw/basics-welsh-income-tax.html.json`.
   - Headings: **Income Tax in Wales**; **Who pays the Welsh rates**; **How you pay**.
   - Evidence: the Welsh Government sets Welsh rates for people living in Wales.
     The page states that dividends and savings interest use the same tax as the
     rest of the UK. HMRC adds a C to the tax code.
   - Limit: use this Welsh source for Welsh claims, not a Scottish source quote.

7. **Corporation Tax** — https://www.gov.uk/corporation-tax
   - Envelope: `data/tax-basics/raw/basics-corporation-tax.html.json`.
   - Headings: **Overview**; **Profits you pay Corporation Tax on**.
   - Evidence: companies or associations pay Corporation Tax to HMRC on profits
     in an accounting period. Taxable profits include trading, investments and
     chargeable gains.
   - Limit: this definition does not establish who ultimately bears the cost.
     The OBR receipt grouping contains separately named related charges and is
     broader than the basic definition.

## Separation from the fiscal sources

These guidance sources explain rules and collection, not the fiscal figures.
The HMRC liability shares, ONS household percentages, older ONS technical report
and OBR receipts have their own retained datasets and independent checkers.
They are not extra responses in this 7-file guidance register. In particular,
there is no `ons-technical-2019.html` or Markdown reading-text file in this seed.
The payer methods record owns the older methodology, workbook notes and their
limits. The current workbook takes priority where older methods differ.

Income Tax liability shares do not become shares of all tax. ONS income and
expenditure denominators stay separate. Collection does not establish burden.
The numeric source contracts, population limits, suppressed cells and source
notes must remain in force when these qualitative explanations are inserted.

## Evidence status

The native review of candidate `d5baa129eb7bc8ef924e2fe631a00b9473a3093d`
blocked hidden basics containers and recorded methods/provenance advisories.
This record corrects unretained snapshot names and unsupported line locators.
The repair still needs exact-candidate checks and independent review. This
source record does not claim a new build, test, review approval or deployment.
