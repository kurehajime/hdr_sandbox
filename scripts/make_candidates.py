#!/usr/bin/env python3
"""
成功例(success_sample.png)の特徴を再現したPNG候補と、失敗比較用バリアントを生成する。

Usage:
  # 基本セット
  python3 scripts/make_candidates.py \
    --input sample/success_sample.png \
    --success-ref sample/success_sample.png \
    --outdir generated

  # 追加切り分けセット（iCCP/cicpは維持し、他条件を変える）
  python3 scripts/make_candidates.py \
    --input sample/success_sample.png \
    --success-ref sample/success_sample.png \
    --outdir generated \
    --extended
"""

from __future__ import annotations

import argparse
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


PNG_SIG = b"\x89PNG\r\n\x1a\n"
TARGET_CICP = [9, 16, 0, 1]


@dataclass
class CandidateResult:
    name: str
    path: Path
    width: int
    height: int
    bit_depth: int
    color_type: int
    has_iccp: bool
    cicp: list[int] | None
    match_legacy_profile: bool
    match_relaxed_profile: bool


def _chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def extract_icc_from_png(path: Path) -> bytes:
    b = path.read_bytes()
    if b[:8] != PNG_SIG:
        raise ValueError(f"not png: {path}")

    o = 8
    while o < len(b):
        ln = struct.unpack(">I", b[o : o + 4])[0]
        o += 4
        typ = b[o : o + 4]
        o += 4
        data = b[o : o + ln]
        o += ln
        o += 4  # crc

        if typ == b"iCCP":
            name = data.split(b"\x00", 1)[0]
            return zlib.decompress(data[len(name) + 2 :])
        if typ == b"IEND":
            break

    raise ValueError(f"iCCP not found: {path}")


def parse_cicp_from_icc(icc: bytes) -> list[int] | None:
    if len(icc) < 132:
        return None
    tag_count = struct.unpack(">I", icc[128:132])[0]
    for i in range(tag_count):
        off = 132 + i * 12
        if off + 12 > len(icc):
            break
        sig = icc[off : off + 4]
        to, sz = struct.unpack(">II", icc[off + 4 : off + 12])
        if sig.lower() == b"cicp" and to + sz <= len(icc):
            d = icc[to : to + sz]
            if len(d) >= 12:
                return list(d[8:12])
    return None


def write_png(
    path: Path,
    arr: np.ndarray,
    *,
    bit_depth: int,
    color_type: int,
    icc_profile: bytes | None,
    text_entries: dict[str, str] | None = None,
) -> None:
    h, w, c = arr.shape
    if color_type == 6 and c != 4:
        raise ValueError("color_type=6 requires 4 channels")
    if color_type == 2 and c != 3:
        raise ValueError("color_type=2 requires 3 channels")
    if bit_depth not in (8, 16):
        raise ValueError("bit_depth must be 8 or 16")

    if bit_depth == 8:
        if arr.dtype != np.uint8:
            arr = np.clip(arr, 0, 255).astype(np.uint8)
    else:
        if arr.dtype != np.uint16:
            arr = np.clip(arr, 0, 65535).astype(np.uint16)

    ihdr = struct.pack(">IIBBBBB", w, h, bit_depth, color_type, 0, 0, 0)
    out = bytearray(PNG_SIG)
    out.extend(_chunk(b"IHDR", ihdr))

    if icc_profile:
        # iCCP: profile_name\0 compression_method(0) + compressed_profile
        iccp_data = b"icc\x00\x00" + zlib.compress(icc_profile, level=9)
        out.extend(_chunk(b"iCCP", iccp_data))

    if text_entries:
        for k, v in text_entries.items():
            t = k.encode("latin1", "ignore") + b"\x00" + v.encode("latin1", "ignore")
            out.extend(_chunk(b"tEXt", t))

    if bit_depth == 8:
        row_bytes = arr.tobytes(order="C")
        row_stride = w * c
    else:
        row_bytes = arr.astype(">u2", copy=False).tobytes(order="C")
        row_stride = w * c * 2

    raw = bytearray()
    for y in range(h):
        raw.append(0)  # filter method: None
        s = y * row_stride
        raw.extend(row_bytes[s : s + row_stride])

    out.extend(_chunk(b"IDAT", zlib.compress(bytes(raw), level=9)))
    out.extend(_chunk(b"IEND", b""))

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(out)


