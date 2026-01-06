// ../scripts/start-all.mjs
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import process from "node:process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// __dirname = AutocadPDFconvert\scripts
// ROOT_DIR = AutocadPDFconvert
const ROOT_DIR = path.resolve(__dirname, "..");

// backend/launcher.py (AutocadPDFconvert\backend\launcher.py)
const LAUNCHER = path.join(ROOT_DIR, "backend", "launcher.py");

// frontend = AutocadPDFconvert\dwgplotter
const UI_DIR = path.join(ROOT_DIR, "dwgplotter");

// choose python executable
const PYTHON_CMD =
  process.env.PYTHON_CMD ||
  (process.platform === "win32" ? "python" : "python3");

// env passed to launcher.py -> uvicorn
// PORT = 8000 to match your React API_BASE_URL
const API_ENV = {
  ...process.env,
  HOST: process.env.HOST || "0.0.0.0",
  PORT: process.env.PORT || "8000",
  APP: process.env.APP || "main:app", // <-- your real app module
  WORKERS: process.env.WORKERS || "1",
  RELOAD: "0",
  UVICORN_EXTRA: process.env.UVICORN_EXTRA || "",
  PYTHONPATH:
    ROOT_DIR +
    (process.env.PYTHONPATH ? path.delimiter + process.env.PYTHONPATH : ""),
};

let apiProc = null;
let uiProc = null;
let shuttingDown = false;

function startApi() {
  console.log("[manager] ROOT_DIR =", ROOT_DIR);
  console.log("[manager] LAUNCHER =", LAUNCHER);

  apiProc = spawn(PYTHON_CMD, [LAUNCHER, "start"], {
    stdio: "inherit",
    shell: false,          // ❗ no shell → spaces in path are safe
    cwd: ROOT_DIR,
    env: API_ENV,
  });

  apiProc.on("close", (code) => {
    console.log(`[API] exited with code ${code}`);
  });

  apiProc.on("error", (err) => {
    console.error("[API] failed to start:", err);
  });
}

function startUi() {
  console.log("[manager] UI_DIR =", UI_DIR);

  // Just let the shell run `npm run dev:ui` inside the dwgplotter folder
  uiProc = spawn("npm", ["run", "dev:ui"], {
    stdio: "inherit",
    shell: true,          // ✅ use shell for npm on Windows
    cwd: UI_DIR,          // <- dwgplotter folder
    env: process.env,
  });

  uiProc.on("close", (code) => {
    console.log(`[UI] exited with code ${code}`);
    if (!shuttingDown) {
      console.log("[manager] UI stopped; shutting down API...");
      shutdown().finally(() => process.exit(code ?? 0));
    }
  });

  uiProc.on("error", (err) => {
    console.error("[UI] failed to start:", err);
  });
}

async function stopApi() {
  if (!apiProc || apiProc.killed) return;

  return new Promise((resolve) => {
    console.log("[manager] stopping API via launcher.py ...");
    const stopper = spawn(PYTHON_CMD, [LAUNCHER, "stop"], {
      stdio: "inherit",
      shell: false,
      cwd: ROOT_DIR,
      env: API_ENV,
    });
    stopper.on("close", () => resolve());
    stopper.on("error", () => resolve());
  });
}

async function shutdown() {
  if (shuttingDown) return;
  shuttingDown = true;

  await stopApi();

  try {
    if (uiProc && !uiProc.killed) {
      uiProc.kill("SIGINT");
      setTimeout(() => {
        if (!uiProc.killed) uiProc.kill("SIGTERM");
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

function startAll() {
  startApi();
  startUi();
}

startAll();
