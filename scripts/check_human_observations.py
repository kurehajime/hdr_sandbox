#!/usr/bin/env python3
"""docs/human-observations.md の整合性チェック + 未観測候補の可視化。"""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path


VALID_OBSERVED = {"glows", "not_glows", "whiteout", "blackout", "mixed", "todo"}
DECISIVE_OBSERVED = {"glows", "not_glows", "mixed"}
NON_DECISIVE_OBSERVED = {"whiteout", "blackout"}


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
                "x_post_url": x_url.strip(),
                "notes": notes,
            }
        )
    return rows


def infer_family(candidate: str) -> str:
    if candidate.startswith("probe_cicp_"):
        return "cicp"
    if candidate.startswith("probe_alpha_"):
        return "alpha"
    if candidate.startswith("probe_luma_"):
        return "luma"
    if candidate.startswith("probe_size_"):
        return "size"
    if candidate.startswith("probe_threshold_"):
        return "threshold"
    if candidate.startswith("probe_isoeff_"):
        return "isoeff"
    if candidate.startswith("success"):
        return "success"
    if candidate.startswith("fail"):
        return "fail"
    if candidate.startswith("probe_"):
        return "probe_other"
    return "other"


def generated_candidates(gen_dir: Path) -> set[str]:
    names: set[str] = set()
    for p in gen_dir.glob("candidate_*.png"):
        name = p.stem
        if name.startswith("candidate_"):
            names.add(name[len("candidate_") :])
        else:
            names.add(name)
    return names


def summarize_candidates(rows: list[dict[str, str]]) -> dict[str, dict[str, object]]:
    summary: dict[str, dict[str, object]] = {}
    for r in rows:
        key = r["candidate"]
        ent = summary.setdefault(
            key,
            {
                "candidate": key,
                "file": r["file"],
                "attempts": 0,
                "latest_observed": "todo",
                "latest_url": "TODO",
                "decisive_set": set(),
                "nondc_count": 0,
                "has_pending": False,
            },
        )
        ent["attempts"] = int(ent["attempts"]) + 1
        ent["file"] = r["file"]
        ent["latest_observed"] = r["observed"]
        ent["latest_url"] = r["x_post_url"]

        if r["observed"] in DECISIVE_OBSERVED:
            ent["decisive_set"].add(r["observed"])
        if r["observed"] in NON_DECISIVE_OBSERVED:
            ent["nondc_count"] = int(ent["nondc_count"]) + 1

        ent["has_pending"] = r["observed"] == "todo" or r["x_post_url"].upper() == "TODO"

    return summary


