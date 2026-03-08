# light_pen

`reference/light_pen` を土台に移植した、X投稿向け HDR PNG 生成フロントエンド。

この版は UltraHDR(JPEG gainmap) を使わず、`hdr_sandbox` で検証した
`iCCP/cicp付き PNG` 生成ロジック（`jswasm-pipeline`）を使います。

## セットアップ

```bash
npm install
npm run dev
```

## GitHub Pages

- デプロイworkflow: `.github/workflows/light-pen-pages.yml`
- `main` へ push（`light_pen/**` 変更時）で自動デプロイ
- 初回のみ、GitHub の Settings > Pages で Source を `GitHub Actions` に設定

## 使い方

1. 背景画像をアップロード（未指定時は `public/base.png`）
   - PNG/JPEG/WebP など `image/*` を受付（非PNGはブラウザ内でPNGへ正規化）
   - 出力解像度は入力画像の元サイズを維持（正方形へ強制しない）
2. キャンバス上にペンで線を描く（描画部分を高輝度化）
   - `背景最大輝度(8bit)` で、線を引いていない領域の白飛びを抑制可能
3. 必要に応じて `画面全体にホログラム適用` ボタンを押す
   - 線描画だけではホログラムは適用されない
4. `HDR候補を生成` を押す
5. 出力2枚を保存
   - `candidate_success_like.png`
   - `candidate_fail_no_iccp.png`

## 実装メモ

- HDR生成コア: `src/hdr/core.mjs`, `src/hdr/pipeline.mjs`
- UI: `src/App.tsx`
- 参照ICC: `public/success_sample.png`
- 生成時に背景画像へ `sRGB -> BT.2020/PQ` 変換を適用してから iCCP/cicp を付与
- 線描画の反映は「白へ混色」ではなく、PQの光量（nits）へ乗算ゲインを掛ける方式（色相維持）

## 注意

- `success_like` は iCCP/cicp 付き、`fail_no_iccp` は iCCP なしの対照画像です。
- X投稿時の見え方判定は実機依存のため、最終確認は実投稿で行ってください。
