# 仮説更新メモ（2026-03-07）

更新日: 2026-03-07  
対象: `docs/reproduction-candidates.md` の人間検証結果を反映

## 1. 事実（人間検証）

### 第1段（基本4候補）

- `candidate_success_like` → 光って見えた
- `candidate_fail_rgb_no_alpha` → 光って見えた
- `candidate_fail_8bit` → 光って見えた
- `candidate_fail_no_iccp` → 光って見えない

### 第2段（extended候補・既実施分）

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

## 4. `alpha=0` / `size=512` 白化観測の解釈（今回追記）

`probe_alpha_0` と `probe_size_512` が「白化して見えた」ことは、
**iCCP/cicp仮説の反証とは限らない**と解釈する。

現時点の暫定解釈:

- `probe_alpha_0` の白化
  - alpha=0（完全透明）により、投稿先/表示系で実質的に内容が見えなくなる経路がある可能性
  - これは「HDR判定の失敗」ではなく、**表示合成（透明処理）由来の白化**の可能性が高い
- `probe_size_512` の白化
  - 512化そのものが原因とは断定できない
  - 元画像由来の透明ピクセル分布やリサイズ後のalpha分布との相互作用で白化した可能性がある

つまり、今回の白化観測は **「透明度条件が強すぎて評価不能になった」** ケースとして扱い、
`iCCP/cicp` 仮説は保留する。

## 5. 次実験（白化回避プローブ）

白化要因（alpha=0や透明域）を避けつつ切り分けるため、`make_candidates.py --extended` を追加拡張した。

追加候補:

- `candidate_probe_alpha_1.png`
  - alpha=1固定（0は回避、ほぼ透明）
- `candidate_probe_alpha_gradient.png`
  - alphaを 1..65535 のグラデーション（0を使わず透明度依存を観測）
- `candidate_probe_size_512_nontransparent.png`
  - 512x512 + alpha=255固定（サイズ要因のみを優先確認）

これにより、以下を確認する:

- alpha=0だけが白化トリガーか
- 512サイズ自体が白化トリガーか
- 透明度分布とリサイズの組み合わせで白化しているか

## 6. 当面の運用ルール

- 比較表は `generated/comparison.md` の **legacy判定**（旧）と **relaxed判定**（新）を併記
- 新しい投稿結果が出るまでは、仕様断定ではなく「仮説更新中」として扱う

## 人間検証結果（X投稿）

- `candidate_probe_alpha_gradient`
  - https://x.com/kurehajime/status/2030244873153175737
  - → 右半分は光って見えた。しかし左半分は黒っぽくなってしまった
- `candidate_probe_alpha_1`
  - 真っ白でなにも見えず
- `candidate_probe_size_512_nontransparent`
  - 真っ黒でなにも見えず