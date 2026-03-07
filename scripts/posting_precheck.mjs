#!/usr/bin/env node
import { spawnSync } from "node:child_process";

const steps = [
  ["python3", ["scripts/check_png_hdr.py", "generated/candidate_success_like.png"]],
  [
    "python3",
    [
      "scripts/check_human_observations.py",
      "--observations",
      "docs/human-observations.md",
      "--generated-dir",
      "generated",
      "--report-out",
      "docs/observation-status-2026-03-08.md",
      "--report-json-out",
      "docs/observation-status-2026-03-08.json",
      "--post-checklist-out",
      "docs/posting-checklist-2026-03-08.md",
      "--checklist-batch-mode",
      "diversified",
      "--checklist-include-targeted-followups",
      "--batch-size",
      "10",
      "--batch-family-cap",
      "2",
    ],
  ],
];

for (const [cmd, argv] of steps) {
  const r = spawnSync(cmd, argv, { stdio: "inherit" });
  if (r.status !== 0) {
    process.exit(r.status ?? 1);
  }
}

console.log("posting_precheck: OK");
