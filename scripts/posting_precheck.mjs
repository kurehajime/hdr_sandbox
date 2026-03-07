#!/usr/bin/env node
import { spawnSync } from "node:child_process";

function todayJstIsoDate() {
  const now = new Date();
  const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  return jst.toISOString().slice(0, 10);
}

function parseArgs(argv) {
  const args = {
    generatedDir: "generated",
    observations: "docs/human-observations.md",
    outDate: todayJstIsoDate(),
    checklistBatchMode: "diversified",
    batchSize: 10,
    batchFamilyCap: 2,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    const v = argv[i + 1];

    if (a === "--generated-dir" && v) {
      args.generatedDir = v;
      i += 1;
    } else if (a === "--observations" && v) {
      args.observations = v;
      i += 1;
    } else if (a === "--out-date" && v) {
      args.outDate = v;
      i += 1;
    } else if (a === "--checklist-batch-mode" && v) {
      args.checklistBatchMode = v;
      i += 1;
    } else if (a === "--batch-size" && v) {
      args.batchSize = Number(v);
      i += 1;
    } else if (a === "--batch-family-cap" && v) {
      args.batchFamilyCap = Number(v);
      i += 1;
    }
  }

  return args;
}

function runStep(cmd, argv) {
  const r = spawnSync(cmd, argv, { stdio: "inherit" });
  if (r.status !== 0) {
    process.exit(r.status ?? 1);
  }
}

const args = parseArgs(process.argv.slice(2));
const reportOut = `docs/observation-status-${args.outDate}.md`;
const reportJsonOut = `docs/observation-status-${args.outDate}.json`;
const checklistOut = `docs/posting-checklist-${args.outDate}.md`;

runStep("python3", ["scripts/check_png_hdr.py", `${args.generatedDir}/candidate_success_like.png`]);

runStep("python3", [
  "scripts/check_human_observations.py",
  "--observations",
  args.observations,
  "--generated-dir",
  args.generatedDir,
  "--report-out",
  reportOut,
  "--report-json-out",
  reportJsonOut,
  "--post-checklist-out",
  checklistOut,
  "--checklist-batch-mode",
  args.checklistBatchMode,
  "--checklist-include-targeted-followups",
  "--batch-size",
  String(args.batchSize),
  "--batch-family-cap",
  String(args.batchFamilyCap),
]);

console.log(`posting_precheck: OK (${args.outDate})`);
console.log(`report_md: ${reportOut}`);
console.log(`report_json: ${reportJsonOut}`);
console.log(`checklist_md: ${checklistOut}`);
