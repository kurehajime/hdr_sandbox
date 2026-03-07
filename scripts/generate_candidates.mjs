#!/usr/bin/env node
import { spawnSync } from "node:child_process";

const args = process.argv.slice(2);

const jsCmd = [
  "node",
  "src/jswasm-pipeline/cli.mjs",
  "--success-ref",
  "sample/success_sample.png",
  "--outdir",
  "generated",
  ...args,
];

const js = spawnSync(jsCmd[0], jsCmd.slice(1), { stdio: "inherit" });
if (js.status === 0) {
  process.exit(0);
}

console.error("[fallback] js/wasm pipeline failed. fallback to python scripts/make_candidates.py --extended");
const py = spawnSync(
  "python3",
  [
    "scripts/make_candidates.py",
    "--input",
    "sample/success_sample.png",
    "--success-ref",
    "sample/success_sample.png",
    "--outdir",
    "generated",
    "--extended",
  ],
  { stdio: "inherit" },
);
process.exit(py.status ?? 1);
