#!/usr/bin/env node
import { promises as fs } from "node:fs";
import path from "node:path";

import { generateMinimalCandidates } from "./pipeline.mjs";

function usage() {
  console.log(`Usage: node src/jswasm-pipeline/cli.mjs [options]

Options:
  --input <path>            source PNG for candidate_success_like (default: sample/success_sample.png)
  --success-ref <path>      source PNG with iCCP (default: sample/success_sample.png)
  --icc-fallback <path>     fallback ICC file when --success-ref has no iCCP
                            (default: generated/icc_bt2020_pq_from_success.icc)
  --mode <name>             pass-through | minimal-pattern (default: pass-through)
  --allow-no-icc-fallback   allow generation even if ICC is unavailable
  --outdir <dir>            output directory (default: generated/jswasm)
  --width <n>               output width (default: 400)
  --height <n>              output height (default: 400)
  --alpha8-patch <0-255>    patch alpha in 8bit space (default: 255)
  --force-js-fallback       skip wasm and force JS fallback path
  -h, --help                show this help
`);
}

function parseArgs(argv) {
  const args = {
    input: "sample/success_sample.png",
    successRef: "sample/success_sample.png",
    iccFallbackPath: "generated/icc_bt2020_pq_from_success.icc",
    mode: "pass-through",
    allowNoIccFallback: false,
    outdir: "generated/jswasm",
    width: 400,
    height: 400,
    alpha8Patch: 255,
    forceJsFallback: false,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    const v = argv[i + 1];
    if (a === "-h" || a === "--help") {
      usage();
      process.exit(0);
    } else if (a === "--success-ref" && v) {
      args.successRef = v;
      i += 1;
    } else if (a === "--input" && v) {
      args.input = v;
      i += 1;
    } else if (a === "--icc-fallback" && v) {
      args.iccFallbackPath = v;
      i += 1;
    } else if (a === "--mode" && v) {
      args.mode = v;
      i += 1;
    } else if (a === "--allow-no-icc-fallback") {
      args.allowNoIccFallback = true;
    } else if (a === "--outdir" && v) {
      args.outdir = v;
      i += 1;
    } else if (a === "--width" && v) {
      args.width = Number(v);
      i += 1;
    } else if (a === "--height" && v) {
      args.height = Number(v);
      i += 1;
    } else if (a === "--alpha8-patch" && v) {
      args.alpha8Patch = Number(v);
      i += 1;
    } else if (a === "--force-js-fallback") {
      args.forceJsFallback = true;
    } else {
      throw new Error(`unknown arg: ${a}`);
    }
  }

  return args;
}

async function readOptionalFile(filePath) {
  try {
    return await fs.readFile(filePath);
  } catch (err) {
    if (err && err.code === "ENOENT") {
      return null;
    }
    throw err;
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const inputPngBytes = await fs.readFile(args.input);
  const successRefPngBytes = await fs.readFile(args.successRef);
  const iccFallbackBytes = await readOptionalFile(args.iccFallbackPath);

  const res = await generateMinimalCandidates({
    inputPngBytes,
    successRefPngBytes,
    iccFallbackBytes,
    mode: args.mode,
    width: args.width,
    height: args.height,
    alpha8Patch: args.alpha8Patch,
    allowNoIccFallback: args.allowNoIccFallback,
    forceJsFallback: args.forceJsFallback,
  });

  await fs.mkdir(args.outdir, { recursive: true });
  const generatedPaths = [];
  for (const [name, bytes] of Object.entries(res.files)) {
    const outPath = path.join(args.outdir, name);
    await fs.writeFile(outPath, bytes);
    generatedPaths.push(outPath);
  }

  console.log(`jswasm_pipeline_mode: ${res.wasmMode}`);
  console.log(`icc_source: ${res.iccSource}`);
  if (res.warning) {
    console.log(`warning: ${res.warning}`);
  }
  if (res.fallbackUsed) {
    console.log("fallback: embedded_iCCP_disabled");
  }
  for (const p of generatedPaths) {
    console.log(`generated: ${p}`);
  }
}

main().catch((err) => {
  console.error(`ERROR: ${err.message}`);
  process.exit(1);
});
