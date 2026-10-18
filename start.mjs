import { spawn } from "node:child_process";
const api = spawn(
  "python",
  [
    "-m",
    "uvicorn",
    "main:app",
    "--host",
    "127.0.0.1",
    "--port",
    process.env.API_PORT || "4000",
    "--no-proxy-headers",
  ],
  { stdio: "inherit", cwd: "/app/backend" },
);
const web = spawn(process.execPath, ["/app/web/server.js"], {
  stdio: "inherit",
  cwd: "/app/web",
});
let stopping = false;
function stop(code = 0) {
  if (stopping) return;
  stopping = true;
  api.kill("SIGTERM");
  web.kill("SIGTERM");
  setTimeout(() => process.exit(code), 1000);
}
for (const child of [api, web]) {
  child.on("error", () => stop(1));
  child.on("exit", (code) => stop(code || 1));
}
process.on("SIGTERM", () => stop());
process.on("SIGINT", () => stop());
