#!/usr/bin/env node
import { spawnSync } from "node:child_process";

function parseArgs(argv) {
  const args = {
    successRef: "sample/success_sample.png",
    outdir: "generated",
    forceFallback: process.env.HDR_FORCE_JS_FALLBACK === "1",
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

function runNode(argv) {
  return spawnSync("node", argv, { stdio: "inherit" });
}

const args = parseArgs(process.argv.slice(2));

if (args.forceFallback) {
  console.error("[fallback] --force-fallback/HDR_FORCE_JS_FALLBACK=1 is set. run JS fallback path directly.");
  const forced = runNode([
    "src/jswasm-pipeline/cli.mjs",
    "--success-ref",
    args.successRef,
    "--outdir",
    args.outdir,
    "--force-js-fallback",
    "--allow-no-icc-fallback",
    ...args.passthrough,
  ]);
  process.exit(forced.status ?? 1);
}

const primary = runNode([
  "src/jswasm-pipeline/cli.mjs",
  "--success-ref",
  args.successRef,
  "--outdir",
  args.outdir,
  ...args.passthrough,
]);

if (primary.status === 0) {
  process.exit(0);
}

console.error(`[fallback] primary js/wasm pipeline failed (exit=${primary.status ?? "null"}, signal=${primary.signal ?? "none"}).`);
console.error("[fallback] retry with JS math + allow-no-icc-fallback.");

const fallback = runNode([
  "src/jswasm-pipeline/cli.mjs",
  "--success-ref",
  args.successRef,
  "--outdir",
  args.outdir,
  "--force-js-fallback",
  "--allow-no-icc-fallback",
  ...args.passthrough,
]);

process.exit(fallback.status ?? 1);
