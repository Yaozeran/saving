# Deployment and Repository Evidence Register
Status: preparation complete; public publication and live evidence outstanding.

## Public identifiers
| Required item | Recorded value / status |
| --- | --- |
| GitHub repository URL | Not available; workspace has no Git metadata |
| Source commit / release tag | Not available; do not invent history |
| Render public deployment URL | Not deployed or verified |
| Sepolia contract address | Not deployed or verified |
| Deployment transaction hash | Not available |
| Deployer wallet address | Not recorded |
| Explorer source verification URL | Not available |
| Demo video URL or live-demo record | Not recorded; timed script supplied |

## Known reproducible configuration
Chain ID: 11155111 (Sepolia). Solidity: 0.8.30. EVM target: Shanghai. Optimizer: enabled, 200 runs. Constructor: annualRateBps, default 500. Contract: Savings, in contract/Savings.sol. The deployer's address becomes immutable owner. New contracts added to meet the brief require an updated deployment record.

Runtime: Docker, Python 3.12/FastAPI/Uvicorn backend, Node 24 Next.js standalone frontend, API port 4000 behind web port 10000, SQLite at /app/data/saving.sqlite. Render Blueprint: render.yaml, starter plan and a 1 GB disk. Required service secrets: SEPOLIA_RPC_URL, ADMIN_REGISTRATION_CODE and AUDITOR_REGISTRATION_CODE; required public configuration: CONTRACT_ADDRESS. The deployment key belongs only in the contract deployment environment, never the hosted web app.

## Publication procedure
1. Review the agreed relaxed scope in docs/SCOPE.md and the original-brief comparison. Run `python3 scripts/collect-evidence.py` and regenerate the documents after material changes.
2. Create an actual repository and genuine commits. Follow .gitignore. Verify .env files, signing keys, database files and node_modules are excluded. The source ZIP is a reviewable snapshot, not a hosted repository.
3. Publish to a GitHub repository under your account. Record its URL and actual source commit. No authorised account/session is available here to publish on your behalf.
4. Set testnet-only deployment credentials in contract/.env; run `cd contract && npm run deploy`. Save the printed address and obtain the deployment hash from the deployment wallet or explorer. Verify compiler/arguments when publishing contract source to the explorer.
5. Create a Render Blueprint from the repository, enter RPC and contract values, and deploy. Retrieve the generated admin invitation secret privately. Record the real public URL after opening it successfully.
6. Register an admin, link the owner wallet and fund reserve. Use a separate customer wallet for deposit, withdrawal and interest scenarios. Confirm explorer receipts and record timestamps.
7. Verify HTTPS login, cross-account access restrictions, disk persistence after restart, mobile layout and service recovery. Record actual observations, not just a checkbox plan.
8. Complete the public identifiers above, add redacted screenshots, run the live demonstration or upload a genuine 10-minute recording. Regenerate the submission snapshot after evidence is added.

## Capture checklist
Include: public app URL, successful health check, admin/customer screens with private emails redacted where appropriate, explorer contract page, funding and deposit/withdraw/claim receipts, and persistence/restart evidence. Never publish RPC access tokens, the invitation code, private keys, seed phrases or session cookies. No generated wireframe is a substitute for a deployed screenshot.

## Current release decision
Do not label this version production-ready or claim every original numeric threshold is met. Local build/test evidence exists; public deployment, contribution history and performed demonstration evidence do not. Credentials and service ownership are required to complete external publication; real MetaMask and public-host validation remain necessary. Use APP_ENV=production and the exact PUBLIC_ORIGIN (or Render-provided RENDER_EXTERNAL_URL) for public hosting.
