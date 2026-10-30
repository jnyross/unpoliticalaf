# UnpoliticalAF public-source acquisition index

Research retrieved 2026-10-30 UTC. Read-only work; no repository, ticket, provider, deployment or credential changes. Exact per-request times, HTTP outcomes and SHA-256 hashes are in `retrievals.json`. Original public bytes are saved where direct retrieval succeeded; `browser-*.json` preserves bounded native-web extraction results where it did not. Search discoveries are not substituted for downloaded source bytes.

## Dated Commons roster

Authoritative dated endpoint: https://members-api.parliament.uk/api/Parties/StateOfTheParties/1/2026-10-30

Saved as `commons-state-2026-10-30.json`, retrieved 2026-10-30T11:21:18.862760+00:00 (UTC). The endpoint is documented by the downloaded official OpenAPI definition at https://members-api.parliament.uk/swagger/v1/swagger.json. `House=1` is Commons. The requested date is 2026-10-30 00:00:00, not a claimed end-of-day snapshot. The companion live endpoint https://members-api.parliament.uk/api/Parties/GetActive/1 returns the current active labels. Both API responses have `totalResults: 0` despite populated `items`; count `items`, not that metadata value.

The official public page agrees with the dated endpoint: https://members.parliament.uk/parties/Commons. It explains that Independent includes members without the party whip and lists a total of 650 MPs. Its native-web response was read; direct HTTP returned 403. No independent-source roster was used as authority.

| API party ID | Official label | MPs | Acquisition treatment |
|---|---|---:|---|
| 15 | Labour | 404 | Party |
| 4 | Conservative | 118 | Party |
| 17 | Liberal Democrat | 71 | Party |
| 8 | Independent | 11 | Group, not one party or one manifesto |
| 1036 | Reform UK | 8 | Party |
| 29 | Scottish National Party | 8 | Party |
| 30 | Sinn Féin | 7 | Party; keep Westminster separate from Irish elections |
| 7 | Democratic Unionist Party | 5 | Party |
| 44 | Green Party | 5 | Party |
| 22 | Plaid Cymru | 4 | Party |
| 31 | Social Democratic & Labour Party | 2 | Party |
| 1115 | Your Party | 2 | Party; no full costed plan established here |
| 1 | Alliance | 1 | Party |
| 1117 | Restore Britain | 1 | Party; 2026 economic paper located |
| 47 | Speaker | 1 | Office, not party policy |
| 158 | Traditional Unionist Voice | 1 | Party |
| 38 | Ulster Unionist Party | 1 | Party |

This is 17 labels, 15 party labels plus Independent and Speaker, with 650 seats. The StateOfTheParties grouping already includes Labour (Co-op) members in Labour. Do not double count a separate Co-op group or import historic election totals. The member-search API can expose more detailed labels; grouping policy needs to remain explicit.

## Party source acquisition list

`publication_date: null` means a source date has not been established, not that the source is current. A file path containing 2024/06 is not publication-date evidence. Dates below describe launch/publication evidence, not a claim that the 2024 offer remains unchanged in 2026. All source claims are party claims, not independent validation.

