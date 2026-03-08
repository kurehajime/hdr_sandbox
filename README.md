# hdr_sandbox

X向けHDR画像投稿の再現調査リポジトリ。

## フェーズ方針（2026-03-08）

- **最重要:** 検証フェーズ（運用・観測管理の改善作業）は一旦停止。
- **現在は JavaScript/WASM 実装を優先。**
- **技術制約:** 実装に使う技術はフロントエンドでも動かせるものに限定する。
  - Node専用API / Python依存 / サーバ依存を新規採用しない
  - `src/jswasm-pipeline/core.mjs` / `src/jswasm-pipeline/pipeline.mjs` は Node 依存なし（ブラウザ実行可能な純JS+WASM）
  - CLI実行は当面許容（開発導線としてのみ。Node API使用はCLIラッパー層に限定）

## JavaScript/WASM 実装フェーズ（最短実行）

### 0) 依存

```bash
npm install
```

### 1) 最小生成パイプライン

```bash
npm run gen:jswasm
```

- 実装: `src/jswasm-pipeline/`
- 出力:
  - `generated/jswasm/candidate_success_like.png`
  - `generated/jswasm/candidate_fail_no_iccp.png`
- 既定モードは `pass-through`（入力PNGをそのまま success_like に採用）で、`sample/success_sample.png` と同一画素で比較できる
- 従来の合成パターンは `--mode minimal-pattern` で利用可能（右端に接触する高輝度長方形パッチ）
- WASM `mulDiv255` が使えない場合は JS 計算へ自動フォールバック
- `sample/success_sample.png` の iCCP 抽出に失敗した場合は `generated/icc_bt2020_pq_from_success.icc` を使用
- iCCP埋め込み失敗時は no-iCCP で継続生成（フォールバック）

### 2) 生成コマンド（失敗時フォールバック付き）

```bash
npm run gen
```

- 1回目: 通常 JS/WASM 経路
- 失敗時: `--force-js-fallback --allow-no-icc-fallback` を付けて再試行
- Pythonフォールバックは標準経路から外し、`precheck:legacy` 側に分離

### 3) 投稿前チェック（1コマンド化）

```bash
npm run precheck
```

- `src/jswasm-pipeline/precheck.mjs` で最小必須チェックを実行
  - `candidate_success_like.png`: RGBA16 + iCCPあり
  - `candidate_fail_no_iccp.png`: RGBA16 + iCCPなし
- 出力:
  - `docs/observation-status-YYYY-MM-DD.md`
  - `docs/observation-status-YYYY-MM-DD.json`
  - `docs/posting-checklist-YYYY-MM-DD.md`

### 4) 生成→投稿前チェックを一気に実行

```bash
npm run impl:run
```

## 実装ファイル

- `src/jswasm-pipeline/core.mjs`（PNG/IHDR/iCCP処理の共通コア）
- `src/jswasm-pipeline/pipeline.mjs`（最小生成パイプライン本体。Node依存なし）
- `src/jswasm-pipeline/cli.mjs`（生成CLI。Node I/Oラッパー）
- `src/jswasm-pipeline/precheck.mjs`（投稿前チェックCLI）
- `scripts/generate_candidates.mjs`（生成時フォールバック制御）

## 旧検証系（保留）

- `scripts/posting_precheck.mjs` / `scripts/check_png_hdr.py` / `scripts/check_human_observations.py`
- `scripts/make_candidates.py`

当面は保守のみ。実装フェーズ完了まで新規改善は行わない。
