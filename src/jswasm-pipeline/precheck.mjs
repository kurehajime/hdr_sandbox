#!/usr/bin/env node
import { promises as fs } from "node:fs";
import path from "node:path";

import { getIhdrSummary, hasIccProfile } from "./core.mjs";

function todayJstIsoDate() {
  const now = new Date();
  const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  return jst.toISOString().slice(0, 10);
}

function parseArgs(argv) {
  const args = {
    generatedDir: "generated",
    outDate: todayJstIsoDate(),
    docsDir: "docs",
  };

  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    const v = argv[i + 1];
    if (a === "--generated-dir" && v) {
      args.generatedDir = v;
      i += 1;
    } else if (a === "--out-date" && v) {
      args.outDate = v;
      i += 1;
    } else if (a === "--docs-dir" && v) {
      args.docsDir = v;
      i += 1;
    } else if (a === "-h" || a === "--help") {
      console.log(`Usage: node src/jswasm-pipeline/precheck.mjs [options]

Options:
  --generated-dir <dir>  generated image dir (default: generated)
  --out-date <YYYY-MM-DD> output date stamp for docs (default: JST today)
  --docs-dir <dir>       docs output dir (default: docs)
`);
      process.exit(0);
    } else {
      throw new Error(`unknown arg: ${a}`);
    }
  }

  return args;
}

async function inspectCandidate(filePath) {
  const bytes = await fs.readFile(filePath);
  const ihdr = getIhdrSummary(bytes, filePath);
  return {
    file: filePath,
    exists: true,
    ihdr,
    hasIcc: hasIccProfile(bytes, filePath),
  };
}

function checkResult({ success, failNoIcc }) {
  const errors = [];

  if (success.ihdr.bitDepth !== 16 || success.ihdr.colorType !== 6) {
    errors.push("candidate_success_like.png must be RGBA16 (bitDepth=16,colorType=6)");
  }
  if (!success.hasIcc) {
    errors.push("candidate_success_like.png must include iCCP");
  }
  if (failNoIcc.ihdr.bitDepth !== 16 || failNoIcc.ihdr.colorType !== 6) {
    errors.push("candidate_fail_no_iccp.png must be RGBA16 (bitDepth=16,colorType=6)");
  }
  if (failNoIcc.hasIcc) {
    errors.push("candidate_fail_no_iccp.png must NOT include iCCP");
  }

  return {
    ok: errors.length === 0,
    errors,
  };
}

function toMarkdown({ outDate, success, failNoIcc, summary }) {
  return [
    `# observation-status-${outDate}`,
    "",
    "## JS/WASM precheck (implementation phase)",
    "",
    `- overall: ${summary.ok ? "ok" : "failed"}`,
    `- checked_at: ${new Date().toISOString()}`,
    "",
    "## candidate_success_like.png",
    `- file: ${success.file}`,
    `- width: ${success.ihdr.width}`,
    `- height: ${success.ihdr.height}`,
    `- bit_depth: ${success.ihdr.bitDepth}`,
    `- color_type: ${success.ihdr.colorType}`,
    `- has_iCCP: ${success.hasIcc}`,
    "",
    "## candidate_fail_no_iccp.png",
    `- file: ${failNoIcc.file}`,
    `- width: ${failNoIcc.ihdr.width}`,
    `- height: ${failNoIcc.ihdr.height}`,
    `- bit_depth: ${failNoIcc.ihdr.bitDepth}`,
    `- color_type: ${failNoIcc.ihdr.colorType}`,
    `- has_iCCP: ${failNoIcc.hasIcc}`,
    "",
    ...(summary.errors.length > 0
      ? ["## errors", "", ...summary.errors.map((e) => `- ${e}`), ""]
      : ["## errors", "", "- none", ""]),
  ].join("\n");
}

function toChecklist({ outDate, summary }) {
  return [
    `# posting-checklist-${outDate}`,
    "",
    "実装フェーズ用の最小チェック（検証運用改善は保留）。",
    "",
    `- [ ] precheck status: ${summary.ok ? "ok" : "failed"}`,
    "- [ ] candidate_success_like.png を投稿して表示確認",
    "- [ ] candidate_fail_no_iccp.png を投稿して非HDR想定を確認",
    "",
    ...(summary.errors.length > 0 ? ["## precheck errors", ...summary.errors.map((e) => `- ${e}`), ""] : []),
  ].join("\n");
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  const successPath = path.join(args.generatedDir, "candidate_success_like.png");
  const failPath = path.join(args.generatedDir, "candidate_fail_no_iccp.png");

  const [success, failNoIcc] = await Promise.all([
    inspectCandidate(successPath),
    inspectCandidate(failPath),
  ]);

  const summary = checkResult({ success, failNoIcc });

  await fs.mkdir(args.docsDir, { recursive: true });
  const reportJsonOut = path.join(args.docsDir, `observation-status-${args.outDate}.json`);
  const reportMdOut = path.join(args.docsDir, `observation-status-${args.outDate}.md`);
  const checklistOut = path.join(args.docsDir, `posting-checklist-${args.outDate}.md`);

  const report = {
    phase: "jswasm-implementation",
    date: args.outDate,
    summary,
    success,
    failNoIcc,
  };

  await fs.writeFile(reportJsonOut, `${JSON.stringify(report, null, 2)}\n`);
  await fs.writeFile(reportMdOut, `${toMarkdown({ outDate: args.outDate, success, failNoIcc, summary })}\n`);
  await fs.writeFile(checklistOut, `${toChecklist({ outDate: args.outDate, summary })}\n`);

  console.log(`posting_precheck: ${summary.ok ? "OK" : "FAILED"} (${args.outDate})`);
  console.log(`report_md: ${reportMdOut}`);
  console.log(`report_json: ${reportJsonOut}`);
  console.log(`checklist_md: ${checklistOut}`);

  if (!summary.ok) {
    process.exit(2);
  }
}

main().catch((err) => {
  console.error(`ERROR: ${err.message}`);
  process.exit(1);
});
