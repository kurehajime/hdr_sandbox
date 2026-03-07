#!/usr/bin/env node
import { runMinimalPipeline } from "./pipeline.mjs";

function parseArgs(argv) {
  const args = {
    successRef: "sample/success_sample.png",
    outdir: "generated",
    width: 400,
    height: 400,
    alpha8Patch: 64,
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
    } else if (a === "--width" && v) {
      args.width = Number(v);
      i += 1;
    } else if (a === "--height" && v) {
      args.height = Number(v);
      i += 1;
    } else if (a === "--alpha8-patch" && v) {
      args.alpha8Patch = Number(v);
      i += 1;
    }
  }

  return args;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const res = await runMinimalPipeline(args);
  console.log(`jswasm_pipeline_mode: ${res.wasmMode}`);
  for (const p of res.generated) {
    console.log(`generated: ${p}`);
  }
}

main().catch((err) => {
  console.error(`ERROR: ${err.message}`);
  process.exit(1);
});
