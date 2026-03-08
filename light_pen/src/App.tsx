import type { ChangeEvent } from 'react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import './App.css'
// @ts-expect-error local .mjs module without TS declarations
import { generateMinimalCandidates } from './hdr/pipeline.mjs'

function App() {
  const [imageName, setImageName] = useState<string | null>(null)
  const [inputBytes, setInputBytes] = useState<Uint8Array | null>(null)
  const [mode, setMode] = useState<'minimal-pattern' | 'pass-through'>('minimal-pattern')
  const [alpha8Patch, setAlpha8Patch] = useState(255)
  const [error, setError] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [successUrl, setSuccessUrl] = useState<string | null>(null)
  const [failUrl, setFailUrl] = useState<string | null>(null)

  const hasInput = useMemo(() => inputBytes !== null, [inputBytes])

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

  const readFileBytes = useCallback(async (file: File) => {
    const ab = await file.arrayBuffer()
    return new Uint8Array(ab)
  }, [])

  const normalizeAnyImageToPngBytes = useCallback(async (file: File) => {
    if (file.type === 'image/png') {
      return readFileBytes(file)
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
      if (!context) {
        throw new Error('キャンバス初期化に失敗しました。')
      }
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
  }, [readFileBytes])

  const fetchBytes = useCallback(async (url: string) => {
    const res = await fetch(url)
    if (!res.ok) {
      throw new Error(`参照画像の読み込みに失敗しました: ${url}`)
    }
    return new Uint8Array(await res.arrayBuffer())
  }, [])

  const resolvePublicAssetUrl = useCallback((fileName: string) => {
    const base = import.meta.env.BASE_URL ?? '/'
    return `${base}${fileName}`
  }, [])

  const handleFileChange = useCallback(
    async (event: ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0]
      if (!file) return
      setError(null)
      try {
        const bytes = await normalizeAnyImageToPngBytes(file)
        setInputBytes(bytes)
        setImageName(file.name)
        clearOutputs()
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : '画像の読み込みに失敗しました。')
      }
    },
    [clearOutputs, normalizeAnyImageToPngBytes],
  )

  const handleGenerate = useCallback(async () => {
    setError(null)
    setIsGenerating(true)
    clearOutputs()
    try {
      const [successRefPngBytes, defaultInputPngBytes] = await Promise.all([
        fetchBytes(resolvePublicAssetUrl('success_sample.png')),
        fetchBytes(resolvePublicAssetUrl('base.png')),
      ])
      const sourcePngBytes = inputBytes ?? defaultInputPngBytes
      const result = await generateMinimalCandidates({
        inputPngBytes: sourcePngBytes,
        successRefPngBytes,
        mode,
        alpha8Patch,
      })
      const successBlob = new Blob([result.files['candidate_success_like.png']], { type: 'image/png' })
      const failBlob = new Blob([result.files['candidate_fail_no_iccp.png']], { type: 'image/png' })
      setSuccessUrl(URL.createObjectURL(successBlob))
      setFailUrl(URL.createObjectURL(failBlob))
    } catch (encodeError) {
      setError(
        encodeError instanceof Error
          ? encodeError.message
          : 'HDR PNGの生成に失敗しました。',
      )
    } finally {
      setIsGenerating(false)
    }
  }, [alpha8Patch, clearOutputs, fetchBytes, inputBytes, mode, resolvePublicAssetUrl])

  useEffect(() => () => {
    revokeObjectUrl(successUrl)
    revokeObjectUrl(failUrl)
  }, [failUrl, revokeObjectUrl, successUrl])

  return (
    <div className="app">
      <header className="app__header">
        <div>
          <h1>Light Pen HDR PNG</h1>
          <p className="app__subtitle">
            既存知見（iCCP/cicp付きPNG）で X 投稿向けの HDR 候補画像を生成します。
          </p>
        </div>
        <label className="file">
          <input type="file" accept="image/*" onChange={handleFileChange} />
          <span>背景画像をアップロード</span>
        </label>
      </header>

      <section className="workspace">
        <div className="workspace__canvas">
          <p className="hint">入力: {imageName ?? '未指定（public/base.png を使用）'}</p>
          <p className="hint">参照ICC: public/success_sample.png</p>
          <p className="hint">モード: {mode === 'minimal-pattern' ? 'minimal-pattern' : 'pass-through'}</p>
        </div>

        <aside className="workspace__controls">
          <div className="panel">
            <h2>生成設定</h2>
            <label className="slider">
              <span>白長方形 alpha(8bit)</span>
              <input
                type="range"
                min={0}
                max={255}
                value={alpha8Patch}
                onChange={(event) => setAlpha8Patch(Number(event.target.value))}
                disabled={mode !== 'minimal-pattern'}
              />
              <strong>{alpha8Patch}</strong>
            </label>
            <label className="slider">
              <span>モード</span>
              <select
                value={mode}
                onChange={(event) => setMode(event.target.value as 'minimal-pattern' | 'pass-through')}
              >
                <option value="minimal-pattern">minimal-pattern</option>
                <option value="pass-through">pass-through</option>
              </select>
              <strong />
            </label>
          </div>

          <div className="panel">
            <h2>HDR PNG</h2>
            <p className="panel__hint">
              {hasInput ? 'アップロード画像' : 'base.png'} + iCCP/cicp で success/fail ペアを生成します。
            </p>
            <button type="button" onClick={handleGenerate} disabled={isGenerating}>
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
