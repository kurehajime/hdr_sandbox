export interface GenerateMinimalCandidatesArgs {
  inputPngBytes: Uint8Array
  successRefPngBytes: Uint8Array
  iccFallbackBytes?: Uint8Array | null
  width?: number
  height?: number
  alpha8Patch?: number
  mode?: 'pass-through' | 'minimal-pattern'
  allowNoIccFallback?: boolean
  forceJsFallback?: boolean
}

export interface GenerateMinimalCandidatesResult {
  wasmMode: string
  iccSource: string
  warning?: string
  fallbackUsed: boolean
  files: Record<string, Uint8Array>
}

export function generateMinimalCandidates(
  args: GenerateMinimalCandidatesArgs,
): Promise<GenerateMinimalCandidatesResult>
