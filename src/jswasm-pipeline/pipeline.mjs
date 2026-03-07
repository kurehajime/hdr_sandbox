import { promises as fs } from "node:fs";
import path from "node:path";
import zlib from "node:zlib";

const PNG_SIG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

const MUL_DIV_255_WASM_BYTES = new Uint8Array([
  0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00,
  0x01, 0x07, 0x01, 0x60, 0x02, 0x7f, 0x7f, 0x01, 0x7f,
  0x03, 0x02, 0x01, 0x00,
  0x07, 0x0d, 0x01, 0x09, 0x6d, 0x75, 0x6c, 0x44, 0x69, 0x76, 0x32, 0x35, 0x35, 0x00, 0x00,
  0x0a, 0x0d, 0x01, 0x0b, 0x00, 0x20, 0x00, 0x20, 0x01, 0x6c, 0x41, 0xff, 0x01, 0x6e, 0x0b,
]);

function chunk(type, data) {
  const typeBuf = Buffer.from(type, "ascii");
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length, 0);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE((zlib.crc32?.(Buffer.concat([typeBuf, data])) ?? crc32(Buffer.concat([typeBuf, data]))) >>> 0, 0);
  return Buffer.concat([len, typeBuf, data, crc]);
}

function crc32(buffer) {
  let c = 0xffffffff;
  for (let i = 0; i < buffer.length; i += 1) {
    c ^= buffer[i];
    for (let j = 0; j < 8; j += 1) {
      c = (c >>> 1) ^ (0xedb88320 & -(c & 1));
    }
  }
  return (c ^ 0xffffffff) >>> 0;
}

export async function extractIccFromPng(pngPath) {
  const b = await fs.readFile(pngPath);
  if (!b.subarray(0, 8).equals(PNG_SIG)) {
    throw new Error(`not png: ${pngPath}`);
  }

  let o = 8;
  while (o < b.length) {
    const ln = b.readUInt32BE(o);
    o += 4;
    const typ = b.subarray(o, o + 4).toString("ascii");
    o += 4;
    const data = b.subarray(o, o + ln);
    o += ln + 4;

    if (typ === "iCCP") {
      const nameEnd = data.indexOf(0x00);
      if (nameEnd < 0 || nameEnd + 2 > data.length) {
        throw new Error(`invalid iCCP chunk: ${pngPath}`);
      }
      return zlib.inflateSync(data.subarray(nameEnd + 2));
    }
    if (typ === "IEND") break;
  }

  throw new Error(`iCCP not found: ${pngPath}`);
}

async function loadMulDiv255() {
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
      mulDiv255: (a, b) => Math.floor(((a >>> 0) * (b >>> 0)) / 255) >>> 0,
    };
  }
}

function buildMinimalPattern({ width, height, alpha8Patch, mulDiv255 }) {
  const px = Buffer.alloc(width * height * 8);
  const bg = 1024;
  const alphaOpaque = 65535;
  const patchAlpha = mulDiv255(alpha8Patch, 65535);

  const patchW = Math.max(24, Math.floor(width / 4));
  const patchH = Math.max(24, Math.floor(height / 4));
  const x0 = Math.floor(width / 2 - patchW / 2);
  const y0 = Math.floor(height / 2 - patchH / 2);
  const x1 = x0 + patchW;
  const y1 = y0 + patchH;

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = (y * width + x) * 8;
      const inPatch = x >= x0 && x < x1 && y >= y0 && y < y1;
      const rgb = inPatch ? 65535 : bg;
      const a = inPatch ? patchAlpha : alphaOpaque;
      px.writeUInt16BE(rgb, i + 0);
      px.writeUInt16BE(rgb, i + 2);
      px.writeUInt16BE(rgb, i + 4);
      px.writeUInt16BE(a, i + 6);
    }
  }

  return px;
}

export async function writeRgba16Png({ outPath, width, height, rgba16be, iccProfile }) {
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 16;
  ihdr[9] = 6;
  ihdr[10] = 0;
  ihdr[11] = 0;
  ihdr[12] = 0;

  const rows = Buffer.alloc(height * (1 + width * 8));
  for (let y = 0; y < height; y += 1) {
    const srcStart = y * width * 8;
    const dstStart = y * (1 + width * 8);
    rows[dstStart] = 0;
    rgba16be.copy(rows, dstStart + 1, srcStart, srcStart + width * 8);
  }

  const chunks = [chunk("IHDR", ihdr)];
  if (iccProfile) {
    const iccp = Buffer.concat([
      Buffer.from("icc", "latin1"),
      Buffer.from([0x00, 0x00]),
      zlib.deflateSync(iccProfile, { level: 9 }),
    ]);
    chunks.push(chunk("iCCP", iccp));
  }
  chunks.push(chunk("IDAT", zlib.deflateSync(rows, { level: 9 })));
  chunks.push(chunk("IEND", Buffer.alloc(0)));

  await fs.mkdir(path.dirname(outPath), { recursive: true });
  await fs.writeFile(outPath, Buffer.concat([PNG_SIG, ...chunks]));
}

export async function runMinimalPipeline({ successRef, outdir, width = 400, height = 400, alpha8Patch = 64 }) {
  const icc = await extractIccFromPng(successRef);
  const op = await loadMulDiv255();
  const pattern = buildMinimalPattern({ width, height, alpha8Patch, mulDiv255: op.mulDiv255 });

  const successPath = path.join(outdir, "candidate_success_like.png");
  const noIccPath = path.join(outdir, "candidate_fail_no_iccp.png");

  await writeRgba16Png({ outPath: successPath, width, height, rgba16be: pattern, iccProfile: icc });
  await writeRgba16Png({ outPath: noIccPath, width, height, rgba16be: pattern, iccProfile: null });

  return {
    wasmMode: op.mode,
    generated: [successPath, noIccPath],
  };
}
