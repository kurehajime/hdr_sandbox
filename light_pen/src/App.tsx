import type { ChangeEvent } from 'react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import './App.css'
import hologramUrl from './assets/kira.png'
// @ts-expect-error local .mjs module without TS declarations
import { decodePngToRgba16, encodeRgba16Png, extractIccFromPngBytes, resizeRgba16Nearest } from './hdr/core.mjs'
const PQ_MAX_NITS = 10000
const SDR_REFERENCE_NITS = 203
const STROKE_MAX_GAIN = 6.0

function readU16BE(bytes: Uint8Array, offset: number): number {
  return ((bytes[offset] << 8) | bytes[offset + 1]) >>> 0
}

function writeU16BE(bytes: Uint8Array, offset: number, value: number) {
  const v = Math.max(0, Math.min(65535, Math.round(value)))
  bytes[offset] = (v >>> 8) & 0xff
  bytes[offset + 1] = v & 0xff
}

function srgbToLinear(v: number): number {
  if (v <= 0.04045) return v / 12.92
  return Math.pow((v + 0.055) / 1.055, 2.4)
}

function pqEncodeFromNits(nits: number): number {
  const l = Math.max(0, Math.min(1, nits / PQ_MAX_NITS))
  const m1 = 0.1593017578125
  const m2 = 78.84375
  const c1 = 0.8359375
  const c2 = 18.8515625
  const c3 = 18.6875
  const lm1 = Math.pow(l, m1)
  const num = c1 + c2 * lm1
  const den = 1 + c3 * lm1
  return Math.pow(num / den, m2)
}

function pqDecodeToNits(pqCode01: number): number {
  const p = Math.max(0, Math.min(1, pqCode01))
  const m1 = 0.1593017578125
  const m2 = 78.84375
  const c1 = 0.8359375
  const c2 = 18.8515625
  const c3 = 18.6875
  const pm = Math.pow(p, 1 / m2)
  const num = Math.max(0, pm - c1)
  const den = c2 - c3 * pm
  if (den <= 0) return PQ_MAX_NITS
  const l = Math.pow(num / den, 1 / m1)
  return Math.max(0, Math.min(PQ_MAX_NITS, l * PQ_MAX_NITS))
}

function pqCode16ToNits(code16: number): number {
  return pqDecodeToNits(Math.max(0, Math.min(65535, code16)) / 65535)
}

function nitsToPqCode16(nits: number): number {
  return Math.max(0, Math.min(65535, Math.round(pqEncodeFromNits(nits) * 65535)))
}

function convertRgba16SrgbToBt2020PqInPlace(rgba16be: Uint8Array) {
  for (let i = 0; i < rgba16be.length; i += 8) {
    const sr = readU16BE(rgba16be, i + 0) / 65535
    const sg = readU16BE(rgba16be, i + 2) / 65535
    const sb = readU16BE(rgba16be, i + 4) / 65535

    const lr = srgbToLinear(sr)
    const lg = srgbToLinear(sg)
    const lb = srgbToLinear(sb)

    // sRGB (D65) -> BT.2020 linear
    const r2020 = 0.6274040 * lr + 0.3292820 * lg + 0.0433136 * lb
    const g2020 = 0.0690970 * lr + 0.9195400 * lg + 0.0113612 * lb
    const b2020 = 0.0163916 * lr + 0.0880132 * lg + 0.8955950 * lb

    const rPq = pqEncodeFromNits(Math.max(0, r2020) * SDR_REFERENCE_NITS)
    const gPq = pqEncodeFromNits(Math.max(0, g2020) * SDR_REFERENCE_NITS)
    const bPq = pqEncodeFromNits(Math.max(0, b2020) * SDR_REFERENCE_NITS)

    writeU16BE(rgba16be, i + 0, Math.round(rPq * 65535))
    writeU16BE(rgba16be, i + 2, Math.round(gPq * 65535))
    writeU16BE(rgba16be, i + 4, Math.round(bPq * 65535))
  }
}

