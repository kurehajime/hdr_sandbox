# light_pen2

`magick-wasm` を使って、ブラウザ内で X 投稿向け `RGBA16 + iCCP` の PNG を組み立てる実験版です。

## 現在の位置づけ

- 本線は [`light_pen`](../light_pen) を使ってください
- `light_pen2` は `magick-wasm` を試すための実験枝として維持します
- 「露光していないところの見た目もできるだけ保ちたい」という要件には、自前で色変換と PNG 組み立てを制御できる `light_pen` の方が向いています

既存の [`light_pen`](../light_pen) が自前 PNG エンコーダ中心なのに対し、こちらは
ImageMagick WASM を合成に使い、最後の ICC 付与と除去だけを `src/hdr/core.mjs` で後処理します。

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

- `candidate_success_like.png`
  - 16-bit PNG
  - `iCCP` あり
- `candidate_fail_no_iccp.png`
  - 16-bit PNG
  - `iCCP` なし
  - `candidate_success_like.png` と生ピクセルは同一で、違いは `iCCP` の有無だけ

## 実装メモ

- UI: `src/App.tsx`
- WebAssembly 本体: `public/magick.wasm`
- 参照 ICC: `public/success_sample.png` から抽出した ICC
- `magick-wasm` はリサイズ、露光ブースト、マスク合成、`MagickFormat.Png64` での 16-bit PNG 書き出しだけを担当する
- `src/hdr/core.mjs` が合成済み PNG へ `iCCP` を後付けし、`fail_no_iccp` 側では `iCCP` を除去する
- 発光処理は `ColorSpace.RGB` に切り替えた上で `EvaluateOperator.Multiply` による等倍率スケーリングを試しています
- 描画マスクは PNG 化したグレースケール画像として `CopyAlpha` 合成に使っています
- `sample/giant.png` では、線なし・`露光ゲイン=1.0` の条件で元画像と `fail_no_iccp` の生ピクセル差分が `0 / 0 / 0 / 0` になることを確認済みです

## 注意

- これは `magick-wasm` ベースの実験版で、色管理はまだ詰め切れていません
- ブラウザ上のプレビューは `iCCP` 解釈の影響を強く受けるため、`success_like` の見た目だけで元画像との差を判断しないでください
- 現在は HDR ICC を `magick-wasm` で画素へ適用せず、合成済み PNG へ後付けする構成です
- 最終的な HDR 判定は X への実投稿で確認してください
