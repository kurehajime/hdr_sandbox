#!/usr/bin/env python3
"""docs/human-observations.md の最低限の整合性チェック。"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path


VALID_OBSERVED = {"glows", "not_glows", "whiteout", "blackout", "mixed", "todo"}


def parse_rows(md: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in md.splitlines():
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) != 5:
            continue
        if cols[0] in {"candidate", "---"}:
            continue
        candidate, file_col, observed, x_url, notes = cols
        m = re.search(r"`([^`]+)`", file_col)
        filename = m.group(1) if m else file_col
        rows.append(
            {
                "candidate": candidate,
                "file": filename,
                "observed": observed.strip().lower(),
                "x_post_url": x_url,
                "notes": notes,
            }
        )
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--observations", default="docs/human-observations.md")
    ap.add_argument("--generated-dir", default="generated")
    args = ap.parse_args()

    obs_path = Path(args.observations)
    gen_dir = Path(args.generated_dir)

    if not obs_path.exists():
        raise SystemExit(f"ERROR: not found: {obs_path}")

    rows = parse_rows(obs_path.read_text(encoding="utf-8"))
    if not rows:
        raise SystemExit("ERROR: table rows not found in observations file")

    observed_counter = Counter()
    bad_observed: list[str] = []
    missing_files: list[str] = []

    for r in rows:
        observed_counter[r["observed"]] += 1
        if r["observed"] not in VALID_OBSERVED:
            bad_observed.append(f"{r['candidate']}={r['observed']}")
        if r["file"].upper() != "TODO" and not (gen_dir / r["file"]).exists():
            missing_files.append(r["file"])

    print(f"rows: {len(rows)}")
    print("observed_counts:")
    for k, v in sorted(observed_counter.items()):
        print(f"- {k}: {v}")

    if bad_observed:
        print("invalid_observed:")
        for x in bad_observed:
            print(f"- {x}")

    if missing_files:
        print("missing_generated_files:")
        for f in sorted(set(missing_files)):
            print(f"- {f}")

    if bad_observed or missing_files:
        raise SystemExit(2)

    print("OK")


if __name__ == "__main__":
    main()
