import { promises as fs } from "node:fs";
import path from "node:path";

import {
  buildMinimalPatternRgba16,
  encodeRgba16Png,
  extractIccFromPngBytes,
} from "./core.mjs";

const MUL_DIV_255_WASM_BYTES = new Uint8Array([
  0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00,
  0x01, 0x07, 0x01, 0x60, 0x02, 0x7f, 0x7f, 0x01, 0x7f,
  0x03, 0x02, 0x01, 0x00,
  0x07, 0x0d, 0x01, 0x09, 0x6d, 0x75, 0x6c, 0x44, 0x69, 0x76, 0x32, 0x35, 0x35, 0x00, 0x00,
  0x0a, 0x0d, 0x01, 0x0b, 0x00, 0x20, 0x00, 0x20, 0x01, 0x6c, 0x41, 0xff, 0x01, 0x6e, 0x0b,
]);

function clampInt(v, min, max, label) {
  const n = Number(v);
  if (!Number.isFinite(n)) {
    throw new Error(`${label} must be finite number`);
  }
  return Math.min(max, Math.max(min, Math.trunc(n)));
}

function jsMulDiv255(a, b) {
  return Math.floor(((a >>> 0) * (b >>> 0)) / 255) >>> 0;
}

export async function extractIccFromPng(pngPath) {
  const bytes = await fs.readFile(pngPath);
  return extractIccFromPngBytes(bytes, pngPath);
}

async function loadMulDiv255({ forceJsFallback = false } = {}) {
  if (forceJsFallback) {
    return {
      mode: "js-fallback-forced",
      mulDiv255: jsMulDiv255,
    };
  }

  try {
    const { instance } = await WebAssembly.instantiate(MUL_DIV_255_WASM_BYTES);
    if (typeof instance.exports.mulDiv255 !== "function") {
      throw new Error("mulDiv255 export missing");
    }
    return {
      mode: "wasm",
      mulDiv255: (a, b) => instance.exports.mulDiv255(a >>> 0, b >>> 0) >>> 0,
    };
  } catch (_err) {
    return {
      mode: "js-fallback",
      mulDiv255: jsMulDiv255,
    };
  }
}

async function resolveIccProfile({ successRef, iccFallbackPath = "", allowNoIccFallback = false }) {
  try {
    return {
      profile: await extractIccFromPng(successRef),
      source: `success-ref:${successRef}`,
    };
  } catch (err) {
    if (iccFallbackPath) {
      try {
        return {
          profile: await fs.readFile(iccFallbackPath),
          source: `icc-fallback:${iccFallbackPath}`,
          warning: `extract_iCCP_failed:${err.message}`,
        };
      } catch (fallbackErr) {
        if (allowNoIccFallback) {
          return {
            profile: null,
            source: "none",
            warning: `extract_iCCP_failed:${err.message};icc_fallback_failed:${fallbackErr.message}`,
          };
        }
        throw new Error(`iCCP extraction failed (${err.message}) and icc fallback read failed (${fallbackErr.message})`);
      }
    }

    if (allowNoIccFallback) {
      return {
        profile: null,
        source: "none",
        warning: `extract_iCCP_failed:${err.message}`,
      };
    }

    throw err;
  }
}

export async function writeRgba16Png({ outPath, width, height, rgba16be, iccProfile }) {
  const png = encodeRgba16Png({
    width,
    height,
    rgba16be,
    iccProfileBytes: iccProfile,
  });

  await fs.mkdir(path.dirname(outPath), { recursive: true });
  await fs.writeFile(outPath, png);
}

export async function runMinimalPipeline({
  successRef,
  outdir,
  width = 400,
  height = 400,
  alpha8Patch = 64,
  iccFallbackPath = "generated/icc_bt2020_pq_from_success.icc",
  allowNoIccFallback = false,
  forceJsFallback = false,
}) {
  const w = clampInt(width, 16, 4096, "width");
  const h = clampInt(height, 16, 4096, "height");
  const a8 = clampInt(alpha8Patch, 0, 255, "alpha8Patch");

  const iccResolved = await resolveIccProfile({ successRef, iccFallbackPath, allowNoIccFallback });
  const op = await loadMulDiv255({ forceJsFallback });
  const pattern = buildMinimalPatternRgba16({ width: w, height: h, alpha8Patch: a8, mulDiv255: op.mulDiv255 });

  const successPath = path.join(outdir, "candidate_success_like.png");
  const noIccPath = path.join(outdir, "candidate_fail_no_iccp.png");

  let fallbackUsed = false;
  try {
    await writeRgba16Png({
      outPath: successPath,
      width: pattern.width,
      height: pattern.height,
      rgba16be: pattern.rgba16be,
      iccProfile: iccResolved.profile,
    });
  } catch (err) {
    fallbackUsed = true;
    await writeRgba16Png({
      outPath: successPath,
      width: pattern.width,
      height: pattern.height,
      rgba16be: pattern.rgba16be,
      iccProfile: null,
    });
    iccResolved.warning = iccResolved.warning
      ? `${iccResolved.warning};embed_iCCP_failed:${err.message}`
      : `embed_iCCP_failed:${err.message}`;
    iccResolved.source = "none";
  }

  await writeRgba16Png({
    outPath: noIccPath,
    width: pattern.width,
    height: pattern.height,
    rgba16be: pattern.rgba16be,
    iccProfile: null,
  });

  return {
    wasmMode: op.mode,
    iccSource: iccResolved.source,
    warning: iccResolved.warning,
    fallbackUsed,
    generated: [successPath, noIccPath],
  };
}
