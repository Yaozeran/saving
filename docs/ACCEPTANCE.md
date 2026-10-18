# Acceptance checklist

Automated commands are documented in README. Complete these manual checks on the deployed service; they are not claimed as performed by generating this checklist.

- Register regular and invited admin accounts; reject incorrect credentials and invitation code.
- Connect MetaMask; switch from a different chain to Sepolia and sign a wallet challenge. Reject duplicate wallet linking.
- Admin connects the deploying owner wallet, funds reserve, and sees a confirmed funding event.
- User deposits Sepolia ETH, sees principal and a transaction explorer link, reloads and signs in again; persisted history remains.
- User withdraws part/all principal, and claims nonzero interest after sufficient time; verify wallet receipts and reserve accounting. Small interest claims can cost more gas than the payout.
- Owner funding is rejected by the contract for a non-owner wallet.
- With an empty reserve, principal withdrawal still succeeds and an interest claim reverts.
- Close the browser after submitting; recover the confirmed receipt using its hash. Import twice and verify no duplicate rows.
- A user cannot view another account's history. Admin sees all recorded journal entries.
- Test account/chain switching, rejected wallet prompts, insufficient funds and unavailable RPC feedback.
- Restart/redeploy Render; existing accounts and journal persist on the disk.
- Check desktop/mobile layout, keyboard access and status feedback.
- Record contract address, deployment hash, Render URL and screenshots after live verification for submission evidence.
