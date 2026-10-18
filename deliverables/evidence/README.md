# Evidence scope

checks.json and matching logs record actual Python/contract/frontend checks. The Python suite has 16 cases; the local EVM suite has three tests. docker-checks.json and logs record the Python runtime image build and proxied health/Origin/session/analytics test. browser-smoke.json records an actual Chromium run against the Python API and an isolated Ganache chain.

The browser wallet is a simulated EIP-1193 adapter using unlocked local test accounts. Screenshots dashboard-local-desktop.png and dashboard-local-mobile.png are real browser renders of that local test, not a public deployment or actual MetaMask extension. The local chain advances a simulated year to exercise interest claims, so block timestamps can be later than recording timestamps. No private keys, seed phrases or real user data are included. Emails and invitations used in tests are disposable examples.

The browser workflow covers customer registration, wallet proof, fee previews, deposit/withdraw/claim execution, two confirmations and journal import, chart table/filter/export, mobile width and auditor read-only controls. It does not replace live Sepolia, real MetaMask, user research, load testing, an external audit, GitHub history or a performed presentation.

artifact-checks.json and SHA256SUMS.txt validate the generated submission snapshot; they are not proof of public publication or independent assessment.