| Party | Bounded official material | Source date / scope | Saved result |
|---|---|---|---|
| Labour | https://labour.org.uk/wp-content/uploads/2024/06/Change-Labour-manifesto-2024-screen-reader.pdf | 2024 UK election; launch 13 June 2024 corroborated by IFS. Fiscal plan starts printed p126. | `labour-2024.pdf` |
| Conservative | https://public.conservatives.com/publicweb/GE2024/Accessible-Manifesto/Accessible-PDF-Conservative-Manifesto-2024.pdf | 2024 UK election; launch 11 June 2024 corroborated by IFS. | `conservative-2024.pdf` |
| Liberal Democrat | https://www.libdems.org.uk/manifesto and https://www.libdems.org.uk/sums | Both explicitly labelled 2024. Launch 10 June 2024 corroborated by IFS. | `libdem-manifesto.html`; official plain text in `libdem-2024-plain-text.txt`; costings in `libdem-2024-costings.pdf` |
| Green Party | https://greenparty.org.uk/app/uploads/2024/06/Green-Party-2024-General-Election-Manifesto-Long-version-with-cover.pdf | 2024 UK election; launch 12 June 2024 corroborated by IFS. | `green-2024.pdf`; full costings/annex completeness not checked |
| Reform UK | https://www.reformparty.uk/policies and https://www.reformparty.uk/policies/economic-rescue-plan/download | Current rolling policy page plus Economic Rescue Plan, launched 26 Oct 2026: https://reformparty.uk/news/reform-economic-rescue-plan-jenrick-tax-free-overtime-growth | Native-web verified 36-page PDF; direct HTTP 403. `browser-current-plans.json`, `browser-pdf-links.json`, `browser-landings.json`. No original current PDF bytes saved. |
| Reform UK historical | https://assets.nationbuilder.com/reformuk/pages/253/attachments/original/1718625371/Reform_UK_Our_Contract_with_You.pdf | 2024 Contract; launch 17 June 2024 corroborated by IFS. | `reform-2024-pdf.pdf`; never label this as the current 2026 plan |
| SNP | https://s3-eu-west-2.amazonaws.com/www.snp.org/uploads/2024/06/2024-06-20b-SNP-General-Election-Manifesto-2024_interactive.pdf | 2024 Westminster. Official launch 19 June: https://www.snp.org/snp-leader-john-swinneys-2024-manifesto-speech/ | `snp-2024-pdf.pdf` and launch HTML. PDF discovered via Lancaster's official university index, hosted on party's CDN. |
| SNP newer | https://www.snp.org/manifesto/ | Now explicitly a 2026 Scottish Parliament manifesto; not a UK-wide budget replacement. | `snp-2026.html`; links include official plain-text PDF |
| Plaid Cymru | https://www.partyof.wales/2024 | Explicitly separates Westminster from PCC election documents. 2024 Westminster launch 13 June corroborated by IFS. | `plaid-2024.html`, `plaid-2024-pdf.pdf`; official linked PDF URL in additional-sources.json |
| Sinn Féin | https://sinnfein.ie/news/sinn-fein-launches-manifesto-for-positive-change/ | Official 19 June 2024 Westminster launch. | `sinnfein-2024-launch.html`; links https://vote.sinnfein.ie/wp-content/uploads/2024/06/Sinn-Fein-Westminster-Election-Manifesto-2024.pdf which returned 403. Do not use the November 2024 Irish manifesto. |
| DUP | https://mydup.com/news/speaking-up-for-northern-ireland | Official 24 June 2024 launch links https://s3.eu-west-1.amazonaws.com/my-dup/2024-Manifesto-Final.pdf | `dup-2024.pdf`; native-web landing in `browser-landings.json` |
| Alliance | https://www.allianceparty.org/2024_westminster_manifesto | Official 20 June 2024 landing links the party's NationBuilder CDN PDF. | `alliance-2024.pdf`; landing in `browser-landings.json` |
| SDLP | https://assets.nationbuilder.com/sdlp/pages/753/attachments/original/1719422488/SDLP_Manifesto_2024.pdf | 2024 Westminster, An Election for Change. Exact launch date not established here. | `sdlp-2024.pdf`; party-namespaced CDN; capture official landing-page provenance before treating as fully validated acquisition |
| UUP | https://assets.nationbuilder.com/uup/pages/40/attachments/original/1719233594/General_Election_Manifesto_2024-compressed.pdf?1719233594= | 2024 Westminster. Exact launch date not established here. | `uup-2024.pdf`; party-namespaced CDN; official landing-page provenance remains to capture |
| TUV | https://tuv.org.uk/wp-content/uploads/2024/06/Proof2.pdf | 2024 manifesto, including quoted Reform economic measures. Exact publication day not established. | `tuv-2024.pdf`; do not infer TUV adopts Reform's October 2026 changes |
| Your Party | https://www.yourparty.uk/political-statement/ and https://www.yourparty.uk/political-statement-explainer/ | Retrieved current pages describe an evolved statement of principles, explicitly not a manifesto. Neither page establishes a costed fiscal plan. | `yourparty-statement.html`, `yourparty-statement-explainer.html` |
| Restore Britain | https://www.restorebritain.org.uk/the_wealth_of_our_nation | Official 3 Aug 2026 launch links a 64-page economic philosophy PDF. | `restore-economic-plan-launch.html`, `restore-economic-plan-pdf.pdf`; direct PDF URL in additional-sources.json |
| Restore Britain supplementary | https://www.restorebritain.org.uk/papers and https://www.restorebritain.org.uk/policy_paper_abolish_inheritance_tax | Rolling index and separately dated 17 Mar 2026 inheritance-tax paper. | Index HTML; bounded native-web text in `browser-more-sources.json`. Not a complete independent audit. |

## Independent assessment acquisition list

The IFS 2024 index is https://ifs.org.uk/election-2024/general-election-2024-manifesto-analysis-ifs. It links all seven dated assessments below. Native web verified their existence; direct IFS article HTTP retrieval returned 403. `browser-assessments.json` contains bounded native-web responses. Its longer first entry includes the Labour response, but it is not a complete archival copy of all seven articles.

