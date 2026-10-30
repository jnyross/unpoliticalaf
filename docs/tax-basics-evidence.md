# Minimum qualitative source evidence

These statements need no current tax-rate table. Use them to explain the numeric displays. Do not merge 2026/27 guidance rates with 2023/24 distribution data.

## Why can a person below the Income Tax allowance still pay tax?

Suggested copy:

> The Personal Allowance applies to Income Tax. It is not an exemption from every tax. A person can owe no Income Tax and still pay VAT through purchases. Some goods and services have no VAT or a different VAT treatment. Household circumstances also affect other taxes.

Evidence:

- `https://www.gov.uk/income-tax`, heading **Income Tax allowances and reliefs**: defines the Personal Allowance as income a person can have before paying Income Tax. The overview says some income is not taxable. Snapshot `basics-income-tax.html`; reading text `basics-income-tax.md`, lines 67–98.
- `https://www.gov.uk/how-vat-works`, **Overview** and **Your responsibilities as a VAT-registered business**: VAT is added to most products and services sold by VAT-registered businesses. Businesses include it in prices and report it to HMRC. Snapshot `basics-vat.html`; reading text lines 67–82.
- The ONS technical report, section **7. Post-tax income**, says VAT is imputed from expenditure on goods and services subject to VAT. It distinguishes exempt, zero-rated, reduced-rate and standard-rate goods. Do not reuse its historical rates or example products as current guidance.

This is a direct synthesis of the first 2 official explanations. Do not say every purchase attracts VAT or that every person pays it.

## What are Income Tax, National Insurance and VAT?

Suggested copy:

> Income Tax applies to taxable income. National Insurance is a separate contribution system linked to employment, self-employment and eligibility for certain benefits. VAT is a tax included in many purchase prices.

Evidence:

- Income Tax overview above: **Overview**.
- `https://www.gov.uk/national-insurance`, **Overview**, **Who pays National Insurance**, **National Insurance classes**: contributions support qualification for certain benefits and the State Pension. Mandatory liability depends on age, employment status and earnings or profits. Do not present it as a personal savings account. Snapshot `basics-national-insurance.html`; reading text lines 69–92.
- VAT overview above: **Overview**.

Do not infer that National Insurance never applies when annual income falls below an Income Tax allowance. Their periods and rules differ. This evidence pack does not support a personal calculator.

## Who sends the money, and who bears the cost?

Suggested copy:

> The person or business that sends tax to HMRC is not always the person who bears its economic cost. Employers send payroll deductions to HMRC. VAT-registered businesses send net VAT to HMRC. The household analysis estimates tax costs under stated assumptions.

Evidence:

- `https://www.gov.uk/paye-for-employers`, **Introduction to PAYE**, **Deductions from their pay**, **Paying HMRC**: employers deduct Income Tax and National Insurance from most employees' pay and pay HMRC. The employer can also owe employer National Insurance. Snapshot `basics-paye-remitter.html`; reading text lines 62–87.
- VAT overview, paragraphs after **Your responsibilities as a VAT-registered business**: businesses normally pay the difference between VAT charged to customers and VAT paid to suppliers. Do not say the business sends the entire VAT-inclusive sales price, or every VAT amount charged, to HMRC.
- ONS technical report `https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/articles/theeffectsoftaxesandbenefitsonhouseholdincome/financialyearending2019`, published **25 June 2020**, sections **7. Post-tax income** and **10. Background notes**, subsection **1. General assumptions**. The model assumes final and intermediate indirect taxes fall on consumers. It also assumes direct taxes fall on the person from whose income they are deducted. It does not establish these assumptions as universal economic facts. Snapshot `ons-technical-2019.html`.

The current workbook also places employer NI in intermediate indirect taxes: `Table 2b!B66` and `C66:L66`. This is an allocation method, not a claim that consumers legally owe employer NI.

## Why is a large Income Tax share not a share of all tax?

Suggested copy:

> A share needs a named total. The top 1% figure uses total Income Tax liability as its denominator. It excludes VAT, National Insurance and other taxes. Household tax percentages use a different denominator: household income or expenditure. Neither display gives a complete estimate of every UK tax's economic burden.

Evidence:

- HMRC `2_4_Taxpayer_share_tax!A1`, `L2`, `K27`: Income Tax liability denominator and 27.2% top-1% value.
- ONS `Table 8!A5,A16,A22`: gross-income, disposable-income and expenditure denominators.
- ONS current Table 2b components and older QMI **5. About the output**, **Relevance**, explain partial coverage. Corporation Tax is not allocated to households. The current direct-tax total includes student loan repayments (`B45`).

## Does this cover Scotland and the devolved nations?

Suggested copy:

> These distribution tables cover the UK. Do not use one England-style tax-band example for everyone. Scotland sets different Income Tax rates and bands on non-savings, non-dividend income. The UK still sets the Personal Allowance and taxes on savings and dividends. Wales also has devolved Income Tax rates. HMRC collects these taxes.

Evidence:

- Scottish Government `https://www.gov.scot/policies/taxes/income-tax/`, **Income Tax**: the Scottish Parliament sets rates and bands for non-savings, non-dividend income. The powers exclude the Personal Allowance. HMRC collects and manages the tax. Snapshot `basics-scottish-powers.html`; reading text lines 58–64.
- `https://www.gov.uk/scottish-income-tax`, **Current rates**: residence in Scotland determines Scottish Income Tax; savings and dividends use the same tax as the rest of the UK. Snapshot `basics-scottish-income-tax.html`; lines 67–70. The adjacent current rate table is not required.
- `https://www.gov.uk/welsh-income-tax`, introductory text and **Who pays the Welsh rates**: Welsh Government sets Welsh rates; residence matters; savings and dividends use UK treatment. **How you pay** explains HMRC tax codes and PAYE. Snapshot `basics-welsh-income-tax.html`; lines 57–89.
- HMRC latest commentary sections 2 and 4 establish UK coverage. Scottish marginal rates are grouped for the published national classifications. The Income Tax share display does not need a separate rate calculation.

Do not claim this short set describes every devolved tax. Property transaction taxes, local taxes and devolved spending need separate source-backed explanations if added.

## Source age and page dates

The guidance pages are living official guidance. Their bodies do not display a publication date. Record retrieval on **30 October 2026**, not an invented release date. Their current rate examples refer to 2026/27, but the proposed copy above uses no rates. The ONS technical report is historical methodology, not current numerical guidance. Prefer current workbook notes where they conflict.


## Seed scope
Only the7register-listed living guidance responses are retained in this seed. ONS methodology and HMRC/ONS numeric sources belong to the separate payer seed; references here are not evidence of their inclusion in this seed. Use no current tax rates or numerical examples from living guidance for2023/24. No product test, independent candidate review, or deployment is claimed by this acquisition.

## Corporation Tax definition

Retained complete official guidance https://www.gov.uk/corporation-tax, Overview:
“Corporation Tax is a tax your company or association pays to HM Revenue and Customs (HMRC) on profits in an ‘accounting period’.”

Suggested short explanation: Corporation Tax applies to taxable company or association profits, including trading, investments and chargeable gains. The OBR revenue group also contains separately named related charges, so it is broader than this definition. The source does not establish who ultimately bears the economic cost. No rate or universal shareholder/consumer burden claim.
