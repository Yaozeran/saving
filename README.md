# Saving

Sepolia savings DApp by **Zeran Yao (G2509029A)**. Next.js dashboard, **Python/FastAPI backend**, SQLite persistence and a Solidity savings vault. Testnet only.

Customers deposit Sepolia ETH, withdraw principal and claim simple interest. Administrators fund the reward reserve with their own wallet. Invited auditors inspect activity without transaction-import permissions or access to account emails. The dashboard includes 14-day charts, history filters/pagination, CSV export, an account audit trail and a fee preview before wallet signing.

## Run locally

Use **Python 3.12**, **Node.js 24 LTS**, and MetaMask with Sepolia ETH.

1. In `contract`: `npm ci`, `npm test`, `npm run compile`.
2. Copy `contract/.env.example` to `contract/.env`, set your Sepolia RPC URL and a testnet-only deployer key, then run `npm run deploy`. Save the contract address. Its deployer is the immutable owner.
3. In `backend`: `python3 -m venv .venv`, then `.venv/bin/pip install -r requirements-dev.txt`. Copy `.env.example` to `.env` if it does not exist. Set RPC URL, contract address and different random admin/auditor invitation secrets.
4. From `backend`, run `.venv/bin/uvicorn main:app --host 127.0.0.1 --port 4000 --no-proxy-headers`.
5. From `web`, run `npm ci` and `npm run dev`. Open http://localhost:3000. API calls are proxied to port 4000. Development API docs: http://127.0.0.1:4000/api/docs.
6. Register an Administrator using its invitation, connect the deploying owner wallet and fund reserve. Register a Customer without an invitation and link a separate wallet. Auditors use the separate auditor invitation and receive read-only reporting access.

Private keys never enter the web backend. Wallet messages verify ownership; transactions require separate wallet signatures. An application administrator is not automatically the contract owner.

## Python migration

The Node backend has been replaced. Existing SQLite users, password hashes, wallet bindings, sessions and transaction rows remain compatible. Startup performs an additive migration adding block metadata, an audit table and indexes. Historical rows retain their original recorded timestamp and show “Legacy record” when block time is unknown. Back up a real database consistently before upgrading. The automated migration test starts from the original Node schema and checks repeated migration, while the password test verifies actual Node scrypt output.

## Docker and Render

`docker build -t saving .`

For localhost testing only:

`docker run --rm -p 10000:10000 --env-file backend/.env -e APP_ENV=development -v saving-data:/app/data saving`

For public hosting use **APP_ENV=production**, HTTPS and **PUBLIC_ORIGIN=https://your-hostname**. Render provides `RENDER_EXTERNAL_URL` automatically; it is used when PUBLIC_ORIGIN is blank. A nonempty PUBLIC_ORIGIN must exactly match the browser origin. Copying the sample development .env to a production host requires changing APP_ENV.

Create a Render Blueprint from `render.yaml` after pushing the source to your Git provider. Enter RPC and contract values; retrieve the generated admin and auditor invitations privately from service settings. A paid disk-backed service stores SQLite at /app/data. Keep one instance. Use SQLite online backup or a stopped, consistent copy including WAL files; test restoration separately.

No public URL or live contract address is claimed. Deployment needs your service account and Sepolia credentials. The container runs Python for the API and Node only for Next.js and its supervisor.

## Verification

- Backend: `cd backend && .venv/bin/python -m pytest test_api.py -q`.
- Contract: `cd contract && npm test && npm run benchmark`.
- Frontend: `cd web && npm run lint && npm run build`.
- All core evidence: `python3 scripts/collect-evidence.py`.
- Optional Chromium/local-EVM integration: install Playwright into a separate tools virtual environment, run `python -m playwright install chromium`, then `python scripts/browser-smoke.py` using that interpreter. Requires installed backend/contract dependencies and a frontend production build. It uses temporary data and a simulated wallet, never a real wallet or public funds. Ports 4000, 4173 and 18545 must be free.

## Accounting and reporting

Default immutable APR is 500 basis points (5%), simple interest over a 365-day year, in integer wei. Interest never compounds automatically. Only cash above total principal can pay interest. Reserve exhaustion blocks interest claims but not principal withdrawals. Available reserve is not a guarantee that every unclaimed liability is covered.

Receipt imports check Sepolia chain ID, successful direct transaction to the configured vault, two confirmations, canonical block hash at import, contract emitter and linked-wallet event. Import is idempotent. The journal does not automatically index external wallet activity or reconcile later reorganisations. Keep a submitted transaction hash for recovery. A replacement/cancelled transaction needs its final successful hash.

History distinguishes block time from recording time; charts group the last 14 days by recording time. Pagination is 10 rows in the UI (up to 100 via API); CSV exports the latest 10,000 matching account-scope events. Admins see email-linked history; auditors see wallets without emails. The audit trail records successful account lifecycle and import events, not every failed attempt or a tamper-proof external log.

## Project scope and deliverables

The agreed scope uses the assignment as a flexible guide: see [agreed scope](docs/SCOPE.md). We intentionally retain one focused savings contract and four meaningful transaction types. There are three app roles. Original-count comparisons remain transparent in the [scope matrix](deliverables/COMPLIANCE_MATRIX.md).

See the [deliverable index](deliverables/README.md) for the report, slides, diagrams, manuals, test evidence and demonstration script. Public deployment, actual MetaMask acceptance, authentic GitHub history and a performed demonstration remain external evidence items. Generated screenshots are explicitly labelled local-chain/simulated-wallet tests.

Technical references: [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/), [Web3.py contracts](https://web3py.readthedocs.io/en/stable/web3.contract.html), [ethers v6](https://docs.ethers.org/v6/), [Render persistent disks](https://render.com/docs/disks).

## Missing transaction recovery (v2.1)

A successful wallet transaction can exist on Sepolia before the backend RPC sees two confirmations. The browser now retries pending-confirmation imports, saves submitted hashes per contract/wallet in local storage, and attempts recovery on login or Refresh. It never creates confirmed history from a browser-supplied amount. Import feedback appears beside history as well as in the sticky status notice.

To recover an older deposit, paste its transaction hash into the history Import form. Customers can import their own wallet events; admins can import events for any already-linked registered wallet, and ownership is derived from the contract log. Auditors remain read-only. The Check Sepolia connection button checks the server's private RPC configuration without exposing its URL/API key. A connection error does not mean the original on-chain deposit failed; check its explorer receipt before sending more funds.

Additional frontend regression checks: `cd web && npm test`. The Chromium test simulates backend confirmation lag and a missing journal entry recovered on reload. `/api/health` reports version 2.1.0 after this release is deployed.
