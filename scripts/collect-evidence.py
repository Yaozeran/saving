"""Run real checks, preserving output and return codes; never reads environment files."""

from pathlib import Path
import subprocess, json, datetime, platform, sys

root = Path(__file__).resolve().parents[1]
out = root / "deliverables/evidence"
out.mkdir(parents=True, exist_ok=True)
backend_python = root / "backend/.venv/bin/python"
checks = [
    (
        "backend-tests",
        "backend",
        [
            str(backend_python) if backend_python.exists() else sys.executable,
            "-m",
            "pytest",
            "test_api.py",
            "-q",
        ],
    ),
    ("contract-tests", "contract", ["npm", "test"]),
    ("contract-compile", "contract", ["npm", "run", "compile"]),
    ("gas-benchmark", "contract", ["npm", "run", "benchmark"]),
    ("web-tests", "web", ["npm", "test"]),
    ("web-lint", "web", ["npm", "run", "lint"]),
    ("web-build", "web", ["npm", "run", "build"]),
]
results = []
for name, cwd, cmd in checks:
    print("Running", name, flush=True)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        p = subprocess.run(
            cmd,
            cwd=root / cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=180,
        )
        code, output = p.returncode, p.stdout
    except subprocess.TimeoutExpired as e:
        code, output = 124, str(e)
    (out / (name + ".log")).write_text(output)
    results.append(
        {
            "check": name,
            "command": " ".join(cmd),
            "cwd": cwd,
            "startedUtc": started,
            "exitCode": code,
            "log": name + ".log",
        }
    )
(out / "checks.json").write_text(
    json.dumps({"host": platform.platform(), "checks": results}, indent=2) + "\n"
)
print(json.dumps(results, indent=2))
raise SystemExit(int(any(r["exitCode"] for r in results)))
