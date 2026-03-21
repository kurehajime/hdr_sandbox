import type { ChangeEvent } from 'react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  AlphaAction,
  Channels,
  ColorProfile,
  ColorSpace,
  CompositeOperator,
  EvaluateOperator,
  type IMagickImage,
  ImageMagick,
  MagickFormat,
  initializeImageMagick,
} from '@imagemagick/magick-wasm'
import './App.css'
import hologramUrl from './assets/kira.png'
// @ts-expect-error local .mjs module without TS declarations
import { extractIccFromPngBytes } from './hdr/core.mjs'

const MAX_OUTPUT_LONG_SIDE = 800
const DEFAULT_SOURCE_MIME = 'image/png'
const DEFAULT_EXPOSURE_GAIN = 2.4

let magickInitPromise: Promise<void> | null = null

function computeAspectFitSize(width: number, height: number, maxLongSide: number) {
  const longSide = Math.max(width, height)
  if (longSide <= maxLongSide) return { width, height }
  const scale = maxLongSide / longSide
  return {
    width: Math.max(1, Math.round(width * scale)),
    height: Math.max(1, Math.round(height * scale)),
  }
}

function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v))
}

async function blobToBytes(blob: Blob): Promise<Uint8Array> {
  return new Uint8Array(await blob.arrayBuffer())
}

async function canvasToPngBytes(canvas: HTMLCanvasElement): Promise<Uint8Array> {
  const blob = await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob((value) => {
      if (value) resolve(value)
      else reject(new Error('PNG の生成に失敗しました。'))
    }, 'image/png')
  })
  return blobToBytes(blob)
}

function resolveImageSrc(blob: Blob): string {
  return URL.createObjectURL(blob)
}

async function loadImageFromBlob(blob: Blob): Promise<HTMLImageElement> {
  const src = resolveImageSrc(blob)
  try {
    return await new Promise<HTMLImageElement>((resolve, reject) => {
      const image = new Image()
      image.onload = () => resolve(image)
      image.onerror = () => reject(new Error('画像のデコードに失敗しました。'))
      image.src = src
    })
  } finally {
    URL.revokeObjectURL(src)
  }
}

function ensureImageMagickReady(wasmBytes: Uint8Array): Promise<void> {
  if (!magickInitPromise) {
    magickInitPromise = initializeImageMagick(wasmBytes)
  }
  return magickInitPromise
}

function normalizeMaskCanvas(sourceCanvas: HTMLCanvasElement, width: number, height: number) {
  const maskCanvas = document.createElement('canvas')
  maskCanvas.width = width
  maskCanvas.height = height
  const context = maskCanvas.getContext('2d')
  if (!context) {
    throw new Error('マスク用キャンバスの初期化に失敗しました。')
  }
  context.fillStyle = 'black'
  context.fillRect(0, 0, width, height)
  context.drawImage(sourceCanvas, 0, 0, width, height)

  const imageData = context.getImageData(0, 0, width, height)
  for (let i = 0; i < imageData.data.length; i += 4) {
    const alpha = imageData.data[i + 3] / 255
    const luma = (imageData.data[i] + imageData.data[i + 1] + imageData.data[i + 2]) / (3 * 255)
    const value = Math.round(clamp01(alpha * luma) * 255)
    imageData.data[i] = value
    imageData.data[i + 1] = value
    imageData.data[i + 2] = value
    imageData.data[i + 3] = 255
  }
  context.putImageData(imageData, 0, 0)
  return maskCanvas
}

function prepareImageForHdrOutput(
  image: IMagickImage,
  outWidth: number,
  outHeight: number,
  targetProfile: ColorProfile,
) {
  if (image.width !== outWidth || image.height !== outHeight) {
    image.resize(outWidth, outHeight)
  }

  try {
    const sourceProfile = image.getColorProfile()
    if (sourceProfile) {
      image.transformColorSpace(sourceProfile, targetProfile)
    } else {
      // Uploaded images often have no embedded ICC. Treat them as sRGB before HDR conversion.
      image.colorSpace = ColorSpace.sRGB
      image.transformColorSpace(targetProfile)
    }
  } catch {
    image.colorSpace = ColorSpace.sRGB
  }

  image.depth = 16
  image.setProfile(targetProfile)
}

function applyLinearExposureBoost(
  image: IMagickImage,
  exposureGain: number,
) {
  image.colorSpace = ColorSpace.RGB
  image.evaluate(Channels.RGB, EvaluateOperator.Multiply, exposureGain)
  image.colorSpace = ColorSpace.sRGB
}

function writePngBytes(image: IMagickImage) {
  return image.write(MagickFormat.Png64, (data) => Uint8Array.from(data))
}

