import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import process from "node:process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ROOT_DIR = path.resolve(__dirname, "..");
const LAUNCHER = path.join(ROOT_DIR, "backend", "launcher.py");
const UI_DIR = path.join(ROOT_DIR, "dwgplotter");

const PYTHON_CMD =
  process.env.PYTHON_CMD ||
  (process.platform === "win32"
    ? path.join(ROOT_DIR, "venv311", "Scripts", "python.exe")
    : "python3");

const API_ENV = {
  ...process.env,
  HOST: process.env.HOST || "0.0.0.0",
  PORT: process.env.PORT || "8000",
  APP: process.env.APP || "backend.main:app",
  WORKERS: process.env.WORKERS || "1",
  RELOAD: "0",
  PYTHONPATH:
    ROOT_DIR +
    (process.env.PYTHONPATH ? path.delimiter + process.env.PYTHONPATH : ""),
};

let apiProc = null;
let uiProc = null;
let shuttingDown = false;

function startApi() {
  apiProc = spawn(PYTHON_CMD, [LAUNCHER, "start"], {
    stdio: "inherit",
    shell: false,
    cwd: ROOT_DIR,
    env: API_ENV,
  });
}

function startUi() {
  uiProc = spawn("npm", ["run", "dev:ui"], {
    stdio: "inherit",
    shell: true,
    cwd: UI_DIR,
    env: process.env,
  });
}

async function stopApi() {
  if (!apiProc || apiProc.killed) return;

  return new Promise((resolve) => {
    const stopper = spawn(PYTHON_CMD, [LAUNCHER, "stop"], {
      stdio: "inherit",
      shell: false,
      cwd: ROOT_DIR,
      env: API_ENV,
    });
    stopper.on("close", resolve);
    stopper.on("error", resolve);
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

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

function startAll() {
  startApi();
  setTimeout(startUi, 1200);
}

startAll();
