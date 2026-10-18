# Transaction history recovery — API v2.1

## What was verified

Read-only inspection on 18 October 2026 found the public Render service responding with the Python API and the expected contract configuration. Its deployed version was 2.0.0 at inspection. Sepolia contract `0xC2609E2Ce2E231E3c90DCb6e84C68988f93df3a5` responds at 500 basis points and contains a successful 0.001 ETH deposit:

`0xc4b758167fdf8672ace0c40b4a47005d115c86915abc407f487d26863c09feba`

The Python receipt verifier successfully decoded that deposit through an independent public Sepolia RPC. The deployment's private Alchemy URL, authenticated account bindings and SQLite contents were not accessible, so their exact failure state is not claimed.

## Failure paths corrected

The old frontend waited for MetaMask's provider to report two confirmations and then attempted one backend import. Backend RPC lag, interruption or closing the browser could leave a successful on-chain transaction absent from the database. The submitted hash was held only in React memory. Errors were shown above the dashboard, away from the history form.

Version 2.1 persists public hashes per contract/wallet in browser storage, retries HTTP 409 pending-confirmation responses and attempts saved-hash recovery on login/Refresh. It displays feedback beside history, distinguishes an unrecorded receipt from a failed transfer, and includes a sanitized server RPC check. It does not automatically index every historical transaction.

Admins can recover a confirmed receipt for an already-linked customer's wallet. The API derives the target account from the verified event address and never accepts a browser-supplied user ID or amount. Auditor imports remain forbidden. Unknown wallets are not silently assigned to the admin.

## Recovery on the hosted app

1. Push the changes and deploy the new Render image. `/api/health` must report `2.1.0`.
2. Sign in as the depositing customer, or as administrator.
3. Paste the hash above into the history recovery form and click Import.
4. Inspect the feedback beside history. If RPC access fails, click Check Sepolia connection and correct Render's full HTTPS RPC URL/API key or Alchemy network permissions, then save and redeploy.
5. Refresh customer and administrator history. One verified event should appear without duplicating the deposit.

No contract redeployment or second deposit is required to recover a missing journal entry. New browser hashes are a recovery aid, not a chain indexer. Clearing browser storage removes that aid; the hash can still be imported manually.

## Checks

Python tests cover admin-to-customer receipt attribution, unknown-wallet rejection and sanitized authenticated diagnostics. Frontend tests cover scoping, corrupt storage, confirmation retries, terminal errors and timing-safe gas budgeting. The browser test forces confirmation conflicts and deletes a local test journal row, then verifies recovery on reload. These controlled cases demonstrate the corrected failure paths; they do not establish the exact state of the private deployed database.
