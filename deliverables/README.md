# Saving — Assignment Deliverables
Prepared against `.agent/doc/project.docx` on 18 October 2026.
Author and sole contributor: **Zeran Yao · G2509029A**.

## Start here

- **TECHNICAL_REPORT.pdf** — fixed-layout, verified **14 pages**, including problem evidence, stakeholders, requirements, engineering design, security, testing, impact limits, contribution table and references.
- **TECHNICAL_REPORT.docx** — editable Word counterpart. Word pagination can vary with fonts/settings; the PDF is the page-count reference.
- **PRESENTATION.pptx / PRESENTATION.pdf** — 12 slides, with presenter notes in the PowerPoint and PRESENTATION_NOTES.md.
- **USER_MANUAL.pdf / .docx / .md** — customer and administrator instructions, wallet workflow and troubleshooting.
- **INDIVIDUAL_CONTRIBUTION.pdf / .docx / .md** — sole contribution statement and artifact mapping.
- **TESTING_REPORT.pdf / .md** — actual automated results, local gas estimates/receipts, optimizer comparison and limitations.
- **diagrams/** — architecture, contract interaction, database, process and UI diagrams; PNG, SVG and editable Mermaid sources for each.
- **DEMO_SCRIPT.pdf / .md** — timed 600-second plan for the required live demonstration or recording.
- **DEPLOYMENT_RECORD.pdf / .md** — deployment settings, publication steps and missing evidence register.
- **COMPLIANCE_MATRIX.pdf / .md** — brief requirements, actual implementation status and rubric mapping.
- **evidence/** — raw test/build logs, return codes and measured gas data.
- **SOURCE_CODE.zip** — clean source snapshot; excludes secrets, databases, dependencies and generated builds. This is not a GitHub repository or contribution history.
- **SUBMISSION_BUNDLE.zip** — all deliverables plus the source snapshot.

## Agreed scope and external evidence

The agreed flexible scope prioritises a Python backend and practical improvements. Customer, Administrator and invited Auditor roles, charts, paginated/filterable history, CSV export, audit records and an in-app fee preview are implemented. We deliberately retain one focused vault and four business transaction types; the original counts are disclosed in COMPLIANCE_MATRIX.md and docs/SCOPE.md rather than driving unrelated features.

Public Render/Sepolia identifiers, authentic GitHub history, actual MetaMask extension acceptance and a performed video/live demonstration remain pending. Browser screenshots are actual local Chromium/Ganache renders with a simulated wallet, not public deployment screenshots. Stakeholder feedback is not claimed.

## Regenerate

Use Python 3.11+ and install `scripts/requirements-deliverables.txt` in a virtual environment. From the project root:

1. Install backend Python dependencies in backend/.venv from requirements-dev.txt; use `npm ci` in contract and web.
2. Run `python3 scripts/collect-evidence.py` for actual fresh results.
3. Run `python3 scripts/build-deliverables.py` for report, diagrams and slides.
4. Run `python3 scripts/package-deliverables.py` for archives, artifact checks and hashes.

The generator refreshes the measured-gas paragraph from the captured JSON. Review the results after rerunning measurements. Current document date is fixed to the submission preparation date above, not silently updated. The source does not use AI-generated artwork; diagrams are code-drawn technical figures.
