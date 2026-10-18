"""Real browser/API/local-EVM workflow; simulated wallet, NOT live MetaMask/Sepolia.
Requires: backend/.venv, npm ci in web+contract, pip install playwright,
          python -m playwright install chromium, and an existing web build.
Run with the Python interpreter that has Playwright installed.
"""

from pathlib import Path
import json, os, socket, subprocess, tempfile, time, urllib.request
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "deliverables/evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)
RPC = "http://127.0.0.1:18545"
ORIGIN = "http://127.0.0.1:4173"


def rpc(method, params=None):
    req = urllib.request.Request(
        RPC,
        data=json.dumps(
            {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    data = json.load(urllib.request.urlopen(req, timeout=15))
    if "error" in data:
        raise RuntimeError(data["error"]["message"])
    return data["result"]


def wait_url(url):
    for _ in range(100):
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                if r.status == 200:
                    return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError("Service not ready: " + url)


def free_port(port):
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", port))
        except OSError:
            raise RuntimeError(
                f"Port {port} already in use; leave the existing process untouched and choose another time to run the smoke test."
            ) from None


for port in (4000, 4173, 18545):
    free_port(port)
processes = []
checks = []
with tempfile.TemporaryDirectory(prefix="saving-smoke-") as tmp:
    log = open(Path(tmp) / "services.log", "w")
    try:

        def spawn(cmd, cwd, env=None):
            p = subprocess.Popen(
                cmd, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT
            )
            processes.append(p)
            return p

        spawn(
            [
                "node",
                str(ROOT / "contract/node_modules/ganache/dist/node/cli.js"),
                "--server.port",
                "18545",
                "--chain.chainId",
                "11155111",
                "--miner.blockTime",
                "1",
                "--logging.quiet",
            ],
            ROOT,
        )
        for _ in range(100):
            try:
                rpc("eth_chainId")
                break
            except Exception:
                time.sleep(0.1)
        deploy = """import {JsonRpcProvider,ContractFactory,parseEther} from "ethers";import {compile} from "./deploy.mjs";
const p=new JsonRpcProvider("http://127.0.0.1:18545");p.pollingInterval=100;const owner=await p.getSigner(0),customer=await p.getSigner(1),a=compile();
const c=await new ContractFactory(a.abi,a.evm.bytecode.object,owner).deploy(500);await c.waitForDeployment();
await(await c.fund({value:parseEther("0.2")})).wait();await(await c.connect(customer).deposit({value:parseEther("1")})).wait();
console.log(JSON.stringify({contract:await c.getAddress(),customer:await customer.getAddress(),owner:await owner.getAddress()}));"""
        config = json.loads(
            subprocess.check_output(
                ["node", "--input-type=module", "-e", deploy],
                cwd=ROOT / "contract",
                text=True,
            ).strip()
        )
        rpc("evm_increaseTime", [365 * 86400])
        rpc("evm_mine")
        env = {
            **os.environ,
            "DB_PATH": str(Path(tmp) / "smoke.sqlite"),
            "SEPOLIA_RPC_URL": RPC,
            "CONTRACT_ADDRESS": config["contract"],
            "ADMIN_REGISTRATION_CODE": "local-smoke-admin",
            "AUDITOR_REGISTRATION_CODE": "local-smoke-auditor",
            "APP_ENV": "development",
            "PUBLIC_ORIGIN": ORIGIN,
        }
        spawn(
            [
                str(ROOT / "backend/.venv/bin/python"),
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "4000",
                "--no-proxy-headers",
            ],
            ROOT / "backend",
            env,
        )
        wait_url("http://127.0.0.1:4000/api/health")
        spawn(
            [
                "node",
                str(ROOT / "web/node_modules/next/dist/bin/next"),
                "start",
                "--hostname",
                "127.0.0.1",
                "--port",
                "4173",
            ],
            ROOT / "web",
            env,
        )
        wait_url(ORIGIN)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(viewport={"width": 1440, "height": 1100})
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))

            def wallet_request(payload):
                method, params = payload["method"], payload.get("params", [])
                if method in ("eth_requestAccounts", "eth_accounts"):
                    return [config["customer"]]
                if method == "personal_sign":
                    return rpc("eth_sign", [config["customer"], params[0]])
                return rpc(method, params)

            page.expose_function("_savingWalletRpc", wallet_request)
            page.add_init_script(
                "window.ethereum={request:args=>window._savingWalletRpc(args),on:()=>{},removeListener:()=>{}}"
            )
            page.goto(ORIGIN)
            page.get_by_role("button", name="Create an account", exact=True).click()
            page.get_by_label("Email address").fill("customer@example.test")
            page.get_by_label("Password", exact=True).fill(
                "local browser test password 123"
            )
            page.get_by_role("button", name="Create account →", exact=True).click()
            expect(page.locator(".account-bar")).to_contain_text(
                "customer@example.test"
            )
            checks.append(
                "customer registration through Next proxy with browser Origin"
            )
            page.get_by_role("button", name="Connect MetaMask").click()
            expect(page.get_by_role("status")).to_contain_text(
                "Wallet verified", timeout=20000
            )
            checks.append("simulated wallet challenge signature verified by Python")
            page.get_by_label("ETH amount").fill("0.01")
            for button, action in [
                ("Preview deposit", "deposit"),
                ("Preview withdrawal", "withdraw"),
                ("Preview interest claim", "claim"),
            ]:
                page.get_by_role("button", name=button, exact=False).click()
                expect(
                    page.get_by_role(
                        "heading", name=action.capitalize() + " ·", exact=False
                    )
                ).to_be_visible(timeout=20000)
                expect(
                    page.get_by_text("Maximum network fee", exact=True)
                ).to_be_visible()
                page.get_by_role("button", name="Confirm in MetaMask").click()
                expect(page.get_by_role("status")).to_contain_text(
                    "Transaction confirmed and recorded", timeout=45000
                )
                checks.append(
                    f"{action}: fee preview, local EVM execution, two confirmations and verified journal import"
                )
            expect(page.locator(".pagination")).to_contain_text("3 recorded events")
            page.get_by_role("button", name="Interest paid", exact=True).click()
            page.get_by_text("View accessible data table", exact=True).click()
            expect(page.locator(".chart-details tbody tr")).to_have_count(14)
            page.get_by_text("View accessible data table", exact=True).click()
            page.get_by_label("Filter event type").select_option("Deposited")
            expect(page.locator(".pagination")).to_contain_text("1 recorded event")
            csv_response = context.request.get(ORIGIN + "/api/transactions/export")
            assert csv_response.status == 200 and "InterestPaid" in csv_response.text()
            checks.append("chart table, event filter and authenticated CSV")
            page.get_by_label("Filter event type").select_option("")
            expect(page.locator(".pagination")).to_contain_text("3 recorded events")
            page.screenshot(
                path=str(EVIDENCE / "dashboard-local-desktop.png"), full_page=True
            )
            page.set_viewport_size({"width": 390, "height": 844})
            page.screenshot(
                path=str(EVIDENCE / "dashboard-local-mobile.png"), full_page=True
            )
            assert page.evaluate(
                "document.documentElement.scrollWidth<=window.innerWidth"
            ), "Mobile layout overflows viewport"
            checks.append(
                "desktop/mobile rendering; no document-width overflow at 390px"
            )
            page.get_by_role("button", name="Sign out", exact=True).click()
            page.get_by_role("button", name="Create an account", exact=True).click()
            page.get_by_label("Email address").fill("auditor@example.test")
            page.get_by_label("Password", exact=True).fill(
                "local browser test password 123"
            )
            page.get_by_label("Account role").select_option("auditor")
            page.get_by_label("Auditor invitation code").fill("local-smoke-auditor")
            page.get_by_role("button", name="Create account →", exact=True).click()
            expect(page.get_by_text("Auditor workspace", exact=False)).to_be_visible()
            expect(
                page.get_by_role("button", name="Preview deposit", exact=False)
            ).to_be_disabled()
            expect(page.locator(".pagination")).to_contain_text("3 recorded events")
            expect(
                page.get_by_role("heading", name="Account audit trail", exact=True)
            ).to_be_visible()
            checks.append(
                "auditor registration, shared journal, disabled financial controls and audit trail"
            )
            assert not errors, errors
            browser.close()
        (EVIDENCE / "browser-smoke.json").write_text(
            json.dumps(
                {
                    "status": "pass",
                    "environment": "Chromium + Python API + isolated Ganache chain, simulated EIP-1193 wallet; not real MetaMask or public Sepolia",
                    "checks": checks,
                },
                indent=2,
            )
            + "\n"
        )
        print(json.dumps({"status": "pass", "checks": checks}, indent=2))
    finally:
        for p in reversed(processes):
            p.terminate()
        for p in reversed(processes):
            try:
                p.wait(timeout=8)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait()
        log.close()
