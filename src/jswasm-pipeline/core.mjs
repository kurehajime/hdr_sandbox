import { deflate, inflate } from "pako";

export const PNG_SIG = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

const IHDR_LEN = 13;

function readU32BE(bytes, offset) {
  return (
    ((bytes[offset] << 24) >>> 0)
    | (bytes[offset + 1] << 16)
    | (bytes[offset + 2] << 8)
    | bytes[offset + 3]
  ) >>> 0;
}

function writeU32BE(bytes, offset, value) {
  bytes[offset] = (value >>> 24) & 0xff;
  bytes[offset + 1] = (value >>> 16) & 0xff;
  bytes[offset + 2] = (value >>> 8) & 0xff;
  bytes[offset + 3] = value & 0xff;
}

function asciiBytes(text) {
  const out = new Uint8Array(text.length);
  for (let i = 0; i < text.length; i += 1) out[i] = text.charCodeAt(i) & 0xff;
  return out;
}

function concatBytes(parts) {
  const len = parts.reduce((acc, p) => acc + p.length, 0);
  const out = new Uint8Array(len);
  let offset = 0;
  for (const part of parts) {
    out.set(part, offset);
    offset += part.length;
  }
  return out;
}

function crc32(bytes) {
  let c = 0xffffffff;
  for (let i = 0; i < bytes.length; i += 1) {
    c ^= bytes[i];
    for (let j = 0; j < 8; j += 1) {
      c = (c >>> 1) ^ (0xedb88320 & -(c & 1));
    }
  }
  return (c ^ 0xffffffff) >>> 0;
}

function chunk(type, data) {
  const typeBytes = asciiBytes(type);
  const len = new Uint8Array(4);
  writeU32BE(len, 0, data.length >>> 0);

  const crcInput = concatBytes([typeBytes, data]);
  const crcValue = crc32(crcInput);
  const crc = new Uint8Array(4);
  writeU32BE(crc, 0, crcValue);

  return concatBytes([len, typeBytes, data, crc]);
}

function expectPng(pngBytes, label = "png") {
  if (pngBytes.length < PNG_SIG.length) {
    throw new Error(`${label}: too short`);
  }
  for (let i = 0; i < PNG_SIG.length; i += 1) {
    if (pngBytes[i] !== PNG_SIG[i]) {
      throw new Error(`${label}: invalid signature`);
    }
  }
}

export function parsePngChunks(pngBytes, label = "png") {
  expectPng(pngBytes, label);
  const chunks = [];

  let offset = PNG_SIG.length;
  while (offset + 8 <= pngBytes.length) {
    const length = readU32BE(pngBytes, offset);
    offset += 4;

    const type = String.fromCharCode(
      pngBytes[offset],
      pngBytes[offset + 1],
      pngBytes[offset + 2],
      pngBytes[offset + 3],
    );
    offset += 4;

    if (offset + length + 4 > pngBytes.length) {
      throw new Error(`${label}: corrupted chunk ${type}`);
    }

    const data = pngBytes.subarray(offset, offset + length);
    offset += length;

    const crc = readU32BE(pngBytes, offset);
    offset += 4;

    chunks.push({ type, data, crc });
    if (type === "IEND") break;
  }

  return chunks;
}

export function getIhdrSummary(pngBytes, label = "png") {
  const chunks = parsePngChunks(pngBytes, label);
  const ihdr = chunks.find((c) => c.type === "IHDR");
  if (!ihdr || ihdr.data.length !== IHDR_LEN) {
    throw new Error(`${label}: IHDR missing or invalid`);
  }
  return {
    width: readU32BE(ihdr.data, 0),
    height: readU32BE(ihdr.data, 4),
    bitDepth: ihdr.data[8],
    colorType: ihdr.data[9],
    compressionMethod: ihdr.data[10],
    filterMethod: ihdr.data[11],
    interlaceMethod: ihdr.data[12],
  };
}

export function extractIccFromPngBytes(pngBytes, label = "png") {
  const chunks = parsePngChunks(pngBytes, label);
  const iccp = chunks.find((c) => c.type === "iCCP");
  if (!iccp) {
    throw new Error(`${label}: iCCP not found`);
  }

  const data = iccp.data;
  const nameEnd = data.indexOf(0x00);
  if (nameEnd < 0 || nameEnd + 2 > data.length) {
    throw new Error(`${label}: invalid iCCP chunk`);
  }

  const compressionMethod = data[nameEnd + 1];
  if (compressionMethod !== 0) {
    throw new Error(`${label}: unsupported iCCP compression method ${compressionMethod}`);
  }

  const compressed = data.subarray(nameEnd + 2);
  return inflate(compressed);
}

export function hasIccProfile(pngBytes, label = "png") {
  const chunks = parsePngChunks(pngBytes, label);
  return chunks.some((c) => c.type === "iCCP");
}

