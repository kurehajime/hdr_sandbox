# 仮説更新メモ（2026-03-07）

更新日: 2026-03-07
対象: `docs/reproduction-candidates.md` の人間検証結果を反映

## 1. 事実（人間検証）

人間検証で得られた観測:

- `candidate_success_like` → 光って見えた
- `candidate_fail_rgb_no_alpha` → 光って見えた
- `candidate_fail_8bit` → 光って見えた
- `candidate_fail_no_iccp` → 光って見えない

## 2. 従来仮説の見直し

従来仮説（機械判定ベース）:

- **16bit必須**
- **alphaチャネル（RGBA）必須**
- iCCP内 `cicp=[9,16,0,1]` 必須

このうち、以下は**反証**された:

- 16bit必須 → `candidate_fail_8bit` が光ったため否定
- alpha必須 → `candidate_fail_rgb_no_alpha` が光ったため否定

## 3. 更新仮説（2026-03-07時点）

現時点の第一候補:

1. **iCCP内 cicp=[9,16,0,1]（BT.2020 + PQ）が主要条件**
2. 16bitか8bitか、RGBAかRGBかは**少なくとも必須条件ではない**
3. ただし「十分条件」かどうかは未確定（他要因が共変している可能性あり）

要するに、従来の「16bit/alpha必須」から、
**「iCCP/cicp主導仮説」**へ更新する。

## 4. `candidate_fail_rgb_no_alpha` / `candidate_fail_8bit` が光った理由の切り分け方針

2つの候補が光ったことにより、bit depth と alpha の個別寄与を切り分ける必要がある。
そのため、`make_candidates.py --extended` で以下を生成するよう拡張した。

- `candidate_probe_8bit_rgb_no_alpha.png`
  - 8bit + RGB(no alpha) を同時適用（2x2の第4点）
- `candidate_probe_alpha_255.png`
  - RGBAのalpha値を255固定（alpha値の影響確認）
- `candidate_probe_alpha_0.png`
  - RGBAのalpha値を0固定（alpha値の影響確認）
- `candidate_probe_size_512.png`
  - 512x512化（400x400固定の必要性確認）

## 5. 次実験（実機投稿）

実機で上記4候補を投稿し、以下を確認する。

- `probe_8bit_rgb_no_alpha` が光るか
  - 光る: bit depth / alpha の非必須性がさらに強化
  - 光らない: 8bitとno-alphaの組み合わせで閾値を跨ぐ可能性
- `probe_alpha_255` と `probe_alpha_0` の差
  - 差なし: alpha値は本質条件ではない可能性
  - 差あり: alpha値（または透過扱い）が判定に関与する可能性
- `probe_size_512` が光るか
  - 光る: 400x400固定不要
  - 光らない: 解像度条件または周辺条件が存在

## 6. 当面の運用ルール

- 比較表は `generated/comparison.md` の **legacy判定**（旧）と **relaxed判定**（新）を併記
- 新しい投稿結果が出るまでは、仕様断定ではなく「仮説更新中」として扱う
## 人間検証結果（X投稿）

- `candidate_probe_8bit_rgb_no_alpha.png`
  - 成功。十分に光って見えた
  - https://x.com/kurehajime/status/2030240958701568112
- `candidate_probe_alpha_255.png`
  - 成功。十分に光って見えた
  - https://x.com/kurehajime/status/2030241207994159531
- `candidate_probe_alpha_0.png`
  - 画像が真っ白でなにも見えず
- `candidate_probe_size_512.png`
  - 画像が真っ白でなにも見えず