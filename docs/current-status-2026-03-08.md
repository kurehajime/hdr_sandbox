# 現状調査メモ（2026-03-08 09:15 JST）

## 結論

- 現在の主軸は「JavaScript/WASM 実装フェーズ」で、`README.md` の方針と `package.json` の実行導線は一致している。
- 最小導線 `npm run precheck` は正常終了し、`generated/jswasm/` 前提のチェックが通る状態。
- 人間観測ベースの再現検証資産（`docs/human-observations*.md`、`docs/reproduction-candidates.md`）は保持されているが、現フェーズでは改善作業は保留扱い。

## 実行確認

- `npm run precheck` 実行結果: `posting_precheck: OK (2026-03-08)`
- 出力先:
  - `docs/observation-status-2026-03-08.md`
  - `docs/observation-status-2026-03-08.json`
  - `docs/posting-checklist-2026-03-08.md`
- `precheck` は `src/jswasm-pipeline/precheck.mjs` を実行し、以下の最小要件を確認する:
  - `generated/jswasm/candidate_success_like.png` が RGBA16 + iCCP あり
  - `generated/jswasm/candidate_fail_no_iccp.png` が RGBA16 + iCCP なし

## 観測された注意点

- 本日の `precheck` 実行により、`docs/observation-status-2026-03-08.md` の `checked_at` が更新された（内容差分は時刻のみ）。
- `docs/reproduction-candidates.md` は検証フェーズ由来の詳細運用を多く含むため、実装フェーズ優先の現在方針と読み分けが必要。

## 現時点の未完了

- 「Xへ実際に投稿してHDR表示を確認する」工程は、人手検証待ち。
- フロントエンド完結版（ブラウザUI/ブラウザ実行フロー）としての統合導線は未着手。
