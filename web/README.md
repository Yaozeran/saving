# Saving frontend

Next.js App Router dashboard for the Saving Sepolia vault. See [the project guide](../README.md) for full Python backend, contract and deployment setup.

Use Node.js 24. Run `npm ci` and `npm run dev` in this directory; the Python API must run at 127.0.0.1:4000. Open http://localhost:3000. Checks: `npm run lint` and `npm run build`.

The browser uses ethers for MetaMask/EIP-1193, signed wallet proof and transaction gas previews. No signing keys are stored in the application. Customer/admin/auditor access, activity charts, history filters/pages, CSV and an account audit trail are supported by the Python API. Wallet actions require Sepolia and the linked address. Auditors have read-only financial controls.

For reproducible Chromium/local-chain integration see scripts/browser-smoke.py and the root guide. This simulation is separate from actual MetaMask/public Sepolia acceptance.
