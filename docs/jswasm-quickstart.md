# JS/WASM 最短実行手順

## フェーズ宣言

- 検証フェーズ（検証運用・観測管理の改善）は一旦停止。
- いまは JavaScript/WASM 実装を優先する。
- 技術制約: 実装はフロントエンドでも動かせる技術のみを使う。
  - Node専用API・Python依存・サーバ依存を新規採用しない
  - CLIは当面の開発導線として利用可

## 1) 依存導入

```bash
npm install
```

## 2) 最小生成

```bash
npm run gen:jswasm
```

補足:

- `sample/success_sample.png` から iCCP を読めない場合は `generated/icc_bt2020_pq_from_success.icc` にフォールバック。
- WASMの代わりにJS計算を強制する場合は `npm run gen:jswasm -- --force-js-fallback`。
- iCCP 埋め込み失敗時は no-iCCP で継続生成する。

## 3) 生成（失敗時フォールバック込み）

```bash
npm run gen
```

- 1回目: 通常 JS/WASM
- 失敗時: JSフォールバック強制 + no-iCCP許容で自動再試行
- フォールバック経路だけ試す場合:

```bash
HDR_FORCE_JS_FALLBACK=1 npm run gen
```

## 4) 投稿前チェック（1コマンド）

```bash
npm run precheck
```

- `candidate_success_like.png`: RGBA16 + iCCPあり
- `candidate_fail_no_iccp.png`: RGBA16 + iCCPなし
- 出力先日付は JST 当日を自動採番 (`docs/observation-status-YYYY-MM-DD.*`)

## 5) 最短ワンライナー

```bash
npm run impl:run
```

## 実装ファイル

- `src/jswasm-pipeline/core.mjs`
- `src/jswasm-pipeline/pipeline.mjs`
- `src/jswasm-pipeline/cli.mjs`
- `src/jswasm-pipeline/precheck.mjs`
- `scripts/generate_candidates.mjs`
