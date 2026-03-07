#!/usr/bin/env python3
"""
PNGのHDR関連メタを簡易チェックするツール。

Usage:
  python3 scripts/check_png_hdr.py path/to/image.png
"""

from __future__ import annotations
import argparse
import struct
import sys
import zlib


def parse_png(path: str):
    b = open(path, "rb").read()
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Not a PNG")

    o = 8
    out = {
        "path": path,
        "size_bytes": len(b),
        "width": None,
        "height": None,
        "bit_depth": None,
        "color_type": None,
        "has_iccp": False,
        "icc_name": None,
        "icc_size": 0,
        "icc_has_cicp": False,
        "cicp": None,
        "texts": [],
    }

    while o < len(b):
        ln = struct.unpack(">I", b[o:o+4])[0]
        o += 4
        typ = b[o:o+4]
        o += 4
        data = b[o:o+ln]
        o += ln
        _crc = b[o:o+4]
        o += 4

        if typ == b"IHDR":
            w, h, bd, ct, _cm, _fm, _im = struct.unpack(">IIBBBBB", data)
            out["width"], out["height"] = w, h
            out["bit_depth"], out["color_type"] = bd, ct

        elif typ == b"iCCP":
            out["has_iccp"] = True
            name = data.split(b"\x00", 1)[0]
            out["icc_name"] = name.decode("latin1", "ignore")
            prof = zlib.decompress(data[len(name)+2:])
            out["icc_size"] = len(prof)

            # ICC tag table: starts at offset 128
            if len(prof) >= 132:
                tag_count = struct.unpack(">I", prof[128:132])[0]
                for i in range(tag_count):
                    off = 132 + i * 12
                    if off + 12 > len(prof):
                        break
                    sig = prof[off:off+4]
                    to, sz = struct.unpack(">II", prof[off+4:off+12])
                    if sig.lower() == b"cicp" and to + sz <= len(prof):
                        d = prof[to:to+sz]
                        if len(d) >= 12:
                            out["icc_has_cicp"] = True
                            # cicp type(4) + reserved(4) + 4 bytes payload
                            out["cicp"] = list(d[8:12])

        elif typ == b"tEXt":
            if b"\x00" in data:
                k, v = data.split(b"\x00", 1)
                out["texts"].append((k.decode("latin1", "ignore"), v.decode("latin1", "ignore")))

        elif typ == b"IEND":
            break

    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("png")
    args = ap.parse_args()

    info = parse_png(args.png)

    print(f"file: {info['path']}")
    print(f"size: {info['size_bytes']} bytes")
    print(f"IHDR: {info['width']}x{info['height']} bit_depth={info['bit_depth']} color_type={info['color_type']}")
    print(f"iCCP: {'yes' if info['has_iccp'] else 'no'}")
    if info["has_iccp"]:
        print(f"  profile_name: {info['icc_name']}")
        print(f"  profile_size: {info['icc_size']} bytes")
        print(f"  cicp_tag: {'yes' if info['icc_has_cicp'] else 'no'}")
        if info["cicp"]:
            p, t, m, r = info["cicp"]
            print(f"  cicp_values: primaries={p}, transfer={t}, matrix={m}, range={r}")

    if info["texts"]:
        print("tEXt:")
        for k, v in info["texts"]:
            print(f"  {k}: {v}")

    # 目標プロファイル判定（今回の成功例ベース）
    ok = (
        info["bit_depth"] == 16
        and info["color_type"] == 6
        and info["icc_has_cicp"]
        and info["cicp"] == [9, 16, 0, 1]
    )
    print(f"match_target_profile: {'YES' if ok else 'NO'}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
