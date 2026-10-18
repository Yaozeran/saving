import { test } from "node:test";
import assert from "node:assert/strict";
import {
  bufferedGas,
  pendingReceipts,
  saveReceipt,
  removeReceipt,
  importWithRetry,
} from "../src/lib/receipt-recovery.ts";
const hash = "0x" + "ab".repeat(32);
function store() {
  const entries = new Map();
  return {
    getItem: (k) => entries.get(k) ?? null,
    setItem: (k, v) => entries.set(k, v),
  };
}
test("receipt survives reload, remains wallet/contract scoped and is removed only on success", () => {
  const storage = store();
  saveReceipt(storage, "0xVault", "0xWallet", hash);
  saveReceipt(storage, "0xVault", "0xWallet", hash);
  assert.deepEqual(pendingReceipts(storage, "0xvault", "0xwallet"), [hash]);
  assert.deepEqual(pendingReceipts(storage, "0xother", "0xwallet"), []);
  assert.deepEqual(pendingReceipts(storage, "0xvault", "0xother"), []);
  removeReceipt(storage, "0xvault", "0xwallet", hash);
  assert.deepEqual(pendingReceipts(storage, "0xvault", "0xwallet"), []);
});
test("malformed or unavailable storage never breaks transaction handling", () => {
  const bad = {
    getItem: () => "{bad",
    setItem: () => {
      throw Error("quota");
    },
  };
  assert.deepEqual(pendingReceipts(bad, "v", "w"), []);
  saveReceipt(bad, "v", "w", hash);
  removeReceipt(bad, "v", "w", hash);
});
test("backend confirmation lag retries the same receipt and eventually records it", async () => {
  let calls = 0,
    delays = 0;
  const result = await importWithRetry(
    hash,
    async (h) => {
      assert.equal(h, hash);
      if (++calls < 3)
        throw Object.assign(Error("Wait for two confirmations"), {
          status: 409,
        });
      return { ok: true };
    },
    4,
    1,
    async () => {
      delays++;
    },
  );
  assert.equal(calls, 3);
  assert.equal(delays, 2);
  assert.equal(result.ok, true);
});
test("configuration/authentication errors stop immediately and exhausted conflicts stay recoverable", async () => {
  for (const status of [400, 401, 403, 503]) {
    let calls = 0;
    await assert.rejects(
      importWithRetry(
        hash,
        async () => {
          calls++;
          throw Object.assign(Error("action needed"), { status });
        },
        3,
        0,
      ),
    );
    assert.equal(calls, 1);
  }
  let calls = 0;
  await assert.rejects(
    importWithRetry(
      hash,
      async () => {
        calls++;
        throw Object.assign(Error("pending"), { status: 409 });
      },
      3,
      0,
      async () => {},
    ),
  );
  assert.equal(calls, 3);
});

test("gas allowance covers time-dependent interest storage beyond a percentage-only buffer", () => {
  assert.equal(bufferedGas(50000n), 90000n);
  assert.ok(bufferedGas(55195n) >= 55195n + 30000n);
});