| Party | IFS assessment | Publication date |
|---|---|---|
| Labour | https://ifs.org.uk/articles/labour-party-manifesto-initial-response | 2024-06-13 |
| Conservative | https://ifs.org.uk/articles/conservative-manifesto-initial-response | 2024-06-11 |
| Liberal Democrat | https://ifs.org.uk/articles/liberal-democrat-manifesto-reaction | 2024-06-10 |
| SNP | https://ifs.org.uk/articles/snp-manifesto-reaction | 2024-06-19 |
| Green Party | https://ifs.org.uk/articles/green-party-manifesto-reaction | 2024-06-12 |
| Plaid Cymru | https://ifs.org.uk/articles/plaid-cymru-manifesto-response | 2024-06-13 |
| Reform UK | https://ifs.org.uk/articles/reform-uk-manifesto-reaction | 2024-06-17 |

The 24 June 2024 IFS comparative presentation is saved as `ifs-2024-finances.pdf` from https://ifs.org.uk/sites/default/files/2024-06/The%20public%20finances%20in%20the%20coming%20Parliament.pdf. Its chart explicitly distinguishes Reform's averages across Parliament from other parties' 2029-30 figures. Preserve those period/unit differences.

Resolution Foundation: https://www.resolutionfoundation.org/publications/the-economic-battle-lines-of-the-general-election/ and https://www.resolutionfoundation.org/publications/growing-for-gold/ both dated 14 June 2024, saved as HTML. The first compares Conservative and Labour; the second assesses Labour's tax and spending package. These are dated assessments of 2024 proposals, not current-plan validation.

Full Fact: https://fullfact.org/manifestos/ is saved as HTML and text. Seven separate 2024 claim-check pages are linked below; these are claim-level checks, not whole-programme fiscal certifications. The live index has date oddities, including 12 June for Labour while its article says launch was 13 June. Store displayed dates and source context faithfully rather than automatically repairing them.

- https://fullfact.org/election-2024/reformuk-manifesto/
- https://fullfact.org/election-2024/snp-manifesto/
- https://fullfact.org/election-2024/labour-manifesto/
- https://fullfact.org/election-2024/green-manifesto/
- https://fullfact.org/election-2024/plaidcymru-manifesto/
- https://fullfact.org/election-2024/conservative-manifesto/
- https://fullfact.org/election-2024/lib-dem-manifesto-fact-checked/

OBR: https://obr.uk/faqs/ explicitly states it does not certify opposition manifesto policies. Treat OBR economic and fiscal forecasts as dated baseline/context, not an invented party scorecard. Current remit material: https://obr.uk/about-the-obr/legislation-and-related-material/. Native-web retrieved; direct downloads returned 403. Recheck the latest governing instrument before making a legal assertion, since the index now lists 2026 changes.

NAO: https://www.nao.org.uk/support-for-parliament/ is saved as HTML and text. It says its work examines how government money was used, without questioning policy objectives. Use relevant reports as implementation/value-for-money evidence, not a claim that NAO has audited every party's manifesto.

## Gaps and ingestion rules

1. Fresh roster is verified, but this is a bounded initial document bundle, not proof that the latest fiscal platform for every party has been exhaustively collected. Current Labour government budgets and opposition 2025/2026 updates require their own dated ingestion. No comprehensive post-2024 survey for all parties is claimed.
2. Your Party has retrieved principles but no established full costed fiscal plan. Current 2026 independent assessments for Restore Britain or Reform's 26 October plan were not located in bounded searches of IFS, Resolution Foundation and Full Fact. Label those cells as missing evidence, not zero impact or assessed.
3. Separate political party, Commons affiliation group and office. Independent cannot inherit a collective manifesto; Speaker should have no fiscal platform. Keep the official party ID and date in every roster record.
4. Each extracted policy needs source URL, saved-byte hash, retrieval time, publication/launch date with its evidence, document jurisdiction, page/section, stated price basis, fiscal years and whether the number is annual/cumulative. Do not compare annual and Parliament-total numbers without an explicit transformation.
5. Preserve party-authored assertions separately from independent assessments. Neither a party's phrase 'fully costed' nor publication on an official site establishes independent verification.
6. Direct HTTP originally failed on several domains; a standard browser User-Agent recovered most PDFs. Remaining 403s are recorded, not silently replaced. Native web successfully read Reform's current PDF and IFS articles. A credential-free factory needs an allowed retrieval route for those sources or must carry a visible acquisition failure. Green's landing produced a native-web 402, but its official static PDF downloaded without credentials or payment.
7. Original PDF bytes are retained, but no PDF extraction library was available locally and none was installed. PDFs were identified by `%PDF` magic and those visited with native web showed page counts. Full paragraph extraction, fiscal table parsing and independent verification are still downstream work.
8. No credentials, private context, repository source or user personal information were sent in queries. No package installation, external code execution, repository edits, GitHub writes, model/provider changes or deployment occurred.
