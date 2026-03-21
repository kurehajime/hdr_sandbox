export interface PngChunk {
  type: string
  data: Uint8Array
  crc: number
}

export interface IhdrSummary {
  width: number
  height: number
  bitDepth: number
  colorType: number
  compressionMethod: number
  filterMethod: number
  interlaceMethod: number
}

export interface ResizeRgba16NearestArgs {
  srcWidth: number
  srcHeight: number
  srcRgba16be: Uint8Array
  dstWidth: number
  dstHeight: number
}

export interface BuildMinimalPatternRgba16Args {
  width: number
  height: number
  alpha8Patch: number
  mulDiv255: number
  baseRgba16be?: Uint8Array | null
}

export interface EncodeRgba16PngArgs {
  width: number
  height: number
  rgba16be: Uint8Array
  iccProfileBytes?: Uint8Array | null
}

export const PNG_SIG: Uint8Array

export function parsePngChunks(pngBytes: Uint8Array, label?: string): PngChunk[]
export function getIhdrSummary(pngBytes: Uint8Array, label?: string): IhdrSummary
export function extractIccFromPngBytes(pngBytes: Uint8Array, label?: string): Uint8Array
export function hasIccProfile(pngBytes: Uint8Array, label?: string): boolean
export function decodePngToRgba16(
  pngBytes: Uint8Array,
  label?: string,
): { width: number; height: number; rgba16be: Uint8Array }
export function resizeRgba16Nearest(args: ResizeRgba16NearestArgs): Uint8Array
export function stripIccProfileFromPngBytes(pngBytes: Uint8Array, label?: string): Uint8Array
export function upsertIccProfileToPngBytes(
  pngBytes: Uint8Array,
  iccProfileBytes: Uint8Array,
  label?: string,
): Uint8Array
export function buildMinimalPatternRgba16(args: BuildMinimalPatternRgba16Args): Uint8Array
export function encodeRgba16Png(args: EncodeRgba16PngArgs): Uint8Array
