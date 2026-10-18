"""Capture a real container build and proxied Python session smoke test."""

from pathlib import Path
import subprocess, json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables/evidence"
OUT.mkdir(parents=True, exist_ok=True)
smoke = """import {spawn} from "node:child_process";
const child=spawn(process.execPath,["/app/start.mjs"],{stdio:"inherit"});
try {
 let ready=false;
 for(let i=0;i<80;i++){
  await new Promise(r=>setTimeout(r,200));
  try{const r=await fetch("http://127.0.0.1:10000/api/health");if(r.ok&&(await r.json()).service==="saving-python"){ready=true;break;}}catch{}
 }
 if(!ready)throw Error("Python API health failed");
 const r=await fetch("http://127.0.0.1:10000/api/register",{method:"POST",headers:{"Content-Type":"application/json",Origin:"http://127.0.0.1:10000"},body:JSON.stringify({email:"container@example.test",password:"local smoke password 123"})});
 if(!r.ok)throw Error(await r.text());
 const headers={cookie:r.headers.get("set-cookie").split(";")[0]};
 const profile=await fetch("http://127.0.0.1:10000/api/me",{headers});if(!profile.ok)throw Error("Session failed");
 const analytics=await fetch("http://127.0.0.1:10000/api/analytics",{headers});if(!analytics.ok||(await analytics.json()).days.length!==14)throw Error("Analytics failed");
 console.log("Python container smoke passed: health, proxy Origin check, account session and 14-day analytics");
}finally{child.kill("SIGTERM");}
"""
checks = []
for name, cmd in [
    ("docker-build", ["docker", "build", "-t", "saving-python-local", "."]),
    (
        "docker-smoke",
        [
            "docker",
            "run",
            "--rm",
            "-e",
            "APP_ENV=development",
            "saving-python-local",
            "node",
            "--input-type=module",
            "-e",
            smoke,
        ],
    ),
]:
    print("Running", name, flush=True)
    p = subprocess.run(
        cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=300,
    )
    (OUT / (name + ".log")).write_text(p.stdout)
    checks.append({"check": name, "exitCode": p.returncode, "log": name + ".log"})
    if p.returncode:
        break
(OUT / "docker-checks.json").write_text(json.dumps(checks, indent=2) + "\n")
print(json.dumps(checks, indent=2))
raise SystemExit(int(any(c["exitCode"] for c in checks)))
