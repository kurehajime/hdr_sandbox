# JS/WASM 最短実行手順

検証フェーズを止めて、まず実装を前に進めるための最短手順。

## 1. 最小生成

```bash
npm install
npm run gen:jswasm
```

補足:

- `sample/success_sample.png` から iCCP を読めない場合は `generated/icc_bt2020_pq_from_success.icc` へ自動フォールバック。
- WASM ではなく JS 経路を強制する場合は `npm run gen:jswasm -- --force-js-fallback`。

## 2. 生成+フォールバック込み

```bash
npm run gen
```

- JS/WASM が落ちたら自動で Python 生成に切り替わる。
- フォールバック経路だけ試す場合は `HDR_FORCE_PY_FALLBACK=1 npm run gen`。

## 3. 投稿前チェック（1コマンド）

```bash
npm run precheck
```

- 出力先日付は JST 当日を自動採番 (`docs/observation-status-YYYY-MM-DD.*`)。

## 4. 最短ワンライナー（実装フェーズ）

```bash
npm run impl:run
```

## 実装ファイル

- `src/jswasm-pipeline/pipeline.mjs`
- `src/jswasm-pipeline/cli.mjs`
- `scripts/generate_candidates.mjs`
- `scripts/posting_precheck.mjs`
