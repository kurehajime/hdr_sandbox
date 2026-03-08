type UltraHDRModule = () => Promise<{
  appendGainMap: (
    width: number,
    height: number,
    sdr: Uint8Array,
    sdrLength: number,
    gainmap: Uint8Array,
    gainmapLength: number,
    gainMapMax: number,
    gainMapMin: number,
    mapGamma: number,
    offsetSdr: number,
    offsetHdr: number,
    hdrCapacityMin: number,
    hdrCapacityMax: number,
  ) => Uint8Array
}>

const loadModule = async () => {
  const moduleUrl = new URL(
    'ultrahdr/libultrahdr-esm.js',
    new URL(import.meta.env.BASE_URL, window.location.origin),
  ).href
  try {
    const loaded = (await import(/* @vite-ignore */ moduleUrl)) as Record<string, unknown>
    return loaded
  } catch (error) {
    throw new Error(
      'UltraHDRモジュールの読み込みに失敗しました。`make ultrahdr`でビルドしてください。',
      { cause: error },
    )
  }
}

export const encodeUltraHDR = async (base: ImageData, gainmap: ImageData) => {
  const module = await loadModule()
  const init = module.default
  if (typeof init !== 'function') {
    throw new Error('libultrahdr-wasmの初期化関数が見つかりません。')
  }
  const instance = await (init as UltraHDRModule)()
  if (!instance?.appendGainMap) {
    throw new Error('libultrahdr-wasmのappendGainMapが見つかりません。')
  }
  const [sdrBytes, gainmapBytes] = await Promise.all([
    imageDataToJpeg(base),
    imageDataToJpeg(gainmap),
  ])
  const metadata = {
    gainMapMax: 64,
    gainMapMin: 0,
    mapGamma: 1,
    offsetSdr: 0,
    offsetHdr: 0,
    hdrCapacityMin: 0,
    hdrCapacityMax: 64,
  }
  const result = instance.appendGainMap(
    base.width,
    base.height,
    sdrBytes,
    sdrBytes.length,
    gainmapBytes,
    gainmapBytes.length,
    metadata.gainMapMax,
    metadata.gainMapMin,
    metadata.mapGamma,
    metadata.offsetSdr,
    metadata.offsetHdr,
    metadata.hdrCapacityMin,
    metadata.hdrCapacityMax,
  )
  const copied = Uint8Array.from(result)
  return new Blob([copied], { type: 'image/jpeg' })
}

const imageDataToJpeg = async (imageData: ImageData) => {
  const canvas = document.createElement('canvas')
  canvas.width = imageData.width
  canvas.height = imageData.height
  const context = canvas.getContext('2d')
  if (!context) {
    throw new Error('JPEG変換用のキャンバスが作成できません。')
  }
  context.putImageData(imageData, 0, 0)
  const blob = await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob(
      (result) => {
        if (result) {
          resolve(result)
        } else {
          reject(new Error('JPEGの生成に失敗しました。'))
        }
      },
      'image/jpeg',
      0.95,
    )
  })
  return new Uint8Array(await blob.arrayBuffer())
}
