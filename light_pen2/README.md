# light_pen2

`magick-wasm` を使って、ブラウザ内で `RGBA16 + iCCP` の PNG を組み立てる実験版です。

既存の [`light_pen`](../light_pen) が自前 PNG エンコーダ中心なのに対し、こちらは
ImageMagick WASM で 16-bit PNG 書き出しと ICC 埋め込みまで行います。

## セットアップ

```bash
npm install
npm run dev
```

## 使い方

1. 背景画像をアップロード
   - PNG/JPEG/WebP など `image/*` を受け付けます
   - 出力はアスペクト比を維持し、長辺を最大 `800px` に収めます
2. キャンバス上に線を描く
   - 線はそのまま HDR 強調マスクとして使われます
3. 必要なら `画面全体にホログラム適用` を押す
4. `露光ゲイン` を調整する
5. `HDR候補を生成` を押す

## 出力

- `candidate_magick_success_like.png`
  - 16-bit PNG
  - `iCCP` あり
- `candidate_magick_fail_no_iccp.png`
  - 16-bit PNG
  - `iCCP` なし

## 実装メモ

- UI: `src/App.tsx`
- WebAssembly 本体: `public/magick.wasm`
- 参照 ICC: `public/bt2020-pq.icc`
- 発光処理は `ColorSpace.RGB` に切り替えた上で `EvaluateOperator.Multiply` による等倍率スケーリングを試しています
- 描画マスクは PNG 化したグレースケール画像として `CopyAlpha` 合成に使っています

## 注意

- これは `magick-wasm` ベースの実験版で、色管理はまだ詰め切れていません
- SDR 入力を HDR ICC へ変換する過程で、背景色の見え方が変わる可能性があります
- 最終的な HDR 判定は X への実投稿で確認してください
