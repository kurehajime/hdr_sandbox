#!/usr/bin/env node
import { runMinimalPipeline } from "./pipeline.mjs";

function usage() {
  console.log(`Usage: node src/jswasm-pipeline/cli.mjs [options]

Options:
  --success-ref <path>      source PNG with iCCP (default: sample/success_sample.png)
  --icc-fallback <path>     fallback ICC file when --success-ref has no iCCP
                            (default: generated/icc_bt2020_pq_from_success.icc)
  --allow-no-icc-fallback   allow generation even if ICC is unavailable
  --outdir <dir>            output directory (default: generated)
  --width <n>               output width (default: 400)
  --height <n>              output height (default: 400)
  --alpha8-patch <0-255>    patch alpha in 8bit space (default: 64)
  --force-js-fallback       skip wasm and force JS fallback path
  -h, --help                show this help
`);
}

function parseArgs(argv) {
  const args = {
    successRef: "sample/success_sample.png",
    iccFallbackPath: "generated/icc_bt2020_pq_from_success.icc",
    allowNoIccFallback: false,
    outdir: "generated",
    width: 400,
    height: 400,
    alpha8Patch: 64,
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
    } else if (a === "--icc-fallback" && v) {
      args.iccFallbackPath = v;
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

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const res = await runMinimalPipeline(args);
  console.log(`jswasm_pipeline_mode: ${res.wasmMode}`);
  console.log(`icc_source: ${res.iccSource}`);
  if (res.warning) {
    console.log(`warning: ${res.warning}`);
  }
  for (const p of res.generated) {
    console.log(`generated: ${p}`);
  }
}

main().catch((err) => {
  console.error(`ERROR: ${err.message}`);
  process.exit(1);
});
