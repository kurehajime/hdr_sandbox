import {
  buildMinimalPatternRgba16,
  encodeRgba16Png,
  extractIccFromPngBytes,
  getIhdrSummary,
  hasIccProfile,
  stripIccProfileFromPngBytes,
  upsertIccProfileToPngBytes,
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

function resolveIccProfileFromBytes({
  successRefPngBytes,
  iccFallbackBytes = null,
  allowNoIccFallback = false,
}) {
  try {
    return {
      profile: extractIccFromPngBytes(successRefPngBytes, "successRefPngBytes"),
      source: "success-ref-bytes",
    };
  } catch (err) {
    if (iccFallbackBytes && iccFallbackBytes.length > 0) {
      return {
        profile: iccFallbackBytes,
        source: "icc-fallback-bytes",
        warning: `extract_iCCP_failed:${err.message}`,
      };
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

export async function generateMinimalCandidates({
  inputPngBytes = null,
  successRefPngBytes,
  iccFallbackBytes = null,
  width = 400,
  height = 400,
  alpha8Patch = 64,
  mode = "pass-through",
  allowNoIccFallback = false,
  forceJsFallback = false,
}) {
  if (!(successRefPngBytes instanceof Uint8Array)) {
    throw new Error("successRefPngBytes must be Uint8Array");
  }
  if (!(typeof mode === "string")) {
    throw new Error("mode must be string");
  }

  if (mode === "pass-through") {
    if (!(inputPngBytes instanceof Uint8Array)) {
      throw new Error("inputPngBytes must be Uint8Array in pass-through mode");
    }

    const ihdr = getIhdrSummary(inputPngBytes, "inputPngBytes");
    if (ihdr.bitDepth !== 16 || ihdr.colorType !== 6) {
      throw new Error(`pass-through mode requires RGBA16 PNG input (bitDepth=16,colorType=6), got bitDepth=${ihdr.bitDepth},colorType=${ihdr.colorType}`);
    }

    const iccResolved = resolveIccProfileFromBytes({
      successRefPngBytes,
      iccFallbackBytes,
      allowNoIccFallback,
    });

    let successPngBytes = inputPngBytes;
    let fallbackUsed = false;
    if (!hasIccProfile(inputPngBytes, "inputPngBytes")) {
      if (iccResolved.profile) {
        try {
          successPngBytes = upsertIccProfileToPngBytes(inputPngBytes, iccResolved.profile, "inputPngBytes");
        } catch (err) {
          if (!allowNoIccFallback) throw err;
          fallbackUsed = true;
          iccResolved.warning = iccResolved.warning
            ? `${iccResolved.warning};embed_iCCP_failed:${err.message}`
            : `embed_iCCP_failed:${err.message}`;
          iccResolved.source = "none";
        }
      } else if (!allowNoIccFallback) {
        throw new Error("ICC profile unavailable");
      }
    } else {
      iccResolved.source = "input-png";
    }

    const failNoIccPngBytes = stripIccProfileFromPngBytes(successPngBytes, "successPngBytes");
    return {
      wasmMode: "pass-through",
      iccSource: iccResolved.source,
      warning: iccResolved.warning,
      fallbackUsed,
      files: {
        "candidate_success_like.png": successPngBytes,
        "candidate_fail_no_iccp.png": failNoIccPngBytes,
      },
    };
  }

  if (mode !== "minimal-pattern") {
    throw new Error(`unknown mode: ${mode}`);
  }

  const w = clampInt(width, 16, 4096, "width");
  const h = clampInt(height, 16, 4096, "height");
  const a8 = clampInt(alpha8Patch, 0, 255, "alpha8Patch");

  const iccResolved = resolveIccProfileFromBytes({
    successRefPngBytes,
    iccFallbackBytes,
    allowNoIccFallback,
  });
  const op = await loadMulDiv255({ forceJsFallback });
  const pattern = buildMinimalPatternRgba16({ width: w, height: h, alpha8Patch: a8, mulDiv255: op.mulDiv255 });

  let successPngBytes;
  let fallbackUsed = false;
  try {
    successPngBytes = encodeRgba16Png({
      width: pattern.width,
      height: pattern.height,
      rgba16be: pattern.rgba16be,
      iccProfileBytes: iccResolved.profile,
    });
  } catch (err) {
    fallbackUsed = true;
    successPngBytes = encodeRgba16Png({
      width: pattern.width,
      height: pattern.height,
      rgba16be: pattern.rgba16be,
      iccProfileBytes: null,
    });
    iccResolved.warning = iccResolved.warning
      ? `${iccResolved.warning};embed_iCCP_failed:${err.message}`
      : `embed_iCCP_failed:${err.message}`;
    iccResolved.source = "none";
  }

  const failNoIccPngBytes = encodeRgba16Png({
    width: pattern.width,
    height: pattern.height,
    rgba16be: pattern.rgba16be,
    iccProfileBytes: null,
  });

  return {
    wasmMode: op.mode,
    iccSource: iccResolved.source,
    warning: iccResolved.warning,
    fallbackUsed,
    files: {
      "candidate_success_like.png": successPngBytes,
      "candidate_fail_no_iccp.png": failNoIccPngBytes,
    },
  };
}
