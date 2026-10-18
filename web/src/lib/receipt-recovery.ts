// Save only public transaction hashes, scoped to the linked wallet and contract.
type Store = Pick<Storage, "getItem" | "setItem">;
const validHash = /^0x[0-9a-fA-F]{64}$/;
const key = (contract: string, wallet: string) =>
  `saving:sepolia:receipts:${contract.toLowerCase()}:${wallet.toLowerCase()}`;
export function pendingReceipts(
  store: Store,
  contract: string,
  wallet: string,
): string[] {
  try {
    const data: unknown = JSON.parse(
      store.getItem(key(contract, wallet)) || "[]",
    );
    return Array.isArray(data)
      ? [
          ...new Set(
            data.filter(
              (h): h is string => typeof h === "string" && validHash.test(h),
            ),
          ),
        ].slice(-20)
      : [];
  } catch {
    return [];
  }
}
export function saveReceipt(
  store: Store,
  contract: string,
  wallet: string,
  hash: string,
) {
  if (!validHash.test(hash)) return;
  try {
    store.setItem(
      key(contract, wallet),
      JSON.stringify(
        [...new Set([...pendingReceipts(store, contract, wallet), hash])].slice(
          -20,
        ),
      ),
    );
  } catch {
    /* Private mode/quota: the caller still displays the hash. */
  }
}
export function removeReceipt(
  store: Store,
  contract: string,
  wallet: string,
  hash: string,
) {
  try {
    store.setItem(
      key(contract, wallet),
      JSON.stringify(
        pendingReceipts(store, contract, wallet).filter((h) => h !== hash),
      ),
    );
  } catch {
    /* Keep the confirmed transaction result even if storage is unavailable. */
  }
}
export async function importWithRetry(
  hash: string,
  post: (hash: string) => Promise<unknown>,
  attempts = 12,
  delayMs = 3000,
  sleep = (ms: number) =>
    new Promise<void>((resolve) => setTimeout(resolve, ms)),
) {
  for (let attempt = 0; attempt < attempts; attempt++) {
    try {
      return await post(hash);
    } catch (error) {
      // Only pending/confirmation/reorganisation conflicts are transient here.
      // Configuration, authentication and wrong-wallet errors need user action.
      if (
        (error as { status?: number })?.status !== 409 ||
        attempt === attempts - 1
      )
        throw error;
      await sleep(delayMs);
    }
  }
}

// Accrued-interest storage can change between estimation and the next block.
export function bufferedGas(estimate: bigint): bigint {
  return (estimate * 120n + 99n) / 100n + 30000n;
}
