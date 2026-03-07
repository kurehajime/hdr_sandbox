#!/usr/bin/env python3
"""docs/human-observations.md の整合性チェック + 未観測候補の可視化。"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


VALID_OBSERVED = {"glows", "not_glows", "whiteout", "blackout", "mixed", "todo"}
DECISIVE_OBSERVED = {"glows", "not_glows", "mixed"}
NON_DECISIVE_OBSERVED = {"whiteout", "blackout"}
RESOLVED_OBSERVED = {"glows", "not_glows"}
UNCERTAIN_LATEST_OBSERVED = NON_DECISIVE_OBSERVED.union({"mixed"})
FAMILY_PRIORITY = ["cicp", "threshold", "isoeff", "alpha", "position", "luma", "size", "probe_other", "success", "fail", "other"]
DEFAULT_EXTRA_OBSERVATIONS_GLOB = "human-observations-*.md"


def parse_rows(md: str, *, source_file: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line_no, line in enumerate(md.splitlines(), start=1):
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
                "source_file": str(source_file),
                "source_line": line_no,
            }
        )
    return rows


def infer_family(candidate: str) -> str:
    if candidate.startswith("probe_cicp_"):
        return "cicp"
    if candidate.startswith("probe_alpha_"):
        return "alpha"
    if candidate.startswith("probe_position_"):
        return "position"
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


def family_rank(candidate: str) -> int:
    family = infer_family(candidate)
    try:
        return FAMILY_PRIORITY.index(family)
    except ValueError:
        return len(FAMILY_PRIORITY)


def generated_candidates(gen_dir: Path) -> set[str]:
    names: set[str] = set()
    for p in gen_dir.glob("candidate_*.png"):
        name = p.stem
        if name.startswith("candidate_"):
            names.add(name[len("candidate_") :])
        else:
            names.add(name)
    return names


def resolve_observation_paths(
    primary: Path,
    globs: list[str],
    *,
    include_default_extra: bool,
) -> list[Path]:
    paths = [primary]
    root = primary.parent

    effective_globs = list(globs)
    if include_default_extra and primary.name == "human-observations.md":
        effective_globs.append(DEFAULT_EXTRA_OBSERVATIONS_GLOB)

    for pattern in effective_globs:
        matched = sorted(root.glob(pattern))
        if not matched:
            raise SystemExit(
                f"ERROR: no files matched --observations-glob pattern '{pattern}' under {root}"
            )
        for p in matched:
            if p not in paths:
                paths.append(p)

    return paths


def load_rows(obs_paths: list[Path]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for p in obs_paths:
        rows.extend(parse_rows(p.read_text(encoding="utf-8"), source_file=p))
    return rows


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


def pick_control(
    per_candidate: dict[str, dict[str, object]],
    preferred: list[str],
    target_observed: str,
) -> dict[str, object] | None:
    for name in preferred:
        entry = per_candidate.get(name)
        if entry and entry.get("latest_observed") == target_observed:
            return entry

    matched = [
        e for e in per_candidate.values() if e.get("latest_observed") == target_observed
    ]
    if not matched:
        return None

    # 再現性高めの候補を優先（試行回数の多いもの）。
    matched.sort(key=lambda x: (-int(x.get("attempts", 0)), str(x.get("candidate", ""))))
    return matched[0]


def pending_state_rank(row: dict[str, str]) -> int:
    """次バッチ候補の状態優先度。

    0: 完全未観測（observed=todo かつ URL=TODO）
    1: 再試行（whiteout/blackout/mixed）
    2: それ以外の pending（主に URL 未反映）
    """
    observed = row["observed"]
    url_todo = row["x_post_url"].upper() == "TODO"

    if observed == "todo" and url_todo:
        return 0
    if observed in UNCERTAIN_LATEST_OBSERVED:
        return 1
    return 2


def order_pending_rows(pending_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(
        pending_rows,
        key=lambda r: (
            pending_state_rank(r),
            family_rank(r["candidate"]),
            r["candidate"],
        ),
    )


def apply_family_cap(
    ordered_rows: list[dict[str, str]],
    *,
    batch_size: int,
    family_cap: int,
) -> list[dict[str, str]]:
    """priority順を保ちつつ、同一familyの過密を抑える。"""
    if batch_size <= 0:
        return []
    if family_cap <= 0:
        return ordered_rows[:batch_size]

    out: list[dict[str, str]] = []
    delayed: list[dict[str, str]] = []
    counts: Counter[str] = Counter()

    for row in ordered_rows:
        family = infer_family(row["candidate"])
        if counts[family] < family_cap:
            out.append(row)
            counts[family] += 1
        else:
            delayed.append(row)

        if len(out) >= batch_size:
            return out

    # cap適用後に枠が余ったら、優先順のまま補充する。
    for row in delayed:
        out.append(row)
        if len(out) >= batch_size:
            break

    return out


def build_diversified_batch(
    pending_rows: list[dict[str, str]],
    *,
    batch_size: int,
) -> list[dict[str, str]]:
    """familyごとにround-robinで候補を選び、多様性を確保する。"""
    if batch_size <= 0:
        return []

    ordered = order_pending_rows(pending_rows)
    by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in ordered:
        by_family[infer_family(row["candidate"])].append(row)

    families = [fam for fam in FAMILY_PRIORITY if by_family.get(fam)]
    extra_families = sorted(set(by_family.keys()) - set(families))
    families.extend(extra_families)

    out: list[dict[str, str]] = []
    while len(out) < batch_size:
        moved = False
        for fam in families:
            rows = by_family[fam]
            if not rows:
                continue
            out.append(rows.pop(0))
            moved = True
            if len(out) >= batch_size:
                break
        if not moved:
            break

    return out


def build_targeted_followups(
    per_candidate: dict[str, dict[str, object]],
    pending_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    """観測結果に応じた小規模フォローアップ実験パックを提案する。"""

    pending_by_candidate = {r["candidate"]: r for r in pending_rows}
    packs: list[dict[str, object]] = []

    gradient = per_candidate.get("probe_alpha_gradient")
    if gradient and gradient.get("latest_observed") == "mixed":
        items = [
            pending_by_candidate[name]
            for name in [
                "probe_alpha_gradient_rl",
                "probe_alpha_gradient_tb",
                "probe_position_quadrant_alpha64",
            ]
            if name in pending_by_candidate
        ]
        if items:
            packs.append(
                {
                    "name": "alpha_gradient_orientation_followup",
                    "reason": (
                        "`probe_alpha_gradient` が mixed のため、向き変更(RL/TB)と"
                        "4象限同一パッチでalpha依存と位置バイアスを切り分ける"
                    ),
                    "items": items,
                }
            )

    size_512 = per_candidate.get("probe_size_512")
    size_512_nontransparent = per_candidate.get("probe_size_512_nontransparent")
    if (
        size_512
        and size_512_nontransparent
        and size_512.get("latest_observed") in NON_DECISIVE_OBSERVED
        and size_512_nontransparent.get("latest_observed") in NON_DECISIVE_OBSERVED
    ):
        bright_patch = pending_by_candidate.get("probe_size_512_alpha255_bright_patch")
        if bright_patch:
            packs.append(
                {
                    "name": "size_512_brightness_recovery_followup",
                    "reason": (
                        "`probe_size_512` と `probe_size_512_nontransparent` が非決定結果"
                        "のため、bright patch条件で輝度不足由来かを検証する"
                    ),
                    "items": [bright_patch],
                }
            )

    alpha_0 = per_candidate.get("probe_alpha_0")
    alpha_1 = per_candidate.get("probe_alpha_1")
    if (
        alpha_0
        and alpha_1
        and alpha_0.get("latest_observed") in NON_DECISIVE_OBSERVED
        and alpha_1.get("latest_observed") in NON_DECISIVE_OBSERVED
    ):
        items = [
            pending_by_candidate[name]
            for name in ["probe_alpha_16", "probe_alpha_64", "probe_alpha_lr_split_16_64"]
            if name in pending_by_candidate
        ]
        if items:
            packs.append(
                {
                    "name": "alpha_floor_threshold_followup",
                    "reason": (
                        "低alpha(0/1)が非決定結果のため、16/64と左右同時比較で"
                        "可視しきい値帯を絞り込む"
                    ),
                    "items": items,
                }
            )

    return packs


def summarize_family_progress(
    per_candidate: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    """各familyの最新進捗（candidate単位）を集約する。"""
    progress: dict[str, dict[str, object]] = {}

    for entry in per_candidate.values():
        candidate = str(entry["candidate"])
        family = infer_family(candidate)
        observed = str(entry["latest_observed"])
        latest_url = str(entry["latest_url"])
        url_todo = latest_url.upper() == "TODO"

        fam = progress.setdefault(
            family,
            {
                "family": family,
                "total": 0,
                "resolved": 0,
                "uncertain": 0,
                "todo_or_url_todo": 0,
            },
        )

        fam["total"] = int(fam["total"]) + 1

        if observed in RESOLVED_OBSERVED and not url_todo:
            fam["resolved"] = int(fam["resolved"]) + 1
        if observed in UNCERTAIN_LATEST_OBSERVED:
            fam["uncertain"] = int(fam["uncertain"]) + 1
        if observed == "todo" or url_todo:
            fam["todo_or_url_todo"] = int(fam["todo_or_url_todo"]) + 1

    ordered_families = sorted(
        progress,
        key=lambda fam: (
            FAMILY_PRIORITY.index(fam) if fam in FAMILY_PRIORITY else len(FAMILY_PRIORITY),
            fam,
        ),
    )
    return [progress[fam] for fam in ordered_families]


def find_mapping_conflicts(
    rows: list[dict[str, str]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """candidate↔file 対応の不整合を検出する。"""
    candidate_to_files: dict[str, set[str]] = defaultdict(set)
    file_to_candidates: dict[str, set[str]] = defaultdict(set)

    for r in rows:
        candidate_to_files[r["candidate"]].add(r["file"])
        file_to_candidates[r["file"]].add(r["candidate"])

    candidate_conflicts = sorted(
        [
            {"candidate": candidate, "files": sorted(files)}
            for candidate, files in candidate_to_files.items()
            if len(files) >= 2
        ],
        key=lambda x: str(x["candidate"]),
    )

    file_conflicts = sorted(
        [
            {"file": file_name, "candidates": sorted(candidates)}
            for file_name, candidates in file_to_candidates.items()
            if len(candidates) >= 2 and file_name.upper() != "TODO"
        ],
        key=lambda x: str(x["file"]),
    )

    return candidate_conflicts, file_conflicts


def find_url_conflicts(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    """x_post_url が複数candidate/fileに跨って使われていないか検出する。"""
    url_to_candidates: dict[str, set[str]] = defaultdict(set)
    url_to_files: dict[str, set[str]] = defaultdict(set)

    for r in rows:
        url = r["x_post_url"].strip()
        if not url or url.upper() == "TODO":
            continue
        url_to_candidates[url].add(r["candidate"])
        url_to_files[url].add(r["file"])

    conflicts = []
    for url in sorted(url_to_candidates):
        candidates = sorted(url_to_candidates[url])
        files = sorted(url_to_files[url])
        if len(candidates) >= 2 or len(files) >= 2:
            conflicts.append(
                {
                    "x_post_url": url,
                    "candidates": candidates,
                    "files": files,
                }
            )

    return conflicts


def find_duplicate_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """同一観測行の重複（主テーブル+extra 取り込み時の二重登録）を検出する。"""
    grouped: dict[tuple[str, str, str, str], list[dict[str, object]]] = defaultdict(list)
    for r in rows:
        key = (
            str(r["candidate"]),
            str(r["file"]),
            str(r["observed"]),
            str(r["x_post_url"]),
        )
        grouped[key].append(r)

    duplicates: list[dict[str, object]] = []
    for (candidate, file_name, observed, x_post_url), rs in sorted(grouped.items()):
        if len(rs) < 2:
            continue
        duplicates.append(
            {
                "candidate": candidate,
                "file": file_name,
                "observed": observed,
                "x_post_url": x_post_url,
                "count": len(rs),
                "sources": [
                    {
                        "source_file": str(r.get("source_file", "")),
                        "source_line": int(r.get("source_line", 0)),
                    }
                    for r in rs
                ],
            }
        )

    return duplicates


def simplify_row(row: dict[str, object]) -> dict[str, object]:
    """出力向けにcandidate行の主要項目だけを抽出する。"""
    candidate = str(row.get("candidate", ""))
    return {
        "candidate": candidate,
        "file": str(row.get("file", "")),
        "observed": str(row.get("observed", row.get("latest_observed", ""))),
        "x_post_url": str(row.get("x_post_url", row.get("latest_url", ""))),
        "family": infer_family(candidate),
    }


def build_structured_report(
    *,
    obs_paths: list[Path],
    rows: list[dict[str, str]],
    pending_rows: list[dict[str, str]],
    missing_in_table: set[str],
    per_candidate: dict[str, dict[str, object]],
    family_progress: list[dict[str, object]],
    conflicts: list[dict[str, object]],
    retry_candidates: list[dict[str, object]],
    mapping_conflicts_candidate: list[dict[str, object]],
    mapping_conflicts_file: list[dict[str, object]],
    url_conflicts: list[dict[str, object]],
    duplicate_rows: list[dict[str, object]],
    batch_size: int,
    batch_family_cap: int,
) -> dict[str, object]:
    ordered_pending = order_pending_rows(pending_rows)
    capped_priority_batch = apply_family_cap(
        ordered_pending,
        batch_size=batch_size,
        family_cap=batch_family_cap,
    )
    diversified_batch = build_diversified_batch(pending_rows, batch_size=batch_size)
    targeted_followups = build_targeted_followups(per_candidate, pending_rows)

    glow_control = pick_control(
        per_candidate,
        preferred=["success_like", "fail_rgb_no_alpha", "fail_8bit"],
        target_observed="glows",
    )
    not_glow_control = pick_control(
        per_candidate,
        preferred=["fail_no_iccp"],
        target_observed="not_glows",
    )

    return {
        "summary": {
            "observation_files": [str(p) for p in obs_paths],
            "total_rows": len(rows),
            "unique_candidates": len(per_candidate),
            "pending_rows": len(pending_rows),
            "conflicting_candidates": len(conflicts),
            "retry_candidates": len(retry_candidates),
            "missing_in_table": len(missing_in_table),
            "mapping_conflicts_candidate": len(mapping_conflicts_candidate),
            "mapping_conflicts_file": len(mapping_conflicts_file),
            "url_conflicts": len(url_conflicts),
            "duplicate_rows": len(duplicate_rows),
        },
        "family_progress": [
            {
                "family": str(fp["family"]),
                "total": int(fp["total"]),
                "resolved": int(fp["resolved"]),
                "uncertain": int(fp["uncertain"]),
                "todo_or_url_todo": int(fp["todo_or_url_todo"]),
                "completion": (int(fp["resolved"]) / int(fp["total"])) if int(fp["total"]) else 0.0,
            }
            for fp in family_progress
        ],
        "pending": [simplify_row(r) for r in ordered_pending],
        "retry": [
            {
                **simplify_row(c),
                "attempts": int(c.get("attempts", 0)),
                "decisive_outcomes": sorted(str(x) for x in c.get("decisive_set", set())),
            }
            for c in retry_candidates
        ],
        "conflicts": [
            {
                **simplify_row(c),
                "attempts": int(c.get("attempts", 0)),
                "decisive_outcomes": sorted(str(x) for x in c.get("decisive_set", set())),
            }
            for c in conflicts
        ],
        "mapping_conflicts": {
            "candidate_to_files": mapping_conflicts_candidate,
            "file_to_candidates": mapping_conflicts_file,
        },
        "url_conflicts": url_conflicts,
        "duplicate_rows": duplicate_rows,
        "suggested_batches": {
            "controls": {
                "glow": simplify_row(glow_control) if glow_control else None,
                "not_glow": simplify_row(not_glow_control) if not_glow_control else None,
            },
            "priority": [simplify_row(r) for r in capped_priority_batch],
            "priority_family_cap": batch_family_cap,
            "diversified_round_robin": [simplify_row(r) for r in diversified_batch],
            "targeted_followups": [
                {
                    "name": str(pack["name"]),
                    "reason": str(pack["reason"]),
                    "items": [simplify_row(r) for r in pack["items"]],
                }
                for pack in targeted_followups
            ],
            "cicp_focus": [
                simplify_row(r)
                for r in ordered_pending
                if infer_family(r["candidate"]) == "cicp"
            ],
        },
        "missing_candidates": sorted(missing_in_table),
    }


def build_post_checklist(
    *,
    per_candidate: dict[str, dict[str, object]],
    pending_rows: list[dict[str, str]],
    batch_size: int,
    batch_family_cap: int,
    mode: str,
    include_targeted_followups: bool,
) -> str:
    ordered_pending = order_pending_rows(pending_rows)
    priority_batch = apply_family_cap(
        ordered_pending,
        batch_size=batch_size,
        family_cap=batch_family_cap,
    )
    diversified_batch = build_diversified_batch(pending_rows, batch_size=batch_size)
    cicp_focus = [
        r
        for r in ordered_pending
        if infer_family(r["candidate"]) == "cicp"
    ][:batch_size]

    if mode == "priority":
        batch_rows = priority_batch
        mode_label = "priority"
    elif mode == "diversified":
        batch_rows = diversified_batch
        mode_label = "diversified_round_robin"
    else:
        batch_rows = cicp_focus
        mode_label = "cicp_focus"

    targeted_followups = build_targeted_followups(per_candidate, pending_rows)

    glow_control = pick_control(
        per_candidate,
        preferred=["success_like", "fail_rgb_no_alpha", "fail_8bit"],
        target_observed="glows",
    )
    not_glow_control = pick_control(
        per_candidate,
        preferred=["fail_no_iccp"],
        target_observed="not_glows",
    )

    lines: list[str] = []
    lines.append("# X Posting Checklist")
    lines.append("")
    lines.append(f"- checklist_mode: {mode_label}")
    lines.append(f"- batch_size: {batch_size}")
    lines.append(f"- batch_family_cap: {batch_family_cap}")
    lines.append(f"- include_targeted_followups: {str(include_targeted_followups).lower()}")
    lines.append("")

    lines.append("## 0) Controls")
    lines.append("")
    lines.append("| role | candidate | file | expected | result_observed | x_post_url | notes |")
    lines.append("|---|---|---|---|---|---|---|")
    if glow_control:
        lines.append(
            f"| glow | `{glow_control['candidate']}` | `{glow_control['file']}` | glows | TODO | TODO | latest={glow_control['latest_observed']} |"
        )
    if not_glow_control:
        lines.append(
            f"| not_glow | `{not_glow_control['candidate']}` | `{not_glow_control['file']}` | not_glows | TODO | TODO | latest={not_glow_control['latest_observed']} |"
        )
    if not glow_control and not not_glow_control:
        lines.append("| control_missing | - | - | - | TODO | TODO | suitable controls not found |")
    lines.append("")

    lines.append("## 1) Batch candidates")
    lines.append("")
    lines.append("| order | family | candidate | file | current_observed | current_url | result_observed | x_post_url | notes |")
    lines.append("|---:|---|---|---|---|---|---|---|---|")
    if batch_rows:
        for idx, row in enumerate(batch_rows, start=1):
            family = infer_family(row["candidate"])
            lines.append(
                f"| {idx} | `{family}` | `{row['candidate']}` | `{row['file']}` | `{row['observed']}` | {row['x_post_url']} | TODO | TODO | TODO |"
            )
    else:
        lines.append("| 1 | - | - | - | - | - | TODO | TODO | pending candidate not found |")
    lines.append("")

    if include_targeted_followups:
        lines.append("## 1b) Targeted follow-up packs")
        lines.append("")
        if targeted_followups:
            lines.append("既存観測のトリガー条件に応じて、次に優先投稿する候補群。")
            lines.append("")
            for pack in targeted_followups:
                lines.append(f"### {pack['name']}")
                lines.append("")
                lines.append(f"- reason: {pack['reason']}")
                lines.append("")
                lines.append("| candidate | file | current_observed | current_url | result_observed | x_post_url | notes |")
                lines.append("|---|---|---|---|---|---|---|")
                for row in pack["items"]:
                    lines.append(
                        f"| `{row['candidate']}` | `{row['file']}` | `{row['observed']}` | {row['x_post_url']} | TODO | TODO | TODO |"
                    )
                lines.append("")
        else:
            lines.append("- currently no targeted follow-up packs were triggered")
            lines.append("")

    lines.append("## 2) Post-run notes")
    lines.append("")
    lines.append("- controls_passed: TODO")
    lines.append("- environment_notes: TODO")
    lines.append("- follow_up_action: TODO")
    lines.append("")

    return "\n".join(lines)


def build_report(
    rows: list[dict[str, str]],
    pending_rows: list[dict[str, str]],
    missing_in_table: set[str],
    per_candidate: dict[str, dict[str, object]],
    family_progress: list[dict[str, object]],
    conflicts: list[dict[str, object]],
    retry_candidates: list[dict[str, object]],
    mapping_conflicts_candidate: list[dict[str, object]],
    mapping_conflicts_file: list[dict[str, object]],
    url_conflicts: list[dict[str, object]],
    duplicate_rows: list[dict[str, object]],
    batch_size: int,
    batch_family_cap: int,
) -> str:
    ordered_pending = order_pending_rows(pending_rows)
    capped_priority_batch = apply_family_cap(
        ordered_pending,
        batch_size=batch_size,
        family_cap=batch_family_cap,
    )
    diversified_batch = build_diversified_batch(pending_rows, batch_size=batch_size)
    targeted_followups = build_targeted_followups(per_candidate, pending_rows)

    by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in ordered_pending:
        by_family[infer_family(r["candidate"])].append(r)

    glow_control = pick_control(
        per_candidate,
        preferred=["success_like", "fail_rgb_no_alpha", "fail_8bit"],
        target_observed="glows",
    )
    not_glow_control = pick_control(
        per_candidate,
        preferred=["fail_no_iccp"],
        target_observed="not_glows",
    )

    lines: list[str] = []
    lines.append("# Human Observation Status Report")
    lines.append("")
    lines.append(f"- total_rows: {len(rows)}")
    lines.append(f"- unique_candidates: {len(per_candidate)}")
    lines.append(f"- pending_rows: {len(pending_rows)}")
    lines.append(f"- conflicting_candidates: {len(conflicts)}")
    lines.append(f"- retry_candidates: {len(retry_candidates)}")
    lines.append(f"- missing_in_table: {len(missing_in_table)}")
    lines.append(f"- mapping_conflicts_candidate: {len(mapping_conflicts_candidate)}")
    lines.append(f"- mapping_conflicts_file: {len(mapping_conflicts_file)}")
    lines.append(f"- url_conflicts: {len(url_conflicts)}")
    lines.append(f"- duplicate_rows: {len(duplicate_rows)}")
    lines.append("")

    if family_progress:
        lines.append("## Family progress (latest per candidate)")
        lines.append("")
        lines.append("| family | candidates | resolved(glows/not_glows) | uncertain(mixed/whiteout/blackout) | todo_or_url_todo | completion |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for fp in family_progress:
            total = int(fp["total"])
            resolved = int(fp["resolved"])
            completion = (resolved / total * 100.0) if total else 0.0
            lines.append(
                f"| `{fp['family']}` | {total} | {resolved} | {int(fp['uncertain'])} | {int(fp['todo_or_url_todo'])} | {completion:.1f}% |"
            )
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

    if mapping_conflicts_candidate:
        lines.append("## Mapping conflicts (candidate -> multiple files)")
        lines.append("")
        lines.append("同一candidateに複数fileが紐づいているため、候補識別が不安定。表記ゆれを修正する。")
        lines.append("")
        lines.append("| candidate | files |")
        lines.append("|---|---|")
        for ent in mapping_conflicts_candidate:
            files = ", ".join(f"`{f}`" for f in ent["files"])
            lines.append(f"| `{ent['candidate']}` | {files} |")
        lines.append("")

    if mapping_conflicts_file:
        lines.append("## Mapping conflicts (file -> multiple candidates)")
        lines.append("")
        lines.append("同一fileが複数candidate名で使われているため、観測履歴の対応が曖昧。")
        lines.append("")
        lines.append("| file | candidates |")
        lines.append("|---|---|")
        for ent in mapping_conflicts_file:
            candidates = ", ".join(f"`{c}`" for c in ent["candidates"])
            lines.append(f"| `{ent['file']}` | {candidates} |")
        lines.append("")

    if url_conflicts:
        lines.append("## URL conflicts (x_post_url -> multiple candidates/files)")
        lines.append("")
        lines.append("同一URLが複数候補に紐づくと、投稿結果の帰属が曖昧になるため要修正。")
        lines.append("")
        lines.append("| x_post_url | candidates | files |")
        lines.append("|---|---|---|")
        for ent in url_conflicts:
            candidates = ", ".join(f"`{c}`" for c in ent["candidates"])
            files = ", ".join(f"`{f}`" for f in ent["files"])
            lines.append(f"| {ent['x_post_url']} | {candidates} | {files} |")
        lines.append("")

    if duplicate_rows:
        lines.append("## Duplicate rows (same candidate/file/observed/url)")
        lines.append("")
        lines.append("主テーブルと extra メモの二重登録などで同一観測が重複した行。attempts集計を歪めるため整理推奨。")
        lines.append("")
        lines.append("| candidate | file | observed | x_post_url | count | sources |")
        lines.append("|---|---|---|---|---:|---|")
        for ent in duplicate_rows:
            sources = ", ".join(
                f"`{src['source_file']}#{src['source_line']}`" for src in ent["sources"]
            )
            lines.append(
                f"| `{ent['candidate']}` | `{ent['file']}` | `{ent['observed']}` | {ent['x_post_url']} | {ent['count']} | {sources} |"
            )
        lines.append("")

    if pending_rows:
        lines.append("## Pending candidates (needs X posting / result entry)")
        lines.append("")
        lines.append("優先順の目安: cicp → threshold/isoeff → alpha/position/luma → その他")
        lines.append("")
        for family in FAMILY_PRIORITY:
            if family not in by_family:
                continue
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

    if glow_control or not_glow_control:
        lines.append("### 0) 端末状態確認用コントロール")
        lines.append("")
        if glow_control:
            lines.append(
                f"- glow control: `{glow_control['file']}` (`{glow_control['candidate']}` / latest={glow_control['latest_observed']})"
            )
        if not_glow_control:
            lines.append(
                f"- not_glow control: `{not_glow_control['file']}` (`{not_glow_control['candidate']}` / latest={not_glow_control['latest_observed']})"
            )
        lines.append("")

    lines.append(f"### 1) 次バッチ候補（最大 {batch_size} 件）")
    lines.append("")
    if batch_family_cap > 0:
        lines.append(
            "選定順: 未観測(todo/TODO) → 再試行(whiteout/blackout/mixed) → URL補完のみ"
            f"（同一family上限={batch_family_cap}）"
        )
    else:
        lines.append("選定順: 未観測(todo/TODO) → 再試行(whiteout/blackout/mixed) → URL補完のみ")
    lines.append("")
    for r in capped_priority_batch:
        lines.append(
            f"- `{r['file']}` ({r['candidate']} / observed={r['observed']} / url={r['x_post_url']})"
        )
    if not ordered_pending:
        lines.append("- pending候補はありません")
    lines.append("")

    priority_batch = [r["candidate"] for r in capped_priority_batch]
    diversified_names = [r["candidate"] for r in diversified_batch]
    if diversified_batch and diversified_names != priority_batch:
        lines.append(f"### 1b) 次バッチ候補（多様性重視・family round-robin / 最大 {batch_size} 件）")
        lines.append("")
        lines.append("端末状態のドリフトを疑う場合、同一family連投を避けて候補を分散する。")
        lines.append("")
        for r in diversified_batch:
            fam = infer_family(r["candidate"])
            lines.append(
                f"- `{r['file']}` ({r['candidate']} / family={fam} / observed={r['observed']} / url={r['x_post_url']})"
            )
        lines.append("")

    if targeted_followups:
        lines.append("### 1c) ターゲット追試パック（観測トリガー連動）")
        lines.append("")
        lines.append("既存観測の結果から、優先して切り分けたい小規模パックを抽出。")
        lines.append("")
        for pack in targeted_followups:
            lines.append(f"- `{pack['name']}`: {pack['reason']}")
            for r in pack["items"]:
                lines.append(
                    f"  - `{r['file']}` ({r['candidate']} / observed={r['observed']} / url={r['x_post_url']})"
                )
        lines.append("")

    cicp = [r for r in ordered_pending if infer_family(r["candidate"]) == "cicp"]
    if cicp:
        lines.append("### 2) cicp比較メモ")
        lines.append("")
        lines.append("以下のcicp候補を同一端末・同一表示条件で連続投稿し、差分だけを比較する:")
        for r in cicp:
            lines.append(f"- `{r['file']}`")
    elif retry_candidates:
        lines.append("### 2) 再試行優先メモ")
        lines.append("")
        lines.append("cicp未観測がないため、次は再現性確認の再投稿を優先:")
        for r in retry_candidates[:6]:
            lines.append(f"- `{r['file']}` ({r['latest_observed']})")
    else:
        lines.append("### 2) 次フェーズ")
        lines.append("")
        lines.append("- cicp未観測候補はありません。次は threshold/isoeff 系を優先。")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--observations", default="docs/human-observations.md")
    ap.add_argument(
        "--observations-glob",
        action="append",
        default=[],
        help=(
            "追加で読み込む観測ファイルのglobパターン。"
            " --observations の親ディレクトリ配下で解決される"
            " (例: --observations-glob 'human-observations-*.md')"
        ),
    )
    ap.add_argument(
        "--no-default-extra-observations",
        action="store_true",
        help=(
            "--observations が docs/human-observations.md の場合に自動追加される"
            f" '{DEFAULT_EXTRA_OBSERVATIONS_GLOB}' 読み込みを無効化する"
        ),
    )
    ap.add_argument("--generated-dir", default="generated")
    ap.add_argument("--report-out", help="未観測候補のMarkdownレポート出力先")
    ap.add_argument(
        "--report-json-out",
        help="機械処理向けのJSONレポート出力先（投稿自動化/集計連携用）",
    )
    ap.add_argument(
        "--post-checklist-out",
        help="X投稿用チェックリストのMarkdown出力先（手動投稿・記録補助）",
    )
    ap.add_argument(
        "--checklist-batch-mode",
        choices=["priority", "diversified", "cicp"],
        default="priority",
        help="post-checklistに採用する候補セット（priority/diversified/cicp）",
    )
    ap.add_argument(
        "--checklist-include-targeted-followups",
        action="store_true",
        help="post-checklistに target follow-up pack セクションを追加する",
    )
    ap.add_argument("--batch-size", type=int, default=8, help="レポート内の次バッチ候補の最大件数")
    ap.add_argument(
        "--batch-family-cap",
        type=int,
        default=0,
        help="次バッチ候補で同一familyに割り当てる最大件数（0で無制限）",
    )
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
    ap.add_argument(
        "--strict-retry",
        action="store_true",
        help="最新観測が whiteout/blackout/mixed の候補が1件でもあれば終了コード2を返す",
    )
    ap.add_argument(
        "--strict-mapping",
        action="store_true",
        help="candidate↔file 対応に不整合（1対多/多対1）があれば終了コード2を返す",
    )
    ap.add_argument(
        "--strict-url-mapping",
        action="store_true",
        help="x_post_url が複数candidate/fileへ紐づく不整合があれば終了コード2を返す",
    )
    ap.add_argument(
        "--strict-duplicate-rows",
        action="store_true",
        help="同一観測行の重複（candidate/file/observed/url一致）があれば終了コード2を返す",
    )
    args = ap.parse_args()

    if args.batch_size <= 0:
        raise SystemExit("ERROR: --batch-size must be > 0")
    if args.batch_family_cap < 0:
        raise SystemExit("ERROR: --batch-family-cap must be >= 0")

    obs_path = Path(args.observations)
    gen_dir = Path(args.generated_dir)

    if not obs_path.exists():
        raise SystemExit(f"ERROR: not found: {obs_path}")

    obs_paths = resolve_observation_paths(
        obs_path,
        args.observations_glob,
        include_default_extra=not args.no_default_extra_observations,
    )
    rows = load_rows(obs_paths)
    if not rows:
        raise SystemExit("ERROR: table rows not found in observations file(s)")

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
    family_progress = summarize_family_progress(per_candidate)
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
            if v["latest_observed"] in UNCERTAIN_LATEST_OBSERVED
        ],
        key=lambda x: str(x["candidate"]),
    )
    mapping_conflicts_candidate, mapping_conflicts_file = find_mapping_conflicts(rows)
    url_conflicts = find_url_conflicts(rows)
    duplicate_rows = find_duplicate_rows(rows)

    print(f"observation_files: {len(obs_paths)}")
    for p in obs_paths:
        print(f"- {p}")

    print(f"rows: {len(rows)}")
    print(f"unique_candidates: {len(per_candidate)}")
    print("observed_counts:")
    for k, v in sorted(observed_counter.items()):
        print(f"- {k}: {v}")

    print("family_progress_latest:")
    for fp in family_progress:
        total = int(fp["total"])
        resolved = int(fp["resolved"])
        completion = (resolved / total * 100.0) if total else 0.0
        print(
            "- "
            f"{fp['family']}: total={total} resolved={resolved} "
            f"uncertain={int(fp['uncertain'])} todo_or_url_todo={int(fp['todo_or_url_todo'])} "
            f"completion={completion:.1f}%"
        )

    print(f"pending_rows: {len(pending_rows)}")
    if pending_rows:
        print("pending_candidates:")
        for r in order_pending_rows(pending_rows):
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

    print(f"mapping_conflicts_candidate: {len(mapping_conflicts_candidate)}")
    if mapping_conflicts_candidate:
        print("mapping_conflicts_candidate_list:")
        for ent in mapping_conflicts_candidate:
            files = ",".join(str(f) for f in ent["files"])
            print(f"- {ent['candidate']} ({files})")

    print(f"mapping_conflicts_file: {len(mapping_conflicts_file)}")
    if mapping_conflicts_file:
        print("mapping_conflicts_file_list:")
        for ent in mapping_conflicts_file:
            candidates = ",".join(str(c) for c in ent["candidates"])
            print(f"- {ent['file']} ({candidates})")

    print(f"url_conflicts: {len(url_conflicts)}")
    if url_conflicts:
        print("url_conflicts_list:")
        for ent in url_conflicts:
            candidates = ",".join(str(c) for c in ent["candidates"])
            files = ",".join(str(f) for f in ent["files"])
            print(f"- {ent['x_post_url']} (candidates={candidates} / files={files})")

    print(f"duplicate_rows: {len(duplicate_rows)}")
    if duplicate_rows:
        print("duplicate_rows_list:")
        for ent in duplicate_rows:
            source_short = ",".join(
                f"{Path(str(src['source_file'])).name}#{src['source_line']}"
                for src in ent["sources"]
            )
            print(
                f"- {ent['candidate']} ({ent['file']} / {ent['observed']} / {ent['x_post_url']} / count={ent['count']} / sources={source_short})"
            )

    if bad_observed:
        print("invalid_observed:")
        for x in bad_observed:
            print(f"- {x}")

    if missing_files:
        print("missing_generated_files:")
        for f in sorted(set(missing_files)):
            print(f"- {f}")

    if args.report_out:
        report = build_report(
            rows,
            pending_rows,
            missing_in_table,
            per_candidate,
            family_progress,
            conflicts,
            retry_candidates,
            mapping_conflicts_candidate,
            mapping_conflicts_file,
            url_conflicts,
            duplicate_rows,
            batch_size=args.batch_size,
            batch_family_cap=args.batch_family_cap,
        )
        out = Path(args.report_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"report_written: {out}")

    if args.report_json_out:
        report_json = build_structured_report(
            obs_paths=obs_paths,
            rows=rows,
            pending_rows=pending_rows,
            missing_in_table=missing_in_table,
            per_candidate=per_candidate,
            family_progress=family_progress,
            conflicts=conflicts,
            retry_candidates=retry_candidates,
            mapping_conflicts_candidate=mapping_conflicts_candidate,
            mapping_conflicts_file=mapping_conflicts_file,
            url_conflicts=url_conflicts,
            duplicate_rows=duplicate_rows,
            batch_size=args.batch_size,
            batch_family_cap=args.batch_family_cap,
        )
        out_json = Path(args.report_json_out)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(
            json.dumps(report_json, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"report_json_written: {out_json}")

    if args.post_checklist_out:
        checklist = build_post_checklist(
            per_candidate=per_candidate,
            pending_rows=pending_rows,
            batch_size=args.batch_size,
            batch_family_cap=args.batch_family_cap,
            mode=args.checklist_batch_mode,
            include_targeted_followups=args.checklist_include_targeted_followups,
        )
        out_checklist = Path(args.post_checklist_out)
        out_checklist.parent.mkdir(parents=True, exist_ok=True)
        out_checklist.write_text(checklist, encoding="utf-8")
        print(f"post_checklist_written: {out_checklist}")

    if bad_observed or missing_files:
        raise SystemExit(2)

    if args.strict_pending and pending_rows:
        raise SystemExit(2)

    if args.strict_conflict and conflicts:
        raise SystemExit(2)

    if args.strict_retry and retry_candidates:
        raise SystemExit(2)

    if args.strict_mapping and (mapping_conflicts_candidate or mapping_conflicts_file):
        raise SystemExit(2)

    if args.strict_url_mapping and url_conflicts:
        raise SystemExit(2)

    if args.strict_duplicate_rows and duplicate_rows:
        raise SystemExit(2)

    print("OK")


if __name__ == "__main__":
    main()
