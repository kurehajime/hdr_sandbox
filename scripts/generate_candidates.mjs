#!/usr/bin/env node
import { spawnSync } from "node:child_process";

function parseArgs(argv) {
  const args = {
    successRef: "sample/success_sample.png",
    outdir: "generated",
    fallbackInput: "sample/success_sample.png",
    forceFallback: process.env.HDR_FORCE_PY_FALLBACK === "1",
    passthrough: [],
  };

  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    const v = argv[i + 1];
    if (a === "--success-ref" && v) {
      args.successRef = v;
      i += 1;
    } else if (a === "--outdir" && v) {
      args.outdir = v;
      i += 1;
    } else if (a === "--fallback-input" && v) {
      args.fallbackInput = v;
      i += 1;
    } else if (a === "--force-fallback") {
      args.forceFallback = true;
    } else {
      args.passthrough.push(a);
      if (v && !v.startsWith("--")) {
        args.passthrough.push(v);
        i += 1;
      }
    }
  }

  return args;
}

function run(cmd, argv) {
  return spawnSync(cmd, argv, { stdio: "inherit" });
}

const args = parseArgs(process.argv.slice(2));

if (!args.forceFallback) {
  const jsCmd = [
    "src/jswasm-pipeline/cli.mjs",
    "--success-ref",
    args.successRef,
    "--outdir",
    args.outdir,
    ...args.passthrough,
  ];

  const js = run("node", jsCmd);
  if (js.status === 0) {
    process.exit(0);
  }

  console.error(`[fallback] js/wasm pipeline failed (exit=${js.status ?? "null"}, signal=${js.signal ?? "none"}).`);
} else {
  console.error("[fallback] --force-fallback/HDR_FORCE_PY_FALLBACK=1 is set. skip js/wasm pipeline.");
}

console.error("[fallback] use python scripts/make_candidates.py --extended");
const py = run("python3", [
  "scripts/make_candidates.py",
  "--input",
  args.fallbackInput,
  "--success-ref",
  args.successRef,
  "--outdir",
  args.outdir,
  "--extended",
]);
process.exit(py.status ?? 1);
