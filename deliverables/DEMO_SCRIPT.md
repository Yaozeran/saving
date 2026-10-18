# Ten-minute Live Demonstration / Recording Script
Prepared for Zeran Yao · G2509029A. This is an executable presentation plan, not evidence that a video or live demonstration has occurred.

## Preparation
Use a configured Sepolia deployment, two funded test wallets, separate admin/customer browser profiles, the explorer contract page and the test logs. Open the presentation, app and terminal before starting. Fund the reserve before demonstrating a claim. Have an existing aged deposit if a visible interest payout is required. Do not change time on Sepolia; simulated time travel is available only in the local EVM tests. Keep seed phrases, invitation secrets, .env files and cookies out of frame. Record the actual public URL and contract details in DEPLOYMENT_RECORD.md.

## Timed run of show
| Time | Presenter narration and action | Visible evidence |
| --- | --- | --- |
| 00:00–00:45 | Introduce name, student number and the sponsor-funded membership savings problem. Explain that this is a testnet prototype. | Slide 1; scope statement |
| 00:45–01:30 | Explain contextual evidence, stakeholders and why independently executable accounting is being investigated. Avoid claiming proven demand or financial inclusion impact. | Slides 2–3; source citation |
| 01:30–02:15 | Explain browser, MetaMask, API, SQLite and vault trust boundaries. State that one contract is intentionally retained under the agreed scope. | Architecture and contract diagrams |
| 02:15–03:15 | Show account registration/login and linked MetaMask wallet. Explain the difference between a message signature and an ETH transaction. Use an already-linked account if prompts would delay the schedule. | Customer profile and address |
| 03:15–04:15 | Enter a small deposit, inspect the MetaMask network, destination and fee, then confirm. Keep the transaction hash visible. | Wallet prompt and explorer receipt |
| 04:15–05:00 | Show reserve funding using the admin's owner wallet or a previously confirmed funding receipt. Explain that admin login alone does not grant contract ownership. | Admin controls and Funded event |
| 05:00–06:00 | Claim an existing accrued balance, inspect the receipt, then show a partial principal withdrawal or its confirmed receipt. Explain insufficient-reserve behaviour. | InterestPaid / Withdrawn events |
| 06:00–06:45 | Refresh history and demonstrate receipt import without duplicate rows. Explain that history covers recorded events only, and recording time differs from block time. | Journal and matching explorer log |
| 06:45–07:45 | Show current captured test output and the optimizer gas table. Label the one-year EVM time jump as simulation. Do not present local gas as a live fee forecast. | TESTING_REPORT and evidence logs |
| 07:45–08:45 | Explain Docker, Render configuration, persistent storage and actual deployment status. If no public service exists, explicitly state this gap rather than substituting localhost. | Public URL if available; deployment register |
| 08:45–09:30 | Review security controls, reserve sustainability, implemented auditor/chart/fee controls, agreed count differences and unmeasured usability. | Compliance slide |
| 09:30–10:00 | State sole contribution, remaining work and what the prototype demonstrates. Stop at ten minutes. | Contribution slide; conclusion |

Total planned duration: 600 seconds. Transaction confirmation may exceed its allocated segment. If pending, retain the hash, show a clearly identified earlier receipt, and return to the submitted transaction when confirmed. Do not edit a pending operation to imply success.

## Live-demo fallback
If the RPC or testnet is unavailable, use local tests as a separately labelled technical demonstration and disclose the live failure. Screenshots and prerecorded receipts can support explanation but cannot be described as a transaction performed live. The assignment permits either a genuine recording or an actual live demonstration; this script alone satisfies neither performance requirement.

## Evidence to add after performance
Record demonstration date, actual duration, public video URL or live-demo setting, contract address, transactions shown and observed failures. Obtain permission before recording any audience participant. No attestation, video, attendance or feedback has been fabricated.