def parse_png_meta(path: Path) -> tuple[int, int, int, int, bool, list[int] | None]:
    b = path.read_bytes()
    if b[:8] != PNG_SIG:
        raise ValueError(f"not png: {path}")

    o = 8
    width = -1
    height = -1
    bit_depth = -1
    color_type = -1
    has_iccp = False
    cicp = None

    while o < len(b):
        ln = struct.unpack(">I", b[o : o + 4])[0]
        o += 4
        typ = b[o : o + 4]
        o += 4
        data = b[o : o + ln]
        o += ln
        o += 4  # crc

        if typ == b"IHDR":
            width, height, bit_depth, color_type, _cm, _fm, _im = struct.unpack(">IIBBBBB", data)
        elif typ == b"iCCP":
            has_iccp = True
            name = data.split(b"\x00", 1)[0]
            icc = zlib.decompress(data[len(name) + 2 :])
            cicp = parse_cicp_from_icc(icc)
        elif typ == b"IEND":
            break

    return width, height, bit_depth, color_type, has_iccp, cicp


def _resize_like(arr: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    pil = Image.fromarray(arr, mode="RGBA")
    return np.array(pil.resize(size, Image.Resampling.LANCZOS), dtype=arr.dtype)


def build_candidates(
    input_path: Path,
    success_ref: Path,
    outdir: Path,
    *,
    extended: bool,
) -> list[CandidateResult]:
    img = Image.open(input_path).convert("RGBA").resize((400, 400), Image.Resampling.LANCZOS)
    arr8_rgba = np.array(img, dtype=np.uint8)
    arr16_rgba = arr8_rgba.astype(np.uint16) * 257

    icc_success = extract_icc_from_png(success_ref)

    text = {
        "generator": "scripts/make_candidates.py",
        "source": str(input_path),
    }

    targets: list[tuple[str, Path, np.ndarray, int, int, bytes | None]] = [
        (
            "success_like",
            outdir / "candidate_success_like.png",
            arr16_rgba,
            16,
            6,
            icc_success,
        ),
        (
            "fail_8bit",
            outdir / "candidate_fail_8bit.png",
            arr8_rgba,
            8,
            6,
            icc_success,
        ),
        (
            "fail_no_iccp",
            outdir / "candidate_fail_no_iccp.png",
            arr16_rgba,
            16,
            6,
            None,
        ),
        (
            "fail_rgb_no_alpha",
            outdir / "candidate_fail_rgb_no_alpha.png",
            arr16_rgba[:, :, :3],
            16,
            2,
            icc_success,
        ),
    ]

    if extended:
        arr8_rgb = arr8_rgba[:, :, :3]
        arr16_alpha255 = arr16_rgba.copy()
        arr16_alpha255[:, :, 3] = 65535
        arr16_alpha0 = arr16_rgba.copy()
        arr16_alpha0[:, :, 3] = 0
        arr16_alpha1 = arr16_rgba.copy()
        arr16_alpha1[:, :, 3] = 1

        # 左→右に alpha を 1..65535 でグラデーション（0は使わない）
        arr16_alpha_grad = arr16_rgba.copy()
        grad = np.linspace(1, 65535, arr16_alpha_grad.shape[1], dtype=np.uint16)
        arr16_alpha_grad[:, :, 3] = grad[np.newaxis, :]

        arr16_rgba_512 = _resize_like(arr16_rgba, (512, 512))
        arr16_rgba_512_alpha255 = arr16_rgba_512.copy()
        arr16_rgba_512_alpha255[:, :, 3] = 65535

        targets.extend(
            [
                (
                    "probe_8bit_rgb_no_alpha",
                    outdir / "candidate_probe_8bit_rgb_no_alpha.png",
                    arr8_rgb,
                    8,
                    2,
                    icc_success,
                ),
                (
                    "probe_alpha_255",
                    outdir / "candidate_probe_alpha_255.png",
                    arr16_alpha255,
                    16,
                    6,
                    icc_success,
                ),
                (
                    "probe_alpha_0",
                    outdir / "candidate_probe_alpha_0.png",
                    arr16_alpha0,
                    16,
                    6,
                    icc_success,
                ),
                (
                    "probe_alpha_1",
                    outdir / "candidate_probe_alpha_1.png",
                    arr16_alpha1,
                    16,
                    6,
                    icc_success,
                ),
                (
                    "probe_alpha_gradient",
                    outdir / "candidate_probe_alpha_gradient.png",
                    arr16_alpha_grad,
                    16,
                    6,
                    icc_success,
                ),
                (
                    "probe_size_512",
                    outdir / "candidate_probe_size_512.png",
                    arr16_rgba_512,
                    16,
                    6,
                    icc_success,
                ),
                (
                    "probe_size_512_nontransparent",
                    outdir / "candidate_probe_size_512_nontransparent.png",
                    arr16_rgba_512_alpha255,
                    16,
                    6,
                    icc_success,
                ),
            ]
        )

    results: list[CandidateResult] = []
    for name, path, arr, bd, ct, icc in targets:
        write_png(path, arr, bit_depth=bd, color_type=ct, icc_profile=icc, text_entries=text)
        width, height, bit_depth, color_type, has_iccp, cicp = parse_png_meta(path)
        legacy_ok = bit_depth == 16 and color_type == 6 and has_iccp and cicp == TARGET_CICP
        relaxed_ok = has_iccp and cicp == TARGET_CICP
        results.append(
            CandidateResult(
                name=name,
                path=path,
                width=width,
                height=height,
                bit_depth=bit_depth,
                color_type=color_type,
                has_iccp=has_iccp,
                cicp=cicp,
                match_legacy_profile=legacy_ok,
                match_relaxed_profile=relaxed_ok,
            )
        )

    # 参照ICCも保存
    (outdir / "icc_bt2020_pq_from_success.icc").write_bytes(icc_success)

    return results


def write_report(results: list[CandidateResult], path: Path, *, extended: bool) -> None:
    lines = [
        "# Candidate Comparison (auto-generated)",
        "",
        "| name | file | size | bit_depth | color_type | iCCP | cicp | legacy(16bit+RGBA+iCCP/cicp) | relaxed(iCCP/cicp only) |",
        "|---|---|---|---:|---:|---|---|---|---|",
    ]
    for r in results:
        cicp = "-" if r.cicp is None else str(r.cicp)
        lines.append(
            "| "
            f"{r.name} | `{r.path.name}` | {r.width}x{r.height} | {r.bit_depth} | {r.color_type} | "
            f"{'yes' if r.has_iccp else 'no'} | {cicp} | "
            f"{'YES' if r.match_legacy_profile else 'NO'} | {'YES' if r.match_relaxed_profile else 'NO'} |"
        )

    lines.extend(
        [
            "",
            "判定ロジック:",
            "- legacy: `bit_depth=16` かつ `color_type=6(RGBA)` かつ `iCCP.cicp=[9,16,0,1]`",
            "- relaxed: `iCCP.cicp=[9,16,0,1]`（bit depth / alpha / size は不問）",
        ]
    )

    if extended:
        lines.extend(
            [
                "",
                "extended候補の狙い:",
                "- `probe_8bit_rgb_no_alpha`: 8bit と no-alpha を同時適用（2x2切り分けの第4点）",
                "- `probe_alpha_255` / `probe_alpha_0`: alpha=255 と alpha=0 の極端条件を比較",
                "- `probe_alpha_1`: alpha=1固定（完全透明を避けつつ極小alphaを確認）",
                "- `probe_alpha_gradient`: alphaを1..65535で連続変化（alpha=0依存の白化を回避して観測）",
                "- `probe_size_512`: 512化のみ（従来観測の再確認）",
                "- `probe_size_512_nontransparent`: 512 + alpha=255固定（サイズ要因と透明要因の切り分け）",
            ]
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="sample/success_sample.png", help="input image path")
    ap.add_argument(
        "--success-ref",
        default="sample/success_sample.png",
        help="reference success png path (iCCP source)",
    )
    ap.add_argument("--outdir", default="generated", help="output directory")
    ap.add_argument(
        "--extended",
        action="store_true",
        help="generate additional probe candidates that vary non-iCCP/cicp conditions",
    )
    args = ap.parse_args()

    input_path = Path(args.input)
    success_ref = Path(args.success_ref)
    outdir = Path(args.outdir)

    results = build_candidates(
        input_path,
        success_ref,
        outdir,
        extended=args.extended,
    )
    report = outdir / "comparison.md"
    write_report(results, report, extended=args.extended)

    print(f"generated {len(results)} candidates -> {outdir}")
    for r in results:
        print(
            f"- {r.name}: {r.path} "
            f"size={r.width}x{r.height} bd={r.bit_depth} ct={r.color_type} "
            f"iCCP={'yes' if r.has_iccp else 'no'} cicp={r.cicp} "
            f"legacy={'YES' if r.match_legacy_profile else 'NO'} "
            f"relaxed={'YES' if r.match_relaxed_profile else 'NO'}"
        )
    print(f"report: {report}")


if __name__ == "__main__":
    main()
