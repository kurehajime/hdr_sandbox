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


ALPHA_LADDER_VALUES = [1, 2, 4, 8, 16, 24, 32, 48, 64, 96, 128, 192, 255]
LUMA_LADDER_VALUES = [512, 1024, 2048, 4096, 8192, 16384, 24576, 32768, 49152, 65535]
MATRIX_ALPHA_VALUES = [1, 2, 4, 8, 16, 24, 32, 48, 64, 96, 128, 160, 192, 224, 255]
MATRIX_LUMA_VALUES = [512, 1024, 2048, 4096, 8192, 12288, 16384, 24576, 32768, 49152, 65535]
ISOEFF_ALPHA_VALUES = [8, 12, 16, 24, 32, 48, 64, 96, 128, 160, 192, 224, 255]
ISOEFF_EFFECTIVE_LEVELS = [0.06, 0.10, 0.16]
THRESHOLD_ZOOM_ALPHA_VALUES = [12, 16, 20, 24, 28, 32, 40, 48, 56, 64, 80, 96]
THRESHOLD_ZOOM_LUMA_VALUES = [4096, 6144, 8192, 10240, 12288, 14336, 16384, 20480, 24576, 28672, 32768, 40960]


def _make_lr_split_pattern(*, width: int = 400, height: int = 400) -> np.ndarray:
    """左右比較しやすい単純パターン（左=低alpha、右=高alpha）。"""
    arr = np.zeros((height, width, 4), dtype=np.uint16)

    # 背景は低輝度グレー
    arr[:, :, :3] = 1024
    mid = width // 2
    arr[:, :mid, 3] = 16
    arr[:, mid:, 3] = 64

    # 視認しやすいよう、左右に同形状の高輝度パッチを配置
    patch_w = width // 5
    patch_h = height // 5
    y0 = height // 2 - patch_h // 2
    y1 = y0 + patch_h

    x0_l = mid // 2 - patch_w // 2
    x1_l = x0_l + patch_w
    x0_r = mid + (mid // 2) - patch_w // 2
    x1_r = x0_r + patch_w

    arr[y0:y1, x0_l:x1_l, :3] = 65535
    arr[y0:y1, x0_r:x1_r, :3] = 65535

    return arr


def _make_alpha_ladder_pattern(
    *,
    width: int = 400,
    height: int = 400,
    alphas: list[int] | None = None,
) -> np.ndarray:
    """縦バーごとにalphaを段階化し、しきい値境界を1枚で観測しやすくする。"""
    alpha_values = ALPHA_LADDER_VALUES if alphas is None else alphas
    if not alpha_values:
        raise ValueError("alpha_values must not be empty")

    arr = np.zeros((height, width, 4), dtype=np.uint16)
    arr[:, :, :3] = 1024  # 低輝度背景
    arr[:, :, 3] = 65535  # 背景は不透明で固定

    # 観測ターゲットのバーを中央帯に配置（上下は比較用背景）
    y0 = height // 4
    y1 = (height * 3) // 4

    n = len(alpha_values)
    for i, a8 in enumerate(alpha_values):
        x0 = (i * width) // n
        x1 = ((i + 1) * width) // n

        # バー内は高輝度色、alphaのみ段階化
        arr[y0:y1, x0:x1, :3] = 65535
        arr[y0:y1, x0:x1, 3] = np.uint16(a8 * 257)

        # 境界視認性のため縦セパレータを挿入
        if x0 > 0:
            arr[:, x0 - 1 : x0 + 1, :3] = 0
            arr[:, x0 - 1 : x0 + 1, 3] = 65535

    return arr


def _make_luma_ladder_pattern(
    *,
    width: int = 400,
    height: int = 400,
    alpha_8bit: int,
    luma_values: list[int] | None = None,
) -> np.ndarray:
    """縦バーごとにRGB(16bit)を段階化し、実効輝度しきい値を観測する。"""
    values = LUMA_LADDER_VALUES if luma_values is None else luma_values
    if not values:
        raise ValueError("luma_values must not be empty")

    arr = np.zeros((height, width, 4), dtype=np.uint16)
    arr[:, :, :3] = 1024
    arr[:, :, 3] = 65535

    y0 = height // 4
    y1 = (height * 3) // 4
    n = len(values)
    alpha_16 = np.uint16(max(0, min(255, alpha_8bit)) * 257)

    for i, l16 in enumerate(values):
        x0 = (i * width) // n
        x1 = ((i + 1) * width) // n

        lv = np.uint16(max(0, min(65535, l16)))
        arr[y0:y1, x0:x1, 0] = lv
        arr[y0:y1, x0:x1, 1] = lv
        arr[y0:y1, x0:x1, 2] = lv
        arr[y0:y1, x0:x1, 3] = alpha_16

        if x0 > 0:
            arr[:, x0 - 1 : x0 + 1, :3] = 0
            arr[:, x0 - 1 : x0 + 1, 3] = 65535

    return arr


def _make_alpha_luma_matrix_pattern(
    *,
    width: int = 400,
    height: int = 400,
    alpha_values: list[int] | None = None,
    luma_values: list[int] | None = None,
) -> np.ndarray:
    """2Dマトリクス（x=alpha, y=luma）で、しきい値境界を1枚で観測する。"""
    alphas = MATRIX_ALPHA_VALUES if alpha_values is None else alpha_values
    lumas = MATRIX_LUMA_VALUES if luma_values is None else luma_values
    if not alphas:
        raise ValueError("alpha_values must not be empty")
    if not lumas:
        raise ValueError("luma_values must not be empty")

    arr = np.zeros((height, width, 4), dtype=np.uint16)
    arr[:, :, :3] = 1024
    arr[:, :, 3] = 65535

    mx = max(8, width // 40)
    my = max(8, height // 40)
    x0_base = mx
    x1_base = width - mx
    y0_base = my
    y1_base = height - my

    cols = len(alphas)
    rows = len(lumas)

    for r, l16 in enumerate(lumas):
        y0 = y0_base + (r * (y1_base - y0_base)) // rows
        y1 = y0_base + ((r + 1) * (y1_base - y0_base)) // rows
        lv = np.uint16(max(0, min(65535, l16)))

        for c, a8 in enumerate(alphas):
            x0 = x0_base + (c * (x1_base - x0_base)) // cols
            x1 = x0_base + ((c + 1) * (x1_base - x0_base)) // cols

            arr[y0:y1, x0:x1, 0] = lv
            arr[y0:y1, x0:x1, 1] = lv
            arr[y0:y1, x0:x1, 2] = lv
            arr[y0:y1, x0:x1, 3] = np.uint16(max(0, min(255, a8)) * 257)

    for c in range(1, cols):
        x = x0_base + (c * (x1_base - x0_base)) // cols
        arr[y0_base:y1_base, max(0, x - 1) : min(width, x + 1), :3] = 0
        arr[y0_base:y1_base, max(0, x - 1) : min(width, x + 1), 3] = 65535

    for r in range(1, rows):
        y = y0_base + (r * (y1_base - y0_base)) // rows
        arr[max(0, y - 1) : min(height, y + 1), x0_base:x1_base, :3] = 0
        arr[max(0, y - 1) : min(height, y + 1), x0_base:x1_base, 3] = 65535

    return arr


def _make_isoeff_triplet_pattern(
    *,
    width: int = 400,
    height: int = 400,
    alpha_values: list[int] | None = None,
    effective_levels: list[float] | None = None,
) -> tuple[np.ndarray, list[dict[str, object]]]:
    """alphaごとにlumaを逆算し、effective一定帯を3段で観測する。"""
    alphas = ISOEFF_ALPHA_VALUES if alpha_values is None else alpha_values
    levels = ISOEFF_EFFECTIVE_LEVELS if effective_levels is None else effective_levels
    if not alphas:
        raise ValueError("alpha_values must not be empty")
    if not levels:
        raise ValueError("effective_levels must not be empty")

    arr = np.zeros((height, width, 4), dtype=np.uint16)
    arr[:, :, :3] = 1024
    arr[:, :, 3] = 65535

    y_margin = max(8, height // 20)
    x_margin = max(8, width // 30)
    y0_base = y_margin
    y1_base = height - y_margin
    x0_base = x_margin
    x1_base = width - x_margin

    rows = len(levels)
    cols = len(alphas)
    spec_rows: list[dict[str, object]] = []

    for r, eff in enumerate(levels):
        y0 = y0_base + (r * (y1_base - y0_base)) // rows
        y1 = y0_base + ((r + 1) * (y1_base - y0_base)) // rows

        row_cells: list[dict[str, float]] = []
        for c, a8 in enumerate(alphas):
            x0 = x0_base + (c * (x1_base - x0_base)) // cols
            x1 = x0_base + ((c + 1) * (x1_base - x0_base)) // cols

            a_norm = max(1 / 255, min(1.0, a8 / 255))
            luma_norm = min(1.0, eff / a_norm)
            l16 = int(round(luma_norm * 65535))
            a16 = int(round(a8 * 257))

            arr[y0:y1, x0:x1, 0] = l16
            arr[y0:y1, x0:x1, 1] = l16
            arr[y0:y1, x0:x1, 2] = l16
            arr[y0:y1, x0:x1, 3] = a16

            row_cells.append(
                {
                    "alpha_8bit": int(a8),
                    "alpha_norm": a_norm,
                    "luma_16bit": int(l16),
                    "luma_norm": luma_norm,
                    "effective": a_norm * luma_norm,
                }
            )

        spec_rows.append({"target_effective": float(eff), "cells": row_cells})

    for c in range(1, cols):
        x = x0_base + (c * (x1_base - x0_base)) // cols
        arr[y0_base:y1_base, max(0, x - 1) : min(width, x + 1), :3] = 0
        arr[y0_base:y1_base, max(0, x - 1) : min(width, x + 1), 3] = 65535

    for r in range(1, rows):
        y = y0_base + (r * (y1_base - y0_base)) // rows
        arr[max(0, y - 1) : min(height, y + 1), x0_base:x1_base, :3] = 0
        arr[max(0, y - 1) : min(height, y + 1), x0_base:x1_base, 3] = 65535

    return arr, spec_rows


def _make_threshold_zoom_matrix_pattern(
    *,
    width: int = 400,
    height: int = 400,
    alpha_values: list[int] | None = None,
    luma_values: list[int] | None = None,
) -> np.ndarray:
    """しきい値近傍を高密度サンプリングする2Dマトリクス（x=alpha, y=luma）。"""
    alphas = THRESHOLD_ZOOM_ALPHA_VALUES if alpha_values is None else alpha_values
    lumas = THRESHOLD_ZOOM_LUMA_VALUES if luma_values is None else luma_values
    if not alphas:
        raise ValueError("alpha_values must not be empty")
    if not lumas:
        raise ValueError("luma_values must not be empty")

    arr = np.zeros((height, width, 4), dtype=np.uint16)
    arr[:, :, :3] = 1024
    arr[:, :, 3] = 65535

    mx = max(8, width // 40)
    my = max(8, height // 40)
    x0_base = mx
    x1_base = width - mx
    y0_base = my
    y1_base = height - my

    cols = len(alphas)
    rows = len(lumas)

    for r, l16 in enumerate(lumas):
        y0 = y0_base + (r * (y1_base - y0_base)) // rows
        y1 = y0_base + ((r + 1) * (y1_base - y0_base)) // rows
        lv = np.uint16(max(0, min(65535, l16)))

        for c, a8 in enumerate(alphas):
            x0 = x0_base + (c * (x1_base - x0_base)) // cols
            x1 = x0_base + ((c + 1) * (x1_base - x0_base)) // cols

            arr[y0:y1, x0:x1, 0] = lv
            arr[y0:y1, x0:x1, 1] = lv
            arr[y0:y1, x0:x1, 2] = lv
            arr[y0:y1, x0:x1, 3] = np.uint16(max(0, min(255, a8)) * 257)

    for c in range(1, cols):
        x = x0_base + (c * (x1_base - x0_base)) // cols
        arr[y0_base:y1_base, max(0, x - 1) : min(width, x + 1), :3] = 0
        arr[y0_base:y1_base, max(0, x - 1) : min(width, x + 1), 3] = 65535

    for r in range(1, rows):
        y = y0_base + (r * (y1_base - y0_base)) // rows
        arr[max(0, y - 1) : min(height, y + 1), x0_base:x1_base, :3] = 0
        arr[max(0, y - 1) : min(height, y + 1), x0_base:x1_base, 3] = 65535

    return arr


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
        arr16_alpha16 = arr16_rgba.copy()
        arr16_alpha16[:, :, 3] = 16
        arr16_alpha64 = arr16_rgba.copy()
        arr16_alpha64[:, :, 3] = 64

        # 左→右に alpha を 1..65535 でグラデーション（0は使わない）
        arr16_alpha_grad = arr16_rgba.copy()
        grad = np.linspace(1, 65535, arr16_alpha_grad.shape[1], dtype=np.uint16)
        arr16_alpha_grad[:, :, 3] = grad[np.newaxis, :]

        arr16_rgba_512 = _resize_like(arr16_rgba, (512, 512))
        arr16_rgba_512_alpha255 = arr16_rgba_512.copy()
        arr16_rgba_512_alpha255[:, :, 3] = 65535

        arr16_rgba_512_bright_patch = arr16_rgba_512_alpha255.copy()
        h512, w512, _ = arr16_rgba_512_bright_patch.shape
        patch = max(64, min(w512, h512) // 4)
        y0 = h512 // 2 - patch // 2
        y1 = y0 + patch
        x0 = (w512 * 3) // 4 - patch // 2
        x1 = x0 + patch
        arr16_rgba_512_bright_patch[y0:y1, x0:x1, :3] = 65535

        arr16_lr_split = _make_lr_split_pattern(width=400, height=400)
        arr16_alpha_ladder = _make_alpha_ladder_pattern(width=400, height=400)
        arr16_luma_ladder_alpha255 = _make_luma_ladder_pattern(width=400, height=400, alpha_8bit=255)
        arr16_luma_ladder_alpha64 = _make_luma_ladder_pattern(width=400, height=400, alpha_8bit=64)
        arr16_alpha_luma_matrix = _make_alpha_luma_matrix_pattern(width=400, height=400)
        arr16_isoeff_triplet, isoeff_spec_rows = _make_isoeff_triplet_pattern(width=400, height=400)
        arr16_threshold_zoom_matrix = _make_threshold_zoom_matrix_pattern(width=400, height=400)

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
                    "probe_alpha_16",
                    outdir / "candidate_probe_alpha_16.png",
                    arr16_alpha16,
                    16,
                    6,
                    icc_success,
                ),
                (
                    "probe_alpha_64",
                    outdir / "candidate_probe_alpha_64.png",
                    arr16_alpha64,
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
                    "probe_alpha_lr_split_16_64",
                    outdir / "candidate_probe_alpha_lr_split_16_64.png",
                    arr16_lr_split,
                    16,
                    6,
                    icc_success,
                ),
                (
                    "probe_alpha_ladder_1_255",
                    outdir / "candidate_probe_alpha_ladder_1_255.png",
                    arr16_alpha_ladder,
                    16,
                    6,
                    icc_success,
                ),
                (
                    "probe_luma_ladder_alpha255",
                    outdir / "candidate_probe_luma_ladder_alpha255.png",
                    arr16_luma_ladder_alpha255,
                    16,
                    6,
                    icc_success,
                ),
                (
                    "probe_luma_ladder_alpha64",
                    outdir / "candidate_probe_luma_ladder_alpha64.png",
                    arr16_luma_ladder_alpha64,
                    16,
                    6,
                    icc_success,
                ),
                (
                    "probe_alpha_luma_matrix",
                    outdir / "candidate_probe_alpha_luma_matrix.png",
                    arr16_alpha_luma_matrix,
                    16,
                    6,
                    icc_success,
                ),
                (
                    "probe_isoeff_triplet",
                    outdir / "candidate_probe_isoeff_triplet.png",
                    arr16_isoeff_triplet,
                    16,
                    6,
                    icc_success,
                ),
                (
                    "probe_threshold_zoom_matrix",
                    outdir / "candidate_probe_threshold_zoom_matrix.png",
                    arr16_threshold_zoom_matrix,
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
                (
                    "probe_size_512_alpha255_bright_patch",
                    outdir / "candidate_probe_size_512_alpha255_bright_patch.png",
                    arr16_rgba_512_bright_patch,
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

    if extended:
        ladder_lines = [
            "# Alpha Ladder Spec (auto-generated)",
            "",
            "`candidate_probe_alpha_ladder_1_255.png` の中央帯は左→右で以下の alpha(8bit) を使用:",
            "",
            "| lane | alpha_8bit | alpha_16bit | normalized |",
            "|---:|---:|---:|---:|",
        ]
        for i, a8 in enumerate(ALPHA_LADDER_VALUES, start=1):
            a16 = a8 * 257
            ladder_lines.append(f"| {i} | {a8} | {a16} | {a8 / 255:.4f} |")
        ladder_lines.extend(
            [
                "",
                "観測ポイント:",
                "- どのlaneから『光って見える』か（発光しきい値）",
                "- しきい値近傍で白化/黒化/通常表示のどれが起きるか",
            ]
        )
        (outdir / "alpha_ladder_spec.md").write_text("\n".join(ladder_lines), encoding="utf-8")

        luma_lines = [
            "# Luma Ladder Spec (auto-generated)",
            "",
            "`candidate_probe_luma_ladder_alpha255.png` と `candidate_probe_luma_ladder_alpha64.png` の中央帯は左→右で以下の RGB(16bit) を使用:",
            "",
            "| lane | rgb_16bit | normalized | effective(alpha=255) | effective(alpha=64) |",
            "|---:|---:|---:|---:|---:|",
        ]
        for i, l16 in enumerate(LUMA_LADDER_VALUES, start=1):
            norm = l16 / 65535
            luma_lines.append(
                f"| {i} | {l16} | {norm:.4f} | {norm * 1.0:.4f} | {norm * (64 / 255):.4f} |"
            )
        luma_lines.extend(
            [
                "",
                "観測ポイント:",
                "- alpha固定時に、どのlaneから『光って見える』か（実効輝度しきい値）",
                "- alpha=255 と alpha=64 で、しきい値laneがどれだけ右にずれるか",
            ]
        )
        (outdir / "luma_ladder_spec.md").write_text("\n".join(luma_lines), encoding="utf-8")

        matrix_lines = [
            "# Alpha×Luma Matrix Spec (auto-generated)",
            "",
            "`candidate_probe_alpha_luma_matrix.png` は 2D グリッドで、",
            "- 列(x): alpha(8bit)",
            "- 行(y): RGB luma(16bit)",
            "を同時に段階化しています。",
            "",
            "仮説:",
            "- 光って見える境界は `effective ≈ (alpha/255) * (luma/65535)` の等高線に近く、",
            "  画像上で左下→右上方向の境界として現れる。",
            "",
            "## Columns (x=alpha)",
            "",
            "| col | alpha_8bit | alpha_16bit | alpha_norm |",
            "|---:|---:|---:|---:|",
        ]
        for i, a8 in enumerate(MATRIX_ALPHA_VALUES, start=1):
            matrix_lines.append(f"| {i} | {a8} | {a8 * 257} | {a8 / 255:.4f} |")

        matrix_lines.extend(
            [
                "",
                "## Rows (y=luma)",
                "",
                "| row | luma_16bit | luma_norm |",
                "|---:|---:|---:|",
            ]
        )
        for i, l16 in enumerate(MATRIX_LUMA_VALUES, start=1):
            matrix_lines.append(f"| {i} | {l16} | {l16 / 65535:.4f} |")

        matrix_lines.extend(
            [
                "",
                "## 観測ポイント",
                "- 光る/光らない境界セルを手でなぞり、境界の傾き（alpha寄りかluma寄りか）を判定する",
                "- 境界が急に折れ曲がる位置があれば、単純な積モデル以外の非線形要因を疑う",
            ]
        )
        (outdir / "alpha_luma_matrix_spec.md").write_text("\n".join(matrix_lines), encoding="utf-8")

        isoeff_lines = [
            "# Iso-effective Triplet Spec (auto-generated)",
            "",
            "`candidate_probe_isoeff_triplet.png` は列方向にalphaを変えつつ、",
            "各行帯で `effective=(alpha/255)*(luma/65535)` の目標値を固定したプローブです。",
            "",
            "期待される見え方:",
            "- もし積モデルが優勢なら、各行帯は列方向にほぼ均一な見え方になる",
            "- 逆にalpha固有の非線形要因が強い場合、同一行でも左右で見え方が崩れる",
            "",
        ]
        for row_idx, row in enumerate(isoeff_spec_rows, start=1):
            target_eff = float(row["target_effective"])
            isoeff_lines.extend(
                [
                    f"## Row {row_idx} (target effective={target_eff:.4f})",
                    "",
                    "| col | alpha_8bit | alpha_norm | luma_16bit | luma_norm | achieved_effective |",
                    "|---:|---:|---:|---:|---:|---:|",
                ]
            )
            for col_idx, cell in enumerate(row["cells"], start=1):
                isoeff_lines.append(
                    "| "
                    f"{col_idx} | {cell['alpha_8bit']} | {cell['alpha_norm']:.4f} | "
                    f"{cell['luma_16bit']} | {cell['luma_norm']:.4f} | {cell['effective']:.4f} |"
                )
            isoeff_lines.append("")
        (outdir / "isoeff_triplet_spec.md").write_text("\n".join(isoeff_lines), encoding="utf-8")

        threshold_lines = [
            "# Threshold Zoom Matrix Spec (auto-generated)",
            "",
            "`candidate_probe_threshold_zoom_matrix.png` は、",
            "既存観測（alphaラダーで概ね alpha≈24 付近から変化）を踏まえ、",
            "しきい値近傍を高密度サンプリングする2Dマトリクスです。",
            "",
            "- 列(x): alpha(8bit) = 12..96 の密サンプル",
            "- 行(y): RGB luma(16bit) = 4096..40960 の密サンプル",
            "",
            "## Columns (x=alpha)",
            "",
            "| col | alpha_8bit | alpha_16bit | alpha_norm |",
            "|---:|---:|---:|---:|",
        ]
        for i, a8 in enumerate(THRESHOLD_ZOOM_ALPHA_VALUES, start=1):
            threshold_lines.append(f"| {i} | {a8} | {a8 * 257} | {a8 / 255:.4f} |")

        threshold_lines.extend(
            [
                "",
                "## Rows (y=luma)",
                "",
                "| row | luma_16bit | luma_norm |",
                "|---:|---:|---:|",
            ]
        )
        for i, l16 in enumerate(THRESHOLD_ZOOM_LUMA_VALUES, start=1):
            threshold_lines.append(f"| {i} | {l16} | {l16 / 65535:.4f} |")

        threshold_lines.extend(
            [
                "",
                "## 観測ポイント",
                "- 2D境界が緩やかな斜線になるか（積モデル優勢）",
                "- alpha≈24 近傍で境界の折れ曲がりや段差が出るか（alpha固有非線形の兆候）",
                "- 既存 `alpha_luma_matrix` より境界追跡の再現性が上がるか",
            ]
        )
        (outdir / "threshold_zoom_matrix_spec.md").write_text("\n".join(threshold_lines), encoding="utf-8")

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
                "- `probe_alpha_1` / `probe_alpha_16` / `probe_alpha_64`: 極小alpha域の表示しきい値を探索",
                "- `probe_alpha_gradient`: alphaを1..65535で連続変化（alpha依存の境界を観測）",
                "- `probe_alpha_lr_split_16_64`: 左右分割（左alpha=16 / 右alpha=64）で見え方を即比較",
                "- `probe_alpha_ladder_1_255`: alpha段階(1..255)の縦バーで発光しきい値の概算を1枚で観測",
                "- `probe_luma_ladder_alpha255` / `probe_luma_ladder_alpha64`: RGB段階バー（alpha固定）で実効輝度しきい値を探索",
                "- `probe_alpha_luma_matrix`: 2Dグリッド（x=alpha, y=luma）でしきい値境界形状を1枚で観測",
                "- `probe_isoeff_triplet`: 3行帯で目標effectiveを固定し、列方向alpha変化に対する均一性を検証",
                "- `probe_threshold_zoom_matrix`: alpha/lumaの境界近傍を高密度サンプリングし、境界線を細かく追跡",
                "- `probe_size_512`: 512化のみ（従来観測の再確認）",
                "- `probe_size_512_nontransparent`: 512 + alpha=255固定（サイズ要因と透明要因の切り分け）",
                "- `probe_size_512_alpha255_bright_patch`: 512 + alpha=255 + 右側高輝度パッチ（実効輝度しきい値を確認）",
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
