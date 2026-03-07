# 仮説更新メモ（2026-03-07）

更新日: 2026-03-07  
対象: `docs/reproduction-candidates.md` の人間検証結果を反映

## 1. 事実（人間検証）

### 第1段（基本4候補）

- `candidate_success_like` → 光って見えた
- `candidate_fail_rgb_no_alpha` → 光って見えた
- `candidate_fail_8bit` → 光って見えた
- `candidate_fail_no_iccp` → 光って見えない

### 第2段（extended候補・既実施）

- `candidate_probe_8bit_rgb_no_alpha.png`
  - 成功。十分に光って見えた
  - https://x.com/kurehajime/status/2030240958701568112
- `candidate_probe_alpha_255.png`
  - 成功。十分に光って見えた
  - https://x.com/kurehajime/status/2030241207994159531
- `candidate_probe_alpha_0.png`
  - 真っ白でなにも見えず
- `candidate_probe_size_512.png`
  - 真っ白でなにも見えず

### 第3段（白化回避プローブ・最新）

- `candidate_probe_alpha_gradient`
  - https://x.com/kurehajime/status/2030244873153175737
  - 右半分だけ光って見える。左半分は黒っぽく見える
- `candidate_probe_alpha_1`
  - 真っ白でなにも見えず
- `candidate_probe_size_512_nontransparent`
  - 真っ黒でなにも見えず

## 2. 既存仮説の確定的な見直し

従来仮説（機械判定ベース）:

- 16bit必須
- alphaチャネル（RGBA）必須
- iCCP内 `cicp=[9,16,0,1]` 必須

このうち、以下は反証済み:

- 16bit必須 → `candidate_fail_8bit` が光った
- alpha必須 → `candidate_fail_rgb_no_alpha` が光った

## 3. 更新仮説（透明度・実効輝度・表示しきい値）

現時点では、単一条件ではなく **3要素の積** で見え方が決まる仮説が有力。

1. **信号条件（メタデータ）**
   - iCCP内 `cicp=[9,16,0,1]`（BT.2020 + PQ）は依然として主要条件
2. **透明度条件（alpha）**
   - alphaが極小だと、HDR判定以前に合成段で可視性が落ちる可能性
3. **実効輝度条件（表示後に実際に届く明るさ）**
   - 「RGB値が高い」だけでは不十分で、透明度・縮小・背景合成後の実効輝度が
     表示系のしきい値を超える必要がある可能性

要するに:

- **iCCP/cicpは必要寄り**
- ただし「光って見える」には **実効輝度がしきい値を超えること** が追加で必要

## 4. 最新観測の解釈

- `alpha_gradient` で右のみ光る
  - alpha増加（または実効輝度増加）に伴って、ある境界を超えた側だけ光った可能性
  - → **表示しきい値の存在** を示唆
- `alpha_1` が白化
  - ほぼ透明で可視情報が潰れ、白背景側に寄る表示経路の可能性
- `size_512_nontransparent` が黒化
  - 透明度要因を除いても黒化したため、サイズ変更に伴うトーンマップ/露出/実効輝度低下の疑い

## 5. 次の最小切り分け（今回追加したプローブ）

`make_candidates.py --extended` に以下を追加:

- `candidate_probe_alpha_16.png`（alpha=16固定）
- `candidate_probe_alpha_64.png`（alpha=64固定）
- `candidate_probe_alpha_lr_split_16_64.png`
  - 左右分割で左alpha=16 / 右alpha=64
  - 同一画像内でしきい値境界を観測しやすくする
- `candidate_probe_alpha_ladder_1_255.png`
  - alpha段階バー（1,2,4,8,16,24,32,48,64,96,128,192,255）
  - 1投稿内で「どのalphaから光るか」を概算する
- `candidate_probe_size_512_alpha255_bright_patch.png`
  - 512x512 + alpha=255固定 + 右側に高輝度パッチ
  - 512黒化が「全体輝度不足」か「メタデータ経路問題」かを切り分け

## 6. 当面の運用ルール

- `generated/comparison.md` は **legacy判定**（旧）と **relaxed判定**（新）を併記
- 人間検証が揃うまでは仕様断定せず、しきい値仮説として扱う
- 新規プローブ投稿時は、
  - 見え方（光る/白化/黒化）
  - 左右差の有無
  - 端末/表示条件
  を必ずセットで記録する
## 人間検証結果（X投稿）

### 基本4候補

- `candidate_probe_alpha_ladder_1_255`
  - https://x.com/kurehajime/status/2030265404149604611
  - → ６本目より右が普通の白より白に見える。とはいえ一番右端も強烈に光ってるというほどではない。
