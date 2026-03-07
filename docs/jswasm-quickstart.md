# JS/WASM 最短実行手順

検証フェーズを止めて、まず実装を前に進めるための最短手順。

## 1. 最小生成

```bash
npm install
npm run gen:jswasm
```

## 2. 生成+フォールバック込み

```bash
npm run gen
```

- JS/WASM が落ちたら自動で Python 生成に切り替わる。

## 3. 投稿前チェック（1コマンド）

```bash
npm run precheck:post
```

## 実装ファイル

- `src/jswasm-pipeline/pipeline.mjs`
- `src/jswasm-pipeline/cli.mjs`
- `scripts/generate_candidates.mjs`
- `scripts/posting_precheck.mjs`
