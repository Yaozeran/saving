# Saving — User Manual
Version: prototype · 18 October 2026 · Zeran Yao (G2509029A)

## 1. Before you begin
This app uses Sepolia test ETH only. It is not a bank account, an insured deposit or an investment product. Have MetaMask installed, an Ethereum account you control, some Sepolia ETH for your deposit and transaction fees, and a configured deployment or a locally running app. The public deployment URL is not yet available. Follow README.md to run the web and API services locally at http://localhost:3000.

A service administrator must deploy Savings.sol and set the same address and Sepolia RPC URL in the backend. Without that configuration, registration still works but on-chain features show a configuration error. Never paste your seed phrase or private key into the website, report or support message.

## 2. Register and sign in
Choose Create an account, enter your email and a password containing 12–128 characters, and submit. Choose Customer for a normal account. Existing users choose Sign in. The current prototype has no email verification or forgotten-password recovery. Use a test account and retain your login details securely.

The app supports Customer, Administrator and Auditor. Select the account role at registration. Customer needs no invitation; the other roles require their respective secret invitation codes. An admin invitation grants access to email-linked activity across all accounts and must be distributed carefully. Selecting a different wallet does not change your application identity.

## 3. Link MetaMask
Select Connect MetaMask. Approve the account connection and Sepolia switch request if shown. Sign the verification message identifying your application account. This message proves wallet ownership; it does not deposit funds. Each account is permanently associated with one wallet and a wallet cannot be associated with two application accounts. Check the abbreviated address against the selected MetaMask address.

If you choose the wrong wallet before signing, cancel. After linking, changing the selected MetaMask account will cause transactions to be rejected until you switch back to the linked address. Account recovery or relinking is not currently available.

## 4. Deposit and view your savings
Enter a positive ETH amount, such as 0.01, and choose Preview deposit. Review the in-app gas estimate, fee cap, destination and network. The fee cap includes a 20% buffer plus a 30,000-unit timing allowance and expires after 60 seconds. Choose Confirm in MetaMask and check the wallet prompt before signing. Leave enough Sepolia ETH in the wallet for gas. The app waits for two confirmations before recording a transaction. The wait depends on the chain and RPC provider; it is not guaranteed to finish within a fixed number of seconds.

Total deposited is your remaining principal. Interest earned is accrued, unclaimed simple interest. The APR comes from the deployed contract and cannot be changed in this version. At 5% APR, 1 ETH held for an exact 365-day year earns 0.05 ETH before rounding. Refresh to fetch a newer on-chain balance; the displayed figure is not continuously streamed. Claimed interest does not automatically compound.

## 5. Withdraw principal or claim interest
To withdraw, enter an amount no greater than your principal and choose Preview withdrawal, then confirm the fee preview and approve in MetaMask. A withdrawal reduces your principal and preserves previously accrued interest. Choose Preview interest claim to request your entire accrued amount. The claim fails if interest is zero or the reserve cannot fund the whole amount. Principal is not used to pay interest. Transaction fees apply even when economic interest is very small.

A successful payout goes directly to the wallet. The application admin cannot withdraw user principal. A confirmed on-chain transaction cannot be undone through the website. Do not repeat a transaction merely because the page is slow; inspect the original hash first.

## 6. Transaction history and recovery
History contains events imported by the app, not every action ever performed with the wallet. Select an event's explorer link to inspect its receipt. History displays both block time and recording time in UTC. Old migrated records with unknown block time are labelled Legacy record. Filter by event type and use Previous/Next for ten rows per page. Export CSV downloads up to 10,000 recorded events in your access scope. Admins see email-linked activity across accounts; auditors see cross-account wallets without email addresses; customers see their own.

If the browser closed after signing, find the transaction hash in MetaMask or the Sepolia explorer. Paste that hash into Recover a transaction and choose Import after two confirmations. Reimporting the same receipt does not duplicate the recorded event. Transactions to other contracts or without a matching linked-wallet event cannot be imported.

## 7. Administrator workflow
Register using the invitation secret from your configured service environment. Connect the exact wallet that deployed the contract. The application role does not make another wallet the contract owner. Enter a funding amount and choose Preview reserve funding and review its fee cap before signing, then confirm in MetaMask. Verify the Funded event and available reserve after confirmation.

Funding moves the administrator's own ETH to the vault. It does not immediately pay users; each user claims their own earned amount. Reserve cash is not a guarantee that all accrued and future obligations are covered. The current UI has no reserve liability projection, owner transfer or reserve withdrawal action.

## 8. Troubleshooting
| Message / symptom | Action |
| --- | --- |
| Install MetaMask | Install or enable the extension in the current browser |
| Select your linked account | Switch MetaMask back to the account linked during verification |
| Request a new wallet challenge | Reconnect and sign the newly issued message within five minutes |
| Wallet belongs to another account | Sign into that account; linking to multiple accounts is disallowed |
| Fund interest reserve | Ask the operator to fund the vault; do not retry blindly |
| Wait for two confirmations | Check explorer status, wait, then import the same hash |
| Service/RPC configuration error | Operator checks RPC chain, availability and contract address |
| No history after a successful transfer | Use the hash import; check that transfer called the configured vault |
| Login fails only in Docker | Production cookies require HTTPS; use the documented localhost development mode only for local testing |

Sign out after using a shared computer. Do not disclose passwords, invitation secrets, wallet keys or RPC credentials in screenshots. The manual describes the existing prototype; it does not assert that missing assignment features are present.

## 9. Charts and auditor workspace
The chart shows deposits, withdrawals, interest payouts and reserve funding over the last 14 UTC recording dates. Select a series, hover a bar or expand the accessible data table. It is a journal-activity chart, not a complete blockchain balance history or a prediction. Late imports appear on their recording date.

Register an Auditor using the separate auditor invitation. Auditors can inspect cross-account wallet events, charts, CSV and the latest 20 account audit records. They cannot import receipts through the API, and financial controls are disabled. Wallet linking and sign-out still work. Application read-only permissions do not prevent a wallet owner from independently using the public contract outside the site.

## 10. Updating from the Node backend
Use the same SQLite DB_PATH with the Python service. Startup adds columns/indexes and an audit table without deleting existing rows. Original passwords and sessions remain compatible. Back up a real database before upgrading. Audit events begin with the new implementation; they do not invent historical sign-in records.

## 11. Recovering a confirmed transaction missing from history
A MetaMask confirmation does not by itself create a database history row. Version 2.1 saves submitted hashes in this browser and retries the server receipt import when confirmations lag. Refresh or sign in again with the same linked wallet to retry a saved hash. For older transactions, paste the hash into Import. Feedback appears immediately beside history. Do not deposit again to create a missing log entry.

An Administrator can also import a confirmed receipt for a customer's already-linked wallet; the transaction is credited to that customer using the verified event, not the admin. Auditors cannot import. Use Check Sepolia connection beside history to diagnose the backend RPC and contract configuration. No API key is displayed.