function App() {
  const [imageName, setImageName] = useState('base.png')
  const [sourceBytes, setSourceBytes] = useState<Uint8Array | null>(null)
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 })
  const [error, setError] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [brushSize, setBrushSize] = useState(18)
  const [exposureGain, setExposureGain] = useState(DEFAULT_EXPOSURE_GAIN)
  const [successUrl, setSuccessUrl] = useState<string | null>(null)
  const [failUrl, setFailUrl] = useState<string | null>(null)

  const baseCanvasRef = useRef<HTMLCanvasElement | null>(null)
  const drawCanvasRef = useRef<HTMLCanvasElement | null>(null)
  const isDrawingRef = useRef(false)
  const lastPointRef = useRef<{ x: number; y: number } | null>(null)
  const hologramCacheRef = useRef<{ width: number; height: number; data: Uint8ClampedArray } | null>(null)

  const hasImage = useMemo(() => sourceBytes !== null, [sourceBytes])

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
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`参照ファイルの読み込みに失敗しました: ${url}`)
    }
    return new Uint8Array(await response.arrayBuffer())
  }, [])

  const drawBasePreview = useCallback(async (blob: Blob) => {
    const image = await loadImageFromBlob(blob)
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
    if (!baseContext || !drawContext) {
      throw new Error('キャンバス初期化に失敗しました。')
    }

    baseContext.clearRect(0, 0, width, height)
    baseContext.drawImage(image, 0, 0, width, height)
    drawContext.clearRect(0, 0, drawCanvas.width, drawCanvas.height)
    clearOutputs()
  }, [clearOutputs])

  const loadSource = useCallback(async (bytes: Uint8Array, mimeType: string, name: string) => {
    const safeMimeType = mimeType || DEFAULT_SOURCE_MIME
    setSourceBytes(bytes)
    setImageName(name)
    const buffer = new ArrayBuffer(bytes.byteLength)
    new Uint8Array(buffer).set(bytes)
    await drawBasePreview(new Blob([buffer], { type: safeMimeType }))
  }, [drawBasePreview])

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
        await loadSource(bytes, DEFAULT_SOURCE_MIME, 'base.png')
      } catch (err) {
        setError(err instanceof Error ? err.message : '初期画像の読み込みに失敗しました。')
      }
    }
    void bootstrap()
  }, [fetchBytes, loadSource, resolvePublicAssetUrl])

  useEffect(() => () => {
    revokeObjectUrl(successUrl)
    revokeObjectUrl(failUrl)
  }, [failUrl, revokeObjectUrl, successUrl])

  const handleFileChange = useCallback(async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setError(null)
    try {
      const bytes = await blobToBytes(file)
      await loadSource(bytes, file.type || DEFAULT_SOURCE_MIME, file.name)
    } catch (err) {
      setError(err instanceof Error ? err.message : '画像の読み込みに失敗しました。')
    }
  }, [loadSource])

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
        output.data[i] = intensity
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
    if (!sourceBytes) return
    const drawCanvas = drawCanvasRef.current
    if (!drawCanvas) return

    setError(null)
    setIsGenerating(true)
    clearOutputs()

    try {
      const [wasmBytes, successRefPngBytes] = await Promise.all([
        fetchBytes(resolvePublicAssetUrl('magick.wasm')),
        fetchBytes(resolvePublicAssetUrl('success_sample.png')),
      ])
      await ensureImageMagickReady(wasmBytes)

      const fitted = computeAspectFitSize(drawCanvas.width, drawCanvas.height, MAX_OUTPUT_LONG_SIDE)
      const outWidth = fitted.width
      const outHeight = fitted.height
      const maskPngBytes = await canvasToPngBytes(normalizeMaskCanvas(drawCanvas, outWidth, outHeight))
      const targetProfile = new ColorProfile(extractIccFromPngBytes(successRefPngBytes, 'successRefPngBytes'))

      const { successBytes, failBytes } = ImageMagick.read(sourceBytes, (sourceImage) => {
        return sourceImage.clone((baseImage) => {
          prepareImageForHdrOutput(baseImage, outWidth, outHeight, targetProfile)

          return sourceImage.clone((boostedImage) => {
            prepareImageForHdrOutput(boostedImage, outWidth, outHeight, targetProfile)
            applyLinearExposureBoost(boostedImage, exposureGain)

            return ImageMagick.read(maskPngBytes, (maskImage) => {
              if (maskImage.width !== outWidth || maskImage.height !== outHeight) {
                maskImage.resize(outWidth, outHeight)
              }
              maskImage.alpha(AlphaAction.Off)
              maskImage.colorSpace = ColorSpace.Gray

              boostedImage.alpha(AlphaAction.Set)
              boostedImage.composite(maskImage, CompositeOperator.CopyAlpha)
              baseImage.alpha(AlphaAction.Set)
              baseImage.composite(boostedImage, CompositeOperator.Over)
              baseImage.depth = 16
              baseImage.setProfile(targetProfile)

              const successBytes = writePngBytes(baseImage)
              const failBytes = baseImage.clone((failImage) => {
                failImage.removeProfile('icc')
                return writePngBytes(failImage)
              })

              return { successBytes, failBytes }
            })
          })
        })
      })

      setSuccessUrl(URL.createObjectURL(new Blob([successBytes], { type: 'image/png' })))
      setFailUrl(URL.createObjectURL(new Blob([failBytes], { type: 'image/png' })))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'magick-wasm による HDR PNG 生成に失敗しました。')
    } finally {
      setIsGenerating(false)
    }
  }, [clearOutputs, exposureGain, fetchBytes, resolvePublicAssetUrl, sourceBytes])

  return (
    <div className="app">
      <header className="app__header">
        <div>
          <h1>Light Pen HDR PNG 2</h1>
          <p className="app__subtitle">magick-wasm で X 投稿向け HDR PNG を組み立てる実験版です。</p>
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
              <span>露光ゲイン</span>
              <input
                type="range"
                min={1}
                max={8}
                step={0.1}
                value={exposureGain}
                onChange={(event) => setExposureGain(Number(event.target.value))}
              />
              <strong>{exposureGain.toFixed(1)}x</strong>
            </label>
            <button type="button" onClick={handleApplyHologramFull} disabled={!hasImage || isGenerating}>
              画面全体にホログラム適用
            </button>
            <button type="button" onClick={handleClear} disabled={!hasImage || isGenerating}>
              線をクリア
            </button>
          </div>

          <div className="panel">
            <h2>X 向け HDR PNG</h2>
            <p className="panel__hint">
              参照成功例の ICC を使って 16-bit PNG を組み立て、描画マスク部分だけリニア倍率で強調します。
            </p>
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