def build_report(
    rows: list[dict[str, str]],
    pending_rows: list[dict[str, str]],
    missing_in_table: set[str],
    per_candidate: dict[str, dict[str, object]],
    conflicts: list[dict[str, object]],
    retry_candidates: list[dict[str, object]],
) -> str:
    by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in pending_rows:
        by_family[infer_family(r["candidate"])].append(r)

    lines: list[str] = []
    lines.append("# Human Observation Status Report")
    lines.append("")
    lines.append(f"- total_rows: {len(rows)}")
    lines.append(f"- unique_candidates: {len(per_candidate)}")
    lines.append(f"- pending_rows: {len(pending_rows)}")
    lines.append(f"- conflicting_candidates: {len(conflicts)}")
    lines.append(f"- retry_candidates: {len(retry_candidates)}")
    lines.append(f"- missing_in_table: {len(missing_in_table)}")
    lines.append("")

    if conflicts:
        lines.append("## Conflicting decisive observations (needs re-check)")
        lines.append("")
        lines.append("同一candidateで glows/not_glows/mixed が混在したもの。再投稿して再現性を確認する。")
        lines.append("")
        lines.append("| candidate | file | attempts | decisive_outcomes | latest_observed | latest_url |")
        lines.append("|---|---|---:|---|---|---|")
        for c in conflicts:
            dec = ", ".join(sorted(c["decisive_set"]))
            lines.append(
                f"| `{c['candidate']}` | `{c['file']}` | {c['attempts']} | `{dec}` | `{c['latest_observed']}` | {c['latest_url']} |"
            )
        lines.append("")

    if retry_candidates:
        lines.append("## Retry candidates (non-decisive latest result)")
        lines.append("")
        lines.append("最新が whiteout/blackout/mixed の候補。判定可能な条件で再投稿する。")
        lines.append("")
        lines.append("| candidate | file | latest_observed | attempts | latest_url |")
        lines.append("|---|---|---|---:|---|")
        for c in retry_candidates:
            lines.append(
                f"| `{c['candidate']}` | `{c['file']}` | `{c['latest_observed']}` | {c['attempts']} | {c['latest_url']} |"
            )
        lines.append("")

    if pending_rows:
        lines.append("## Pending candidates (needs X posting / result entry)")
        lines.append("")
        lines.append("優先順の目安: cicp → threshold/isoeff → alpha/luma → その他")
        lines.append("")
        for family in sorted(by_family.keys(), key=lambda k: (k != "cicp", k)):
            lines.append(f"### {family}")
            lines.append("")
            lines.append("| candidate | file | observed | x_post_url |")
            lines.append("|---|---|---|---|")
            for r in by_family[family]:
                lines.append(
                    f"| `{r['candidate']}` | `{r['file']}` | `{r['observed']}` | {r['x_post_url']} |"
                )
            lines.append("")

    if missing_in_table:
        lines.append("## Generated but missing in observations table")
        lines.append("")
        for name in sorted(missing_in_table):
            lines.append(f"- `{name}`")
        lines.append("")

    lines.append("## Suggested immediate batch")
    lines.append("")
    cicp = [r for r in pending_rows if infer_family(r["candidate"]) == "cicp"]
    if cicp:
        lines.append("以下の6条件(cicp)を同一端末・同一表示条件で連続投稿して比較する:")
        for r in cicp:
            lines.append(f"- `{r['file']}`")
    elif retry_candidates:
        lines.append("cicp未観測がないため、次は再現性確認の再投稿を優先:")
        for r in retry_candidates[:6]:
            lines.append(f"- `{r['file']}` ({r['latest_observed']})")
    else:
        lines.append("- cicp未観測候補はありません。次は threshold/isoeff 系を優先。")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--observations", default="docs/human-observations.md")
    ap.add_argument("--generated-dir", default="generated")
    ap.add_argument("--report-out", help="未観測候補のMarkdownレポート出力先")
    ap.add_argument(
        "--strict-pending",
        action="store_true",
        help="pending(todo/TODO URL) が1件でもあれば終了コード2を返す",
    )
    ap.add_argument(
        "--strict-conflict",
        action="store_true",
        help="同一candidateの decisive 観測が衝突したら終了コード2を返す",
    )
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

    pending_rows = [
        r
        for r in rows
        if r["observed"] == "todo" or r["x_post_url"].upper() == "TODO"
    ]

    obs_candidates = {r["candidate"] for r in rows}
    gen_candidates = generated_candidates(gen_dir)
    missing_in_table = gen_candidates - obs_candidates

    per_candidate = summarize_candidates(rows)
    conflicts = sorted(
        [
            v
            for v in per_candidate.values()
            if len(v["decisive_set"]) >= 2
        ],
        key=lambda x: str(x["candidate"]),
    )
    retry_candidates = sorted(
        [
            v
            for v in per_candidate.values()
            if v["latest_observed"] in NON_DECISIVE_OBSERVED.union({"mixed"})
        ],
        key=lambda x: str(x["candidate"]),
    )

    print(f"rows: {len(rows)}")
    print(f"unique_candidates: {len(per_candidate)}")
    print("observed_counts:")
    for k, v in sorted(observed_counter.items()):
        print(f"- {k}: {v}")

    print(f"pending_rows: {len(pending_rows)}")
    if pending_rows:
        print("pending_candidates:")
        for r in pending_rows:
            print(f"- {r['candidate']} ({r['observed']} / {r['x_post_url']})")

    print(f"conflicting_candidates: {len(conflicts)}")
    if conflicts:
        print("conflict_candidates:")
        for c in conflicts:
            dec = ",".join(sorted(c["decisive_set"]))
            print(f"- {c['candidate']} ({dec})")

    print(f"retry_candidates: {len(retry_candidates)}")
    if retry_candidates:
        print("retry_candidates_list:")
        for c in retry_candidates:
            print(f"- {c['candidate']} ({c['latest_observed']})")

    print(f"missing_in_table: {len(missing_in_table)}")
    if missing_in_table:
        print("generated_candidates_missing_in_table:")
        for name in sorted(missing_in_table):
            print(f"- {name}")

    if bad_observed:
        print("invalid_observed:")
        for x in bad_observed:
            print(f"- {x}")

    if missing_files:
        print("missing_generated_files:")
        for f in sorted(set(missing_files)):
            print(f"- {f}")

    if args.report_out:
        report = build_report(rows, pending_rows, missing_in_table, per_candidate, conflicts, retry_candidates)
        out = Path(args.report_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"report_written: {out}")

    if bad_observed or missing_files:
        raise SystemExit(2)

    if args.strict_pending and pending_rows:
        raise SystemExit(2)

    if args.strict_conflict and conflicts:
        raise SystemExit(2)

    print("OK")


if __name__ == "__main__":
    main()