function App() {
  const [imageName, setImageName] = useState<string>('base.png')
  const [sourcePngBytes, setSourcePngBytes] = useState<Uint8Array | null>(null)
  const [imageSize, setImageSize] = useState<{ width: number; height: number }>({ width: 0, height: 0 })
  const [error, setError] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [brushSize, setBrushSize] = useState(18)
  const [backgroundCap8, setBackgroundCap8] = useState(255)
  const [successUrl, setSuccessUrl] = useState<string | null>(null)
  const [failUrl, setFailUrl] = useState<string | null>(null)

  const baseCanvasRef = useRef<HTMLCanvasElement | null>(null)
  const drawCanvasRef = useRef<HTMLCanvasElement | null>(null)
  const isDrawingRef = useRef(false)
  const lastPointRef = useRef<{ x: number; y: number } | null>(null)
  const hologramCacheRef = useRef<{ width: number; height: number; data: Uint8ClampedArray } | null>(null)

  const hasImage = useMemo(() => sourcePngBytes !== null, [sourcePngBytes])

  const revokeObjectUrl = useCallback((url: string | null) => {
    if (url) URL.revokeObjectURL(url)
  }, [])

  const clearOutputs = useCallback(() => {
    setSuccessUrl((prev) => {
      revokeObjectUrl(prev)
      return null
    })
    setFailUrl((prev) => {
      revokeObjectUrl(prev)
      return null
    })
  }, [revokeObjectUrl])

  const resolvePublicAssetUrl = useCallback((fileName: string) => {
    const base = import.meta.env.BASE_URL ?? '/'
    return `${base}${fileName}`
  }, [])

  const fetchBytes = useCallback(async (url: string) => {
    const res = await fetch(url)
    if (!res.ok) throw new Error(`参照画像の読み込みに失敗しました: ${url}`)
    return new Uint8Array(await res.arrayBuffer())
  }, [])

  const bytesToImage = useCallback(async (bytes: Uint8Array) => {
    const blob = new Blob([bytes as unknown as BlobPart], { type: 'image/png' })
    const objectUrl = URL.createObjectURL(blob)
    try {
      return await new Promise<HTMLImageElement>((resolve, reject) => {
        const image = new Image()
        image.onload = () => resolve(image)
        image.onerror = () => reject(new Error('画像のデコードに失敗しました。'))
        image.src = objectUrl
      })
    } finally {
      URL.revokeObjectURL(objectUrl)
    }
  }, [])

  const drawBasePreview = useCallback(async (pngBytes: Uint8Array) => {
    const image = await bytesToImage(pngBytes)
    const baseCanvas = baseCanvasRef.current
    const drawCanvas = drawCanvasRef.current
    if (!baseCanvas || !drawCanvas) return
    const width = image.naturalWidth
    const height = image.naturalHeight
    baseCanvas.width = width
    baseCanvas.height = height
    drawCanvas.width = width
    drawCanvas.height = height
    setImageSize({ width, height })
    const baseContext = baseCanvas.getContext('2d')
    const drawContext = drawCanvas.getContext('2d')
    if (!baseContext || !drawContext) throw new Error('キャンバス初期化に失敗しました。')
    baseContext.clearRect(0, 0, width, height)
    baseContext.drawImage(image, 0, 0, width, height)
    drawContext.clearRect(0, 0, width, height)
    clearOutputs()
  }, [bytesToImage, clearOutputs])

  const normalizeAnyImageToPngBytes = useCallback(async (file: File) => {
    if (file.type === 'image/png') {
      return new Uint8Array(await file.arrayBuffer())
    }
    const objectUrl = URL.createObjectURL(file)
    try {
      const image = await new Promise<HTMLImageElement>((resolve, reject) => {
        const el = new Image()
        el.onload = () => resolve(el)
        el.onerror = () => reject(new Error('画像のデコードに失敗しました。'))
        el.src = objectUrl
      })
      const canvas = document.createElement('canvas')
      canvas.width = image.naturalWidth
      canvas.height = image.naturalHeight
      const context = canvas.getContext('2d')
      if (!context) throw new Error('キャンバス初期化に失敗しました。')
      context.drawImage(image, 0, 0)
      const blob = await new Promise<Blob>((resolve, reject) => {
        canvas.toBlob((value) => {
          if (value) resolve(value)
          else reject(new Error('PNG変換に失敗しました。'))
        }, 'image/png')
      })
      return new Uint8Array(await blob.arrayBuffer())
    } finally {
      URL.revokeObjectURL(objectUrl)
    }
  }, [])

  const loadHologramPattern = useCallback(async (width: number, height: number) => {
    const cached = hologramCacheRef.current
    if (cached && cached.width === width && cached.height === height) return cached.data
    const image = await new Promise<HTMLImageElement>((resolve, reject) => {
      const el = new Image()
      el.onload = () => resolve(el)
      el.onerror = () => reject(new Error('ホログラム画像の読み込みに失敗しました。'))
      el.src = hologramUrl
    })
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const context = canvas.getContext('2d')
    if (!context) throw new Error('ホログラム用キャンバスの初期化に失敗しました。')
    const tileSize = Math.min(width, height)
    for (let y = 0; y < height; y += tileSize) {
      for (let x = 0; x < width; x += tileSize) {
        context.drawImage(image, x, y, tileSize, tileSize)
      }
    }
    const data = context.getImageData(0, 0, width, height).data
    const copied = new Uint8ClampedArray(data)
    hologramCacheRef.current = { width, height, data: copied }
    return copied
  }, [])

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const bytes = await fetchBytes(resolvePublicAssetUrl('base.png'))
        setSourcePngBytes(bytes)
        await drawBasePreview(bytes)
        setImageName('base.png')
      } catch (err) {
        setError(err instanceof Error ? err.message : '初期画像の読み込みに失敗しました。')
      }
    }
    void bootstrap()
  }, [drawBasePreview, fetchBytes, resolvePublicAssetUrl])

  useEffect(() => () => {
    revokeObjectUrl(successUrl)
    revokeObjectUrl(failUrl)
  }, [failUrl, revokeObjectUrl, successUrl])

  const handleFileChange = useCallback(async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    setError(null)
    try {
      const bytes = await normalizeAnyImageToPngBytes(file)
      setSourcePngBytes(bytes)
      setImageName(file.name)
      await drawBasePreview(bytes)
    } catch (err) {
      setError(err instanceof Error ? err.message : '画像の読み込みに失敗しました。')
    }
  }, [drawBasePreview, normalizeAnyImageToPngBytes])

  const getCanvasPoint = useCallback((event: React.PointerEvent<HTMLCanvasElement>) => {
    const canvas = drawCanvasRef.current
    if (!canvas) return null
    const rect = canvas.getBoundingClientRect()
    const scaleX = canvas.width / rect.width
    const scaleY = canvas.height / rect.height
    return { x: (event.clientX - rect.left) * scaleX, y: (event.clientY - rect.top) * scaleY }
  }, [])

  const drawStroke = useCallback((from: { x: number; y: number }, to: { x: number; y: number }) => {
    const drawCanvas = drawCanvasRef.current
    const context = drawCanvas?.getContext('2d')
    if (!context) return
    context.strokeStyle = 'rgba(255,255,255,1.0)'
    context.lineWidth = brushSize
    context.lineCap = 'round'
    context.lineJoin = 'round'
    context.beginPath()
    context.moveTo(from.x, from.y)
    context.lineTo(to.x, to.y)
    context.stroke()
  }, [brushSize])

  const handlePointerDown = useCallback((event: React.PointerEvent<HTMLCanvasElement>) => {
    if (!hasImage) return
    const point = getCanvasPoint(event)
    if (!point) return
    isDrawingRef.current = true
    lastPointRef.current = point
    event.currentTarget.setPointerCapture(event.pointerId)
  }, [getCanvasPoint, hasImage])

  const handlePointerMove = useCallback((event: React.PointerEvent<HTMLCanvasElement>) => {
    if (!isDrawingRef.current) return
    const point = getCanvasPoint(event)
    const lastPoint = lastPointRef.current
    if (!point || !lastPoint) return
    drawStroke(lastPoint, point)
    lastPointRef.current = point
  }, [drawStroke, getCanvasPoint])

  const handlePointerUp = useCallback((event: React.PointerEvent<HTMLCanvasElement>) => {
    if (!isDrawingRef.current) return
    isDrawingRef.current = false
    lastPointRef.current = null
    event.currentTarget.releasePointerCapture(event.pointerId)
  }, [])

  const handleClear = useCallback(() => {
    const drawCanvas = drawCanvasRef.current
    if (!drawCanvas) return
    const context = drawCanvas.getContext('2d')
    if (!context) return
    context.clearRect(0, 0, drawCanvas.width, drawCanvas.height)
    clearOutputs()
  }, [clearOutputs])

  const handleApplyHologramFull = useCallback(async () => {
    const drawCanvas = drawCanvasRef.current
    const context = drawCanvas?.getContext('2d')
    if (!drawCanvas || !context) return
    setError(null)
    try {
      const patternData = await loadHologramPattern(drawCanvas.width, drawCanvas.height)
      const output = context.createImageData(drawCanvas.width, drawCanvas.height)
      for (let i = 0; i < output.data.length; i += 4) {
        const norm = (patternData[i] + patternData[i + 1] + patternData[i + 2]) / (3 * 255)
        const contrasted = Math.min(1, Math.max(0, (norm - 0.3) / 0.7))
        const shaped = Math.pow(contrasted, 2.2)
        const intensity = Math.min(255, Math.round(255 * Math.min(1, shaped * 2.4)))
        const alpha = Math.min(255, Math.round(180 + shaped * 75))
        output.data[i + 0] = intensity
        output.data[i + 1] = intensity
        output.data[i + 2] = intensity
        output.data[i + 3] = alpha
      }
      context.putImageData(output, 0, 0)
      clearOutputs()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'ホログラム適用に失敗しました。')
    }
  }, [clearOutputs, loadHologramPattern])

  const handleGenerate = useCallback(async () => {
    if (!sourcePngBytes) return
    const drawCanvas = drawCanvasRef.current
    const drawContext = drawCanvas?.getContext('2d')
    if (!drawCanvas || !drawContext) return

    setError(null)
    setIsGenerating(true)
    clearOutputs()
    try {
      const [successRefPngBytes, drawImageData] = await Promise.all([
        fetchBytes(resolvePublicAssetUrl('success_sample.png')),
        Promise.resolve(drawContext.getImageData(0, 0, drawCanvas.width, drawCanvas.height)),
      ])

      const outW = drawCanvas.width
      const outH = drawCanvas.height
      const decoded = decodePngToRgba16(sourcePngBytes, 'inputPngBytes')
      const rgba16be = resizeRgba16Nearest({
        srcWidth: decoded.width,
        srcHeight: decoded.height,
        srcRgba16be: decoded.rgba16be,
        dstWidth: outW,
        dstHeight: outH,
      })
      convertRgba16SrgbToBt2020PqInPlace(rgba16be)
      const bgCap16 = Math.max(0, Math.min(255, backgroundCap8)) * 257

      for (let i = 0; i < outW * outH; i += 1) {
        const p = i * 4
        const maskAlpha = drawImageData.data[p + 3] / 255
        const s = i * 8
        let currentR = readU16BE(rgba16be, s + 0)
        let currentG = readU16BE(rgba16be, s + 2)
        let currentB = readU16BE(rgba16be, s + 4)

        // Reduce whiteout by capping background luminance where no stroke is drawn.
        const bgWeight = 1 - maskAlpha
        if (bgWeight > 0) {
          const maxChannel = Math.max(currentR, currentG, currentB)
          if (maxChannel > bgCap16 && maxChannel > 0) {
            const scale = bgCap16 / maxChannel
            const factor = 1 - bgWeight * (1 - scale)
            currentR = Math.round(currentR * factor)
            currentG = Math.round(currentG * factor)
            currentB = Math.round(currentB * factor)
          }
        }

        if (maskAlpha > 0) {
          const maskLuma = (drawImageData.data[p + 0] + drawImageData.data[p + 1] + drawImageData.data[p + 2]) / (3 * 255)
          const strokeWeight = Math.max(0, Math.min(1, maskAlpha * maskLuma))
          const desiredGain = 1 + strokeWeight * (STROKE_MAX_GAIN - 1)
          const rNits = pqCode16ToNits(currentR)
          const gNits = pqCode16ToNits(currentG)
          const bNits = pqCode16ToNits(currentB)
          const maxNits = Math.max(1e-6, rNits, gNits, bNits)
          const headroomGain = PQ_MAX_NITS / maxNits
          const gain = Math.max(1, Math.min(desiredGain, headroomGain))
          currentR = nitsToPqCode16(rNits * gain)
          currentG = nitsToPqCode16(gNits * gain)
          currentB = nitsToPqCode16(bNits * gain)
        }

        writeU16BE(rgba16be, s + 0, currentR)
        writeU16BE(rgba16be, s + 2, currentG)
        writeU16BE(rgba16be, s + 4, currentB)
        writeU16BE(rgba16be, s + 6, 65535)
      }

      const iccProfile = extractIccFromPngBytes(successRefPngBytes, 'successRefPngBytes')
      const successBytes = encodeRgba16Png({
        width: outW,
        height: outH,
        rgba16be,
        iccProfileBytes: iccProfile,
      })
      const failBytes = encodeRgba16Png({
        width: outW,
        height: outH,
        rgba16be,
        iccProfileBytes: null,
      })

      setSuccessUrl(URL.createObjectURL(new Blob([successBytes as unknown as BlobPart], { type: 'image/png' })))
      setFailUrl(URL.createObjectURL(new Blob([failBytes as unknown as BlobPart], { type: 'image/png' })))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'HDR PNG の生成に失敗しました。')
    } finally {
      setIsGenerating(false)
    }
  }, [backgroundCap8, clearOutputs, fetchBytes, resolvePublicAssetUrl, sourcePngBytes])

  return (
    <div className="app">
      <header className="app__header">
        <div>
          <h1>Light Pen HDR PNG</h1>
          <p className="app__subtitle">描いた線だけを高輝度化し、X投稿向けHDR PNGを生成します。</p>
        </div>
        <label className="file">
          <input type="file" accept="image/*" onChange={handleFileChange} />
          <span>背景画像をアップロード</span>
        </label>
      </header>

      <section className="workspace">
        <div className="workspace__canvas">
          <div className="canvas-stack">
            <canvas ref={baseCanvasRef} className="canvas" />
            <canvas
              ref={drawCanvasRef}
              className="canvas canvas--draw"
              onPointerDown={handlePointerDown}
              onPointerMove={handlePointerMove}
              onPointerUp={handlePointerUp}
              onPointerLeave={handlePointerUp}
            />
          </div>
          <p className="hint">入力: {imageName} ({imageSize.width}x{imageSize.height})</p>
        </div>

        <aside className="workspace__controls">
          <div className="panel">
            <h2>描画設定</h2>
            <label className="slider">
              <span>ペンの太さ</span>
              <input
                type="range"
                min={4}
                max={120}
                value={brushSize}
                onChange={(event) => setBrushSize(Number(event.target.value))}
              />
              <strong>{brushSize}px</strong>
            </label>
            <label className="slider">
              <span>背景最大輝度(8bit)</span>
              <input
                type="range"
                min={96}
                max={255}
                value={backgroundCap8}
                onChange={(event) => setBackgroundCap8(Number(event.target.value))}
              />
              <strong>{backgroundCap8}</strong>
            </label>
            <button type="button" onClick={handleApplyHologramFull} disabled={!hasImage || isGenerating}>
              画面全体にホログラム適用
            </button>
            <button type="button" onClick={handleClear} disabled={!hasImage || isGenerating}>
              線をクリア
            </button>
          </div>

          <div className="panel">
            <h2>HDR PNG</h2>
            <p className="panel__hint">success/fail の2枚を同時生成し、iCCP有無で比較できます。</p>
            <button type="button" onClick={handleGenerate} disabled={!hasImage || isGenerating}>
              {isGenerating ? '生成中…' : 'HDR候補を生成'}
            </button>
            {successUrl && <img className="preview" src={successUrl} alt="candidate success preview" />}
            {successUrl && (
              <a className="download" href={successUrl} download="candidate_success_like.png">
                success_like を保存
              </a>
            )}
            {failUrl && (
              <a className="download" href={failUrl} download="candidate_fail_no_iccp.png">
                fail_no_iccp を保存
              </a>
            )}
            {error && <p className="error">{error}</p>}
          </div>
        </aside>
      </section>
    </div>
  )
}

export default App
