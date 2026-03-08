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

1. 背景PNGをアップロード（未指定時は `public/base.png`）
   - PNG/JPEG/WebP など `image/*` を受付（非PNGはブラウザ内でPNGへ正規化）
2. モードを選択
   - `minimal-pattern`（背景 + 白長方形パッチ重畳）
   - `pass-through`（入力PNGをそのまま success_like に採用）
3. `HDR候補を生成` を押す
4. 出力2枚を保存
   - `candidate_success_like.png`
   - `candidate_fail_no_iccp.png`

## 実装メモ

- HDR生成コア: `src/hdr/core.mjs`, `src/hdr/pipeline.mjs`
- UI: `src/App.tsx`
- 参照ICC: `public/success_sample.png`

## 注意

- `minimal-pattern` は `--alpha8-patch` 相当の値をUIで調整可能（既定255）。
- X投稿時の見え方判定は実機依存のため、最終確認は実投稿で行ってください。
