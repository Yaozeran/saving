# Assignment Comparison and Agreed Scope
Original source: .agent/doc/project.docx. On 18 October 2026 the project owner confirmed flexible requirements and requested a Python backend with practical improvements. See docs/SCOPE.md.

## Functional scope
| Original requirement | Current implementation | Scope/evidence |
| --- | --- | --- |
| At least three roles | Customer, Administrator, Auditor | Invited privileged roles; auditor read-only and emails withheld |
| MetaMask and wallet signing | EIP-1193 integration, signed wallet proof | Chromium simulated-wallet workflow passes; actual extension pending |
| Three interacting contracts | One Savings vault | Intentional focused scope; original count differs |
| Ten transaction types | Deposit, withdraw, claim, fund | Four genuine business types retained; original count differs |
| Backend REST / persistent database | Python/FastAPI, SQLite, compatible legacy migration | 16 pytest cases; real Node-hash compatibility |
| Responsive dashboard and history | Chart, filters, pages, CSV and audit trail | Chromium desktop and 390px local-chain checks |
| Event logs | Confirmed receipt-based journal with block metadata | Manual recovery/import; no automatic full-chain indexer |
| Gas estimation | Expiring fee-cap preview before wallet signature | Balance/chain/account rechecks; 20% gas buffer |
| Gas optimisation analysis | Compiler off/on comparison | Measured gas JSON and testing report |
| Smart contract testing | Three local EVM tests | Accounting, reserve, top-up and partial withdrawal |
| Public cloud | Python Docker image and Render Blueprint | Local container checked; public URL pending |

## Deliverable inventory
| Deliverable | Artifact | Qualification |
| --- | --- | --- |
| 10–15 page report | TECHNICAL_REPORT.pdf / .docx | PDF verified at 14 pages |
| Five diagram types | diagrams/ in PNG, SVG and Mermaid | Current Python architecture, vault, model, flow and UI |
| GitHub source/history | SOURCE_CODE.zip, README | Actual repository URL and genuine history not supplied |
| Public deployment details | DEPLOYMENT_RECORD.pdf / .md | Real URL, contract address/hash pending |
| Testing report | TESTING_REPORT.pdf / .md; evidence/ | Local measurements; no security audit |
| Slides | PRESENTATION.pptx / .pdf | Twelve slides with notes |
| Ten-minute video/live demo | DEMO_SCRIPT.pdf / .md | Timed script only; actual performance pending |
| User manual | USER_MANUAL.pdf / .docx / .md | Includes auditor, fee preview and migration |
| Individual contribution | INDIVIDUAL_CONTRIBUTION.pdf / .docx / .md | Zeran Yao, G2509029A, sole contribution |

## Rubric mapping
| Criterion | Original marks | Current evidence |
| --- | --- | --- |
| Problem / validation | 15 | Sourced context and controlled scenarios; no stakeholder pilot |
| Architecture / design | 10 | Five diagrams, API and migration model |
| Contract security | 15 | Principal protection, guarded payouts and tests; no audit |
| Frontend / UX | 10 | Responsive charts, accessible table, fees and browser checks |
| Backend / database | 10 | Python, three roles, sessions, migrations and scoped exports |
| Blockchain functionality | 10 | Four coherent transaction types; relaxed count decision |
| Testing / impact | 10 | Pytest, EVM, browser and gas evidence; social impact unmeasured |
| Cloud / DevOps | 5 | Tested local image, Render configuration; public hosting pending |
| Innovation / feasibility | 5 | Transparent reserve and principal boundary; subsidy economics |
| Report | 5 | Fourteen-page report with contribution table and sources |
| Presentation / demo | 5 | Slides and timed plan; performed-demo evidence pending |

No mark is predicted and original numeric differences are not concealed. Focused implementation follows the agreed flexible scope, while public identifiers and actual demonstration evidence must still be completed truthfully.
