import { test } from "node:test";
import assert from "node:assert/strict";
import ganache from "ganache";
import { BrowserProvider, ContractFactory, parseEther } from "ethers";
import { compile } from "../deploy.mjs";
test("principal protection, interest accounting, owner funding and reserve exhaustion", async () => {
  const chain = ganache.provider({ logging: { quiet: true } });
  const p = new BrowserProvider(chain);
  p.pollingInterval = 20;
  try {
    const owner = await p.getSigner(0),
      user = await p.getSigner(1);
    const a = compile();
    const c = await new ContractFactory(
      a.abi,
      a.evm.bytecode.object,
      owner,
    ).deploy(500);
    await c.waitForDeployment();
    const u = c.connect(user);
    await (await u.deposit({ value: parseEther("1") })).wait();
    assert.equal(await c.totalPrincipal(), parseEther("1"));
    await chain.request({ method: "evm_increaseTime", params: [365 * 86400] });
    await chain.request({ method: "evm_mine", params: [] });
    assert.ok((await c.earned(await user.getAddress())) >= parseEther("0.05"));
    await assert.rejects(u.claim());
    await assert.rejects(u.fund({ value: 1n }));
    await (await c.fund({ value: parseEther("0.2") })).wait();
    await (await u.claim({ gasLimit: 300000 })).wait();
    assert.ok((await c.reserve()) < parseEther("0.16"));
    await (await u.withdraw(parseEther("1"))).wait();
    assert.equal(await c.totalPrincipal(), 0n);
    assert.equal((await c.accounts(await user.getAddress())).principal, 0n);
    await assert.rejects(u.withdraw(1n));
    await assert.rejects(u.deposit({ value: 0n }));
  } finally {
    await chain.disconnect();
  }
});

test("principal can be withdrawn while reserve is empty, preserving earned interest", async () => {
  const chain = ganache.provider({ logging: { quiet: true } });
  const p = new BrowserProvider(chain);
  p.pollingInterval = 20;
  try {
    const signer = await p.getSigner();
    const a = compile();
    const vault = await new ContractFactory(
      a.abi,
      a.evm.bytecode.object,
      signer,
    ).deploy(500);
    await vault.waitForDeployment();
    await (await vault.deposit({ value: parseEther("1") })).wait();
    await chain.request({ method: "evm_increaseTime", params: [365 * 86400] });
    await chain.request({ method: "evm_mine", params: [] });
    assert.equal(await vault.reserve(), 0n);
    await (await vault.withdraw(parseEther("1"))).wait();
    assert.equal(await vault.totalPrincipal(), 0n);
    assert.ok(
      (await vault.earned(await signer.getAddress())) >= parseEther("0.05"),
    );
  } finally {
    await chain.disconnect();
  }
});

test("a top-up earns no retroactive interest and partial withdrawal preserves prior accrual", async () => {
  const chain = ganache.provider({ logging: { quiet: true } });
  const p = new BrowserProvider(chain);
  p.pollingInterval = 20;
  try {
    const signer = await p.getSigner();
    const a = compile();
    const vault = await new ContractFactory(
      a.abi,
      a.evm.bytecode.object,
      signer,
    ).deploy(500);
    await vault.waitForDeployment();
    await (await vault.deposit({ value: parseEther("1") })).wait();
    await chain.request({ method: "evm_increaseTime", params: [365 * 86400] });
    await chain.request({ method: "evm_mine", params: [] });
    await (await vault.deposit({ value: parseEther("1") })).wait();
    const accrued = await vault.earned(await signer.getAddress());
    assert.ok(accrued >= parseEther("0.05") && accrued < parseEther("0.051"));
    await (
      await vault.withdraw(parseEther("0.5"), { gasLimit: 300000 })
    ).wait();
    assert.equal(await vault.totalPrincipal(), parseEther("1.5"));
    assert.ok((await vault.earned(await signer.getAddress())) >= accrued);
  } finally {
    await chain.disconnect();
  }
});
