// scripts/start-all.js
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import process from "node:process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// project root (folder with package.json)
const ROOT_DIR = path.resolve(__dirname, "..");

// launcher.py lives in backend/
const LAUNCHER = path.join(ROOT_DIR, "backend", "launcher.py");

// choose python executable
const PYTHON_CMD =
  process.env.PYTHON_CMD ||
  (process.platform === "win32" ? "python" : "python3");

// env passed to launcher.py -> uvicorn
// PORT = 8000 so it matches your API_BASE_URL
const API_ENV = {
  ...process.env,
  HOST: process.env.HOST || "0.0.0.0",
  PORT: process.env.PORT || "8000",
  APP: process.env.APP || "backend.main:app",
  WORKERS: process.env.WORKERS || "1",
  RELOAD: "0",
  UVICORN_EXTRA: process.env.UVICORN_EXTRA || "",
  PYTHONPATH:
    ROOT_DIR +
    (process.env.PYTHONPATH ? path.delimiter + process.env.PYTHONPATH : ""),
};

function run(cmd, args, name, opts = {}) {
  const child = spawn(cmd, args, {
    stdio: "inherit",
    shell: process.platform === "win32",
    env: opts.env || process.env,
    cwd: opts.cwd || process.cwd(),
  });

  console.log(`[${name}] started (pid ${child.pid})`);

  child.on("close", (code) => {
    console.log(`[${name}] exited with code ${code}`);
    if (name === "UI" && !shuttingDown) {
      console.log("[manager] UI stopped; shutting down API...");
      shutdown().finally(() => process.exit(code ?? 0));
    }
  });

  child.on("error", (err) => {
    console.error(`[${name}] failed to start:`, err);
    if (!shuttingDown) {
      shutdown().finally(() => process.exit(1));
    }
  });

  return child;
}

let apiProc = null;
let uiProc = null;
let shuttingDown = false;

function startAll() {
  console.log("[manager] starting API via launcher.py ...");
  apiProc = run(PYTHON_CMD, [LAUNCHER, "start"], "API", {
    env: API_ENV,
    cwd: ROOT_DIR,
  });

  console.log("[manager] starting UI (npm run dev)...");
  const npmCmd = process.platform === "win32" ? "npm.cmd" : "npm";
  uiProc = run(npmCmd, ["run", "dev"], "UI", { cwd: ROOT_DIR });
}

async function stopAPI() {
  return new Promise((resolve) => {
    console.log("[manager] stopping API via launcher.py ...");
    const stopper = spawn(PYTHON_CMD, [LAUNCHER, "stop"], {
      stdio: "inherit",
      shell: process.platform === "win32",
      env: API_ENV,
    });
    stopper.on("close", () => resolve());
    stopper.on("error", () => resolve());
  });
}

async function shutdown() {
  if (shuttingDown) return;
  shuttingDown = true;

  await stopAPI();

  try {
    if (uiProc && !uiProc.killed) {
      uiProc.kill("SIGINT");
      setTimeout(() => {
        if (!uiProc.killed) uiProc.kill("SIGTERM");
      }, 500);
    }
  } catch {}

  try {
    if (apiProc && !apiProc.killed) {
      apiProc.kill("SIGINT");
      setTimeout(() => {
        if (!apiProc.killed) apiProc.kill("SIGTERM");
      }, 500);
    }
  } catch {}
}

process.on("SIGINT", () => {
  console.log("\n[manager] SIGINT");
  shutdown().finally(() => process.exit(0));
});
process.on("SIGTERM", () => {
  console.log("\n[manager] SIGTERM");
  shutdown().finally(() => process.exit(0));
});

startAll();
