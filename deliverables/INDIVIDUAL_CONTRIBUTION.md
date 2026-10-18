# Individual Contribution Report
Enterprise Financial DApp · Saving · 18 October 2026

## Contributor declaration
| Name | Student number | Project role | Share |
| --- | --- | --- | --- |
| Zeran Yao | G2509029A | Sole contributor | 100% |

The ownership and contribution allocation follow the student's instruction that the project was built individually. This report does not invent group members or split percentages across fictitious collaborators.

## Contribution mapped to artifacts
| Area | Work represented | Inspectable artifacts |
| --- | --- | --- |
| Requirements | Savings use case, wallet flow, role and persistence requirements | .agent/task.txt; deliverables/COMPLIANCE_MATRIX.md |
| Contract | Principal, simple interest, reserve funding and payout accounting | contract/Savings.sol; contract/deploy.mjs |
| Backend | REST API, password sessions, wallet proof, receipt journal | backend/main.py |
| Frontend | Responsive dashboard, account forms, MetaMask and transaction feedback | web/src/app/page.tsx; web/src/app/globals.css |
| Testing | API and EVM scenarios; build/lint; gas experiment | backend/test_api.py; contract/test/; contract/benchmark.mjs |
| DevOps | Non-root runtime, supervised services and persistent disk Blueprint | Dockerfile; start.mjs; render.yaml |
| Documentation | Report, diagrams, manual, slides and demonstration script | deliverables/; scripts/build-deliverables.py |

## Evidence and limits
Use source inspection and real version history to evaluate the contribution. No Git metadata existed in the workspace during deliverable preparation, so there is no verified GitHub URL, commit count, historical timeline or per-person commit distribution. Source archive hashes identify the submitted snapshot but are not a substitute for contribution history. Publish authentic commits; do not backdate or fabricate earlier activity.

Implemented functionality now includes a Python backend, three roles, charting, fee previews, paginated history, exports and an audit trail. One contract and four genuine transaction types are retained under the project owner's relaxed scope. Public deployment, authentic repository history, actual MetaMask acceptance and a performed demonstration are not claimed. Migration and compatibility tests support the backend transition.

## Reflection
The key design decision was to separate account identity from custody. Password login controls private portal access, while wallet signatures authorise on-chain movements. Another significant decision was to protect principal from interest claims, accepting that insufficient sponsor funding delays interest payouts. The main learning is that an explicit formula and passing local tests do not demonstrate a viable or enterprise-ready financial service. Sustainability, privacy, recovery, usability and operational evidence need independent attention.

## Student confirmation
Confirm this statement before submission: the listed identity, scope and contribution share reflect the work you are submitting. No signature or attestation has been generated on the student's behalf.