function buildIccChunkData(iccProfileBytes) {
  const name = asciiBytes("icc");
  const nul = new Uint8Array([0x00]);
  const method = new Uint8Array([0x00]);
  const compressed = deflate(iccProfileBytes, { level: 9 });
  return concatBytes([name, nul, method, compressed]);
}

function rebuildPngFromChunks(chunks) {
  const outChunks = chunks.map((c) => chunk(c.type, c.data));
  return concatBytes([PNG_SIG, ...outChunks]);
}

export function stripIccProfileFromPngBytes(pngBytes, label = "png") {
  const chunks = parsePngChunks(pngBytes, label);
  const filtered = chunks.filter((c) => c.type !== "iCCP");
  return rebuildPngFromChunks(filtered);
}

export function upsertIccProfileToPngBytes(pngBytes, iccProfileBytes, label = "png") {
  if (!(iccProfileBytes instanceof Uint8Array) || iccProfileBytes.length === 0) {
    throw new Error("iccProfileBytes must be non-empty Uint8Array");
  }
  const chunks = parsePngChunks(pngBytes, label);
  const withoutIcc = chunks.filter((c) => c.type !== "iCCP");
  const ihdrIdx = withoutIcc.findIndex((c) => c.type === "IHDR");
  if (ihdrIdx < 0) {
    throw new Error(`${label}: IHDR missing`);
  }

  const iccpChunk = { type: "iCCP", data: buildIccChunkData(iccProfileBytes) };
  const out = withoutIcc.slice(0, ihdrIdx + 1).concat([iccpChunk], withoutIcc.slice(ihdrIdx + 1));
  return rebuildPngFromChunks(out);
}

function clampInt(v, min, max, label) {
  const n = Number(v);
  if (!Number.isFinite(n)) {
    throw new Error(`${label} must be finite number`);
  }
  return Math.min(max, Math.max(min, Math.trunc(n)));
}

function writeU16BE(bytes, offset, value) {
  bytes[offset] = (value >>> 8) & 0xff;
  bytes[offset + 1] = value & 0xff;
}

export function buildMinimalPatternRgba16({ width, height, alpha8Patch, mulDiv255 }) {
  const w = clampInt(width, 16, 4096, "width");
  const h = clampInt(height, 16, 4096, "height");
  const a8 = clampInt(alpha8Patch, 0, 255, "alpha8Patch");

  const px = new Uint8Array(w * h * 8);
  const bg = 1024;
  const alphaOpaque = 65535;
  const patchAlpha = mulDiv255(a8, 65535) >>> 0;

  // Use an edge-touching bright rectangle to make subtle HDR differences easier to notice.
  const patchW = Math.max(48, Math.floor(w / 3));
  const patchH = Math.max(48, Math.floor(h / 3));
  const x1 = w;
  const x0 = Math.max(0, x1 - patchW);
  const y0 = Math.floor(h / 2 - patchH / 2);
  const y1 = Math.min(h, y0 + patchH);

  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      const i = (y * w + x) * 8;
      const inPatch = x >= x0 && x < x1 && y >= y0 && y < y1;
      const rgb = inPatch ? 65535 : bg;
      const a = inPatch ? patchAlpha : alphaOpaque;
      writeU16BE(px, i + 0, rgb);
      writeU16BE(px, i + 2, rgb);
      writeU16BE(px, i + 4, rgb);
      writeU16BE(px, i + 6, a);
    }
  }

  return { width: w, height: h, rgba16be: px };
}

export function encodeRgba16Png({ width, height, rgba16be, iccProfileBytes = null }) {
  const w = clampInt(width, 16, 4096, "width");
  const h = clampInt(height, 16, 4096, "height");
  const expected = w * h * 8;
  if (rgba16be.length !== expected) {
    throw new Error(`rgba16be length mismatch: expected ${expected}, got ${rgba16be.length}`);
  }

  const ihdr = new Uint8Array(IHDR_LEN);
  writeU32BE(ihdr, 0, w);
  writeU32BE(ihdr, 4, h);
  ihdr[8] = 16;
  ihdr[9] = 6;
  ihdr[10] = 0;
  ihdr[11] = 0;
  ihdr[12] = 0;

  const rowSize = 1 + w * 8;
  const rows = new Uint8Array(h * rowSize);
  for (let y = 0; y < h; y += 1) {
    const srcOffset = y * w * 8;
    const dstOffset = y * rowSize;
    rows[dstOffset] = 0;
    rows.set(rgba16be.subarray(srcOffset, srcOffset + w * 8), dstOffset + 1);
  }

  const chunks = [chunk("IHDR", ihdr)];

  if (iccProfileBytes && iccProfileBytes.length > 0) {
    chunks.push(chunk("iCCP", buildIccChunkData(iccProfileBytes)));
  }

  chunks.push(chunk("IDAT", deflate(rows, { level: 9 })));
  chunks.push(chunk("IEND", new Uint8Array(0)));

  return concatBytes([PNG_SIG, ...chunks]);
}
