"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  BrowserProvider,
  Contract,
  formatEther,
  parseEther,
  type Eip1193Provider,
} from "ethers";
import ActivityChart, { type Analytics } from "@/components/activity-chart";
type User = { email: string; role: string; wallet: string | null };
type Balance = {
  principal: string;
  interest: string;
  rateBps: string;
  reserve: string;
  owner: string;
  totalPrincipal: string;
  block: number;
};
type Tx = {
  hash: string;
  log_index: number;
  kind: string;
  amount: string;
  created: string;
  block_time?: string | null;
  wallet?: string;
  email?: string;
};
type Audit = {
  id: number;
  user_id: number;
  action: string;
  detail: string;
  created: string;
};
type Quote = {
  action: string;
  amount: string;
  gas: string;
  gasLimit: string;
  fee: string;
  maxFee: string;
  tip: string | null;
  value: string;
  wallet: string;
  contract: string;
  expires: number;
};
const abi = [
  "function deposit() payable",
  "function withdraw(uint256)",
  "function claim()",
  "function fund() payable",
];
async function api(path: string, body?: object) {
  const r = await fetch("/api/" + path, {
    method: body ? "POST" : "GET",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await r
    .json()
    .catch(() => ({
      error: "The service did not respond. Try again shortly.",
    }));
  if (!r.ok) throw Error(data.error);
  return data;
}
const eth = (v: string = "0") =>
  Number(formatEther(v)).toLocaleString(undefined, {
    maximumFractionDigits: 8,
  });
export default function Home() {
  const [user, setUser] = useState<User | null>(null),
    [balance, setBalance] = useState<Balance | null>(null),
    [transactions, setTransactions] = useState<Tx[]>([]),
    [address, setAddress] = useState("");
  const [mode, setMode] = useState("login"),
    [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [adminCode, setAdminCode] = useState(""),
    [registerRole, setRegisterRole] = useState("user"),
    [amount, setAmount] = useState("0.01"),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [ready, setReady] = useState(false),
    [pending, setPending] = useState("");
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [audit, setAudit] = useState<Audit[]>([]);
  const [page, setPage] = useState(1),
    [total, setTotal] = useState(0),
    [kind, setKind] = useState("");
  const [quote, setQuote] = useState<Quote | null>(null);
  const privileged = user?.role === "admin" || user?.role === "auditor";
  const readOnly = user?.role === "auditor";
  const loadHistory = useCallback(async (nextPage = 1, nextKind = "") => {
    const data = await api(
      `activity?page=${nextPage}&pageSize=10&kind=${encodeURIComponent(nextKind)}`,
    );
    setTransactions(data.items);
    setTotal(data.total);
    setPage(data.page);
    setKind(nextKind);
  }, []);
  const refresh = useCallback(async () => {
    const config = await api("config");
    setAddress(config.contract || "");
    let me;
    try {
      me = await api("me");
    } catch {
      setUser(null);
      setBalance(null);
      setTransactions([]);
      setAnalytics(null);
      setAudit([]);
      setQuote(null);
      setReady(true);
      return;
    }
    setUser(me);
    await loadHistory();
    setAnalytics(await api("analytics"));
    if (me.role === "admin" || me.role === "auditor")
      setAudit((await api("audit")).items);
    else setAudit([]);
    try {
      setBalance(await api("balance"));
    } catch (e) {
      setBalance(null);
      setNotice((e as Error).message);
    }
    setReady(true);
  }, [loadHistory]);
  useEffect(() => {
    void Promise.resolve()
      .then(refresh)
      .catch((e) => {
        setNotice(e.message);
        setReady(true);
      });
  }, [refresh]);
  useEffect(() => {
    const ethereum = (
      window as unknown as {
        ethereum?: Eip1193Provider & {
          on?: (event: string, fn: () => void) => void;
          removeListener?: (event: string, fn: () => void) => void;
        };
      }
    ).ethereum;
    const changed = () => {
      setQuote(null);
      setNotice(
        "Wallet or network changed. Select your linked wallet on Sepolia before continuing.",
      );
    };
    ethereum?.on?.("accountsChanged", changed);
    ethereum?.on?.("chainChanged", changed);
    return () => {
      ethereum?.removeListener?.("accountsChanged", changed);
      ethereum?.removeListener?.("chainChanged", changed);
    };
  }, []);
  async function run(fn: () => Promise<void>) {
    setBusy(true);
    setNotice("");
    try {
      await fn();
    } catch (e) {
      setNotice((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function wallet() {
    const ethereum = (window as unknown as { ethereum?: Eip1193Provider })
      .ethereum;
    if (!ethereum) throw Error("Install MetaMask to connect your wallet.");
    const provider = new BrowserProvider(ethereum);
    await provider.send("eth_requestAccounts", []);
    if ((await provider.getNetwork()).chainId !== 11155111n) {
      await provider.send("wallet_switchEthereumChain", [
        { chainId: "0xaa36a7" },
      ]);
    }
    return new BrowserProvider(ethereum);
  }
  async function connect() {
    const p = await wallet();
    const signer = await p.getSigner();
    const { message } = await api("challenge", {});
    await api("wallet", { signature: await signer.signMessage(message) });
    await refresh();
    setNotice("Wallet verified and linked to your account.");
  }
  async function prepare(action: string) {
    setQuote(null);
    if (readOnly) throw Error("Auditor access is read-only.");
    if (!user?.wallet) throw Error("Connect and verify your wallet first.");
    if (!address) throw Error("The vault contract has not been configured.");
    const p = await wallet();
    const signer = await p.getSigner();
    if ((await signer.getAddress()).toLowerCase() !== user.wallet.toLowerCase())
      throw Error("Select your linked account in MetaMask.");
    if (
      action === "fund" &&
      (user.role !== "admin" ||
        balance?.owner.toLowerCase() !== user.wallet.toLowerCase())
    )
      throw Error(
        "Funding requires the contract owner wallet and an administrator account.",
      );
    let value = 0n;
    if (action !== "claim") {
      try {
        value = parseEther(amount);
      } catch {
        throw Error("Enter a valid ETH amount with at most 18 decimal places.");
      }
      if (value <= 0n) throw Error("Enter a positive ETH amount.");
    }
    const vault = new Contract(address, abi, signer);
    const gas =
      action === "claim"
        ? await vault.claim.estimateGas()
        : action === "withdraw"
          ? await vault.withdraw.estimateGas(value)
          : action === "fund"
            ? await vault.fund.estimateGas({ value })
            : await vault.deposit.estimateGas({ value });
    const fees = await p.getFeeData();
    const maxFee = fees.maxFeePerGas ?? fees.gasPrice;
    if (maxFee === null)
      throw Error("Fee data is unavailable. Try estimating again.");
    const gasLimit = (gas * 120n + 99n) / 100n;
    const fee = gasLimit * maxFee;
    const spend =
      (action === "deposit" || action === "fund" ? value : 0n) + fee;
    if ((await p.getBalance(user.wallet)) < spend)
      throw Error(
        "Insufficient wallet balance for the amount and maximum network fee.",
      );
    setQuote({
      action,
      amount:
        action === "claim"
          ? "All accrued interest"
          : formatEther(value) + " ETH",
      value: String(value),
      gas: String(gas),
      gasLimit: String(gasLimit),
      fee: String(fee),
      maxFee: String(maxFee),
      tip:
        fees.maxFeePerGas !== null && fees.maxPriorityFeePerGas !== null
          ? String(fees.maxPriorityFeePerGas)
          : null,
      wallet: user.wallet,
      contract: address,
      expires: Date.now() + 60000,
    });
  }
  async function confirmTransaction() {
    const q = quote;
    if (!q) return;
    if (Date.now() > q.expires) {
      setQuote(null);
      throw Error("Fee preview expired. Estimate again before signing.");
    }
    if (readOnly || user?.wallet !== q.wallet || address !== q.contract) {
      setQuote(null);
      throw Error("Account changed. Estimate again.");
    }
    const p = await wallet();
    const signer = await p.getSigner();
    if (
      (await signer.getAddress()).toLowerCase() !== q.wallet.toLowerCase() ||
      (await p.getNetwork()).chainId !== 11155111n
    ) {
      setQuote(null);
      throw Error("Wallet or network changed. Estimate again.");
    }
    // Check again after wallet prompts, which may have stayed open for a while.
    if (Date.now() > q.expires) {
      setQuote(null);
      throw Error("Fee preview expired. Estimate again.");
    }
    const overrides =
      q.tip !== null
        ? {
            gasLimit: BigInt(q.gasLimit),
            maxFeePerGas: BigInt(q.maxFee),
            maxPriorityFeePerGas: BigInt(q.tip),
          }
        : { gasLimit: BigInt(q.gasLimit), gasPrice: BigInt(q.maxFee) };
    const vault = new Contract(q.contract, abi, signer);
    setQuote(null);
    const tx =
      q.action === "claim"
        ? await vault.claim(overrides)
        : q.action === "withdraw"
          ? await vault.withdraw(BigInt(q.value), overrides)
          : q.action === "fund"
            ? await vault.fund({ ...overrides, value: BigInt(q.value) })
            : await vault.deposit({ ...overrides, value: BigInt(q.value) });
    setPending(tx.hash);
    setNotice("Transaction submitted. Waiting for two confirmations…");
    await tx.wait(2);
    await api("transactions", { hash: tx.hash });
    setPending("");
    await refresh();
    setNotice("Transaction confirmed and recorded.");
  }
  return (
    <div className="shell">
      <aside>
        <Link className="brand" href="/">
          ◈{" "}
          <span>
            saving<span className="dot">.</span>
          </span>
        </Link>
        <div className="network">
          <i /> Sepolia testnet
        </div>
        <nav>
          <a className="active" href="#overview">
            ▦ &nbsp; Overview
          </a>
          <a href="#activity">↗ &nbsp; Transactions</a>
          <a href="#about">ⓘ &nbsp; How it works</a>
        </nav>
        <div className="side-bottom">
          <div className="mini-mark">◇</div>
          <strong>Your keys. Your savings.</strong>
          <p>Every deposit and payout is verifiable on Ethereum.</p>
          <small>Built by Zeran Yao</small>
        </div>
      </aside>
      <main>
        <header>
          <span>
            Workspace / <b>Overview</b>
          </span>
          <span className="pill">● &nbsp; Testnet only · no real value</span>
        </header>
        <section className="intro" id="overview">
          <div>
            <div className="eyebrow">A LITTLE TODAY. MORE TOMORROW.</div>
            <h1>Make room for growth.</h1>
            <p>Save Sepolia ETH and watch your interest grow, on-chain.</p>
          </div>
          {user && (
            <button
              className="secondary"
              disabled={busy}
              onClick={() => run(connect)}
            >
              {user.wallet
                ? user.wallet.slice(0, 6) + "…" + user.wallet.slice(-4)
                : "Connect MetaMask"}{" "}
              ↗
            </button>
          )}
        </section>
        {notice && (
          <div className="notice" role="status">
            {notice}
          </div>
        )}
        {!ready ? (
          <p>Loading your workspace…</p>
        ) : !user ? (
          <section className="auth">
            <div className="auth-copy">
              <div className="orb">◈</div>
              <h2>
                Your next chapter
                <br />
                starts with a deposit.
              </h2>
              <p>
                A simple savings experience. A transparent rate.
                <br />A wallet that stays in your hands.
              </p>
              <div className="tags">
                <span>MetaMask connected</span>
                <span>On-chain interest</span>
              </div>
            </div>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void run(async () => {
                  await api(mode === "login" ? "login" : "register", {
                    email,
                    password,
                    ...(mode === "register" && registerRole === "admin"
                      ? { adminCode }
                      : {}),
                    ...(mode === "register" && registerRole === "auditor"
                      ? { auditorCode: adminCode }
                      : {}),
                  });
                  setPassword("");
                  await refresh();
                });
              }}
            >
              <div className="eyebrow">WELCOME TO SAVING</div>
              <h2>
                {mode === "login" ? "Welcome back." : "Create your account."}
              </h2>
              <p>
                {mode === "login"
                  ? "Sign in to your savings workspace."
                  : "Start your Sepolia savings journey."}
              </p>
              <label>
                Email address
                <input
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </label>
              <label>
                Password
                <input
                  type="password"
                  autoComplete={
                    mode === "login" ? "current-password" : "new-password"
                  }
                  minLength={12}
                  maxLength={128}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </label>
              {mode === "register" && (
                <>
                  <label>
                    Account role
                    <select
                      value={registerRole}
                      onChange={(e) => {
                        setRegisterRole(e.target.value);
                        setAdminCode("");
                      }}
                    >
                      <option value="user">Customer</option>
                      <option value="admin">
                        Administrator · invitation required
                      </option>
                      <option value="auditor">
                        Auditor · invitation required
                      </option>
                    </select>
                  </label>
                  {registerRole !== "user" && (
                    <label>
                      {registerRole === "admin" ? "Administrator" : "Auditor"}{" "}
                      invitation code
                      <input
                        type="password"
                        required
                        value={adminCode}
                        onChange={(e) => setAdminCode(e.target.value)}
                      />
                    </label>
                  )}
                </>
              )}
              <button disabled={busy}>
                {busy
                  ? "Please wait…"
                  : mode === "login"
                    ? "Sign in →"
                    : "Create account →"}
              </button>
              <p className="switch">
                {mode === "login" ? "New here?" : "Already registered?"}{" "}
                <button
                  type="button"
                  className="text-button"
                  onClick={() =>
                    setMode(mode === "login" ? "register" : "login")
                  }
                >
                  {mode === "login" ? "Create an account" : "Sign in"}
                </button>
              </p>
            </form>
          </section>
        ) : (
          <>
            <div className="account-bar">
              <span>
                {user.email} <span className="pill">{user.role}</span>
              </span>
              <button
                className="text-button"
                disabled={busy}
                onClick={() =>
                  run(async () => {
                    await api("logout", {});
                    setMode("login");
                    setRegisterRole("user");
                    setAdminCode("");
                    setQuote(null);
                    setBalance(null);
                    await refresh();
                  })
                }
              >
                Sign out
              </button>
            </div>
            <section className="stats">
              <article className="principal">
                <div>
                  Total deposited <span>↗</span>
                </div>
                <h2>
                  {eth(balance?.principal)} <small>ETH</small>
                </h2>
                <p>Your principal, always yours to withdraw</p>
              </article>
              <article>
                <div>
                  Interest earned <span>✧</span>
                </div>
                <h2>
                  {eth(balance?.interest)} <small>ETH</small>
                </h2>
                <p>Accrued, unclaimed simple interest</p>
              </article>
              <article>
                <div>
                  Annual interest rate <span>↗</span>
                </div>
                <h2>
                  {balance ? Number(balance.rateBps) / 100 : "—"}
                  <small>% APR</small>
                </h2>
                <p>Fixed by the deployed smart contract</p>
              </article>
            </section>
            <ActivityChart data={analytics} />
            {readOnly && (
              <div className="read-only-note">
                Auditor workspace · inspect activity and export evidence.
                Financial actions are disabled.
              </div>
            )}
            <section className="workspace">
              <article className="panel">
                <div className="eyebrow">GROW AT YOUR OWN PACE</div>
                <h2>Put your ETH to work.</h2>
                <p>Deposit or withdraw directly from your wallet.</p>
                <label>
                  Amount <span>Sepolia ETH</span>
                  <div className="amount">
                    <input
                      aria-label="ETH amount"
                      value={amount}
                      onChange={(e) => {
                        setAmount(e.target.value);
                        setQuote(null);
                      }}
                      inputMode="decimal"
                    />
                    <b>ETH</b>
                  </div>
                </label>
                <div className="actions">
                  <button
                    disabled={busy || !balance || readOnly}
                    onClick={() => run(() => prepare("deposit"))}
                  >
                    Preview deposit ↗
                  </button>
                  <button
                    className="secondary"
                    disabled={busy || !balance || readOnly}
                    onClick={() => run(() => prepare("withdraw"))}
                  >
                    Preview withdrawal
                  </button>
                </div>
                <button
                  className="text-button"
                  disabled={busy || !balance || readOnly}
                  onClick={() => run(() => prepare("claim"))}
                >
                  Preview interest claim →
                </button>
              </article>
              <article className="panel reserve">
                <span className="reserve-icon">✧</span>
                <h2>Transparent by design.</h2>
                <p>
                  Interest comes from an administrator-funded reserve. Every
                  payout goes directly to your connected wallet.
                </p>
                <div className="reserve-line">
                  <span>Available interest reserve</span>
                  <strong>{eth(balance?.reserve)} ETH</strong>
                </div>
                {user.role === "admin" && (
                  <button
                    disabled={busy || !balance || readOnly}
                    onClick={() => run(() => prepare("fund"))}
                  >
                    Preview reserve funding ↗
                  </button>
                )}
                <small>
                  Interest claims require sufficient reserve. Principal
                  withdrawals remain available.
                </small>
              </article>
            </section>
            {quote && (
              <section
                className="panel fee-preview"
                aria-labelledby="fee-heading"
              >
                <div className="section-heading">
                  <div>
                    <div className="eyebrow">REVIEW BEFORE YOU SIGN</div>
                    <h2 id="fee-heading">
                      {quote.action.charAt(0).toUpperCase() +
                        quote.action.slice(1)}{" "}
                      · {quote.amount}
                    </h2>
                  </div>
                  <button
                    className="text-button"
                    disabled={busy}
                    onClick={() => setQuote(null)}
                  >
                    Cancel preview
                  </button>
                </div>
                <dl>
                  <div>
                    <dt>Network</dt>
                    <dd>Sepolia (11155111)</dd>
                  </div>
                  <div>
                    <dt>Gas estimate</dt>
                    <dd>{quote.gas} units</dd>
                  </div>
                  <div>
                    <dt>Maximum network fee</dt>
                    <dd>{formatEther(quote.fee)} ETH</dd>
                  </div>
                  <div>
                    <dt>Contract</dt>
                    <dd className="address-value">{quote.contract}</dd>
                  </div>
                </dl>
                <p>
                  Fee cap includes a 20% gas buffer. Actual cost may be lower.
                  Preview expires after 60 seconds; MetaMask asks for your final
                  signature.
                </p>
                <button disabled={busy} onClick={() => run(confirmTransaction)}>
                  Confirm in MetaMask ↗
                </button>
              </section>
            )}
            <section className="panel activity" id="activity">
              <div className="section-heading">
                <div>
                  <h2>Transaction history</h2>
                  <p>
                    {privileged
                      ? "All recorded account activity"
                      : "Your confirmed on-chain activity"}
                  </p>
                </div>
                <button
                  className="secondary"
                  disabled={busy}
                  onClick={() => run(refresh)}
                >
                  Refresh ↻
                </button>
              </div>
              <div className="history-tools">
                <label>
                  Event type
                  <select
                    aria-label="Filter event type"
                    value={kind}
                    disabled={busy}
                    onChange={(e) => run(() => loadHistory(1, e.target.value))}
                  >
                    <option value="">All events</option>
                    <option value="Deposited">Deposits</option>
                    <option value="Withdrawn">Withdrawals</option>
                    <option value="InterestPaid">Interest payouts</option>
                    <option value="Funded">Reserve funding</option>
                  </select>
                </label>
                <a
                  className="export-link"
                  href="/api/transactions/export"
                  download
                >
                  Export CSV ↧
                </a>
              </div>
              {!readOnly && (
                <form
                  className="sync"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void run(async () => {
                      await api("transactions", { hash: pending });
                      setPending("");
                      await refresh();
                      setNotice("Transaction imported.");
                    });
                  }}
                >
                  <input
                    aria-label="Transaction hash"
                    placeholder="Recover a transaction: paste its 0x hash"
                    value={pending}
                    onChange={(e) => setPending(e.target.value)}
                  />
                  <button className="secondary" disabled={busy || !pending}>
                    Import
                  </button>
                </form>
              )}
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Transaction</th>
                      <th>Amount</th>
                      {user.role === "admin" && <th>Account</th>}
                      {privileged && <th>Wallet</th>}
                      <th>Block time (UTC)</th>
                      <th>Recorded (UTC)</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((t) => (
                      <tr key={t.hash + t.log_index}>
                        <td>
                          <a
                            href={`https://sepolia.etherscan.io/tx/${t.hash}`}
                            target="_blank"
                            rel="noreferrer"
                          >
                            {t.kind} ↗
                          </a>
                        </td>
                        <td>{eth(t.amount)} ETH</td>
                        {user.role === "admin" && <td>{t.email}</td>}
                        {privileged && (
                          <td className="wallet-cell" title={t.wallet}>
                            {t.wallet
                              ? t.wallet.slice(0, 6) + "…" + t.wallet.slice(-4)
                              : "—"}
                          </td>
                        )}
                        <td>{t.block_time || "Legacy record"}</td>
                        <td>{t.created}</td>
                        <td>
                          <span className="confirmed">Confirmed</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!transactions.length && (
                  <div className="empty">
                    ↗<h3>A fresh start.</h3>
                    <p>
                      Your confirmed deposits, withdrawals and interest payouts
                      will appear here.
                    </p>
                  </div>
                )}
              </div>
              <div className="pagination">
                <span>
                  {total} recorded event{total === 1 ? "" : "s"} · page {page}{" "}
                  of {Math.max(1, Math.ceil(total / 10))}
                </span>
                <div>
                  <button
                    className="secondary"
                    disabled={busy || page <= 1}
                    onClick={() => run(() => loadHistory(page - 1, kind))}
                  >
                    Previous
                  </button>
                  <button
                    className="secondary"
                    disabled={busy || page * 10 >= total}
                    onClick={() => run(() => loadHistory(page + 1, kind))}
                  >
                    Next
                  </button>
                </div>
              </div>
            </section>
            {privileged && (
              <section className="panel audit-panel">
                <div className="section-heading">
                  <div>
                    <h2>Account audit trail</h2>
                    <p>
                      Latest 20 recorded account events · no passwords or
                      signing keys.
                    </p>
                  </div>
                </div>
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Account ID</th>
                        <th>Action</th>
                        <th>Recorded (UTC)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {audit.map((a) => (
                        <tr key={a.id}>
                          <td>#{a.user_id}</td>
                          <td>{a.action.replaceAll("_", " ")}</td>
                          <td>{a.created}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}
          </>
        )}
        <footer id="about">
          <div>
            <strong>Small steps. Visible progress.</strong>
            <p>
              Simple interest accrues with time. Gas fees apply to every
              transaction.
            </p>
          </div>
          {address ? (
            <a
              href={`https://sepolia.etherscan.io/address/${address}`}
              target="_blank"
              rel="noreferrer"
            >
              View smart contract ↗
            </a>
          ) : (
            <span>Contract deployment pending</span>
          )}
        </footer>
      </main>
    </div>
  );
}
