# 仮説更新メモ（2026-03-07）

更新日: 2026-03-07  
対象: `docs/human-observations.md` と `docs/reproduction-candidates.md` の観測を仮説に反映

> 運用メモ: 人間観測の新規追記は `docs/human-observations.md` に集約し、
> このファイルは仮説整理・解釈のみを更新する。

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
- `candidate_probe_luma_ladder_alpha255.png`
  - alpha=255固定でRGB(16bit)を段階化した縦バー
  - 「透明度要因を除いた実効輝度しきい値」を観測する
- `candidate_probe_luma_ladder_alpha64.png`
  - alpha=64固定でRGB(16bit)を段階化した縦バー
  - alphaを下げたときに、しきい値laneがどれだけ右にずれるかを観測する
- `candidate_probe_alpha_luma_matrix.png`（今回追加）
  - x軸=alpha(8bit), y軸=luma(16bit) の2Dグリッド
  - 1枚の中で「光る/光らない」境界線の形状を観測し、積モデル `effective≈alpha×luma` を直接検証する
  - lane定義は `generated/alpha_luma_matrix_spec.md` を参照

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

## 7. 今回の30分イテレーション仮説（2D境界観測）

仮説:

- しきい値は1次元（alphaのみ／lumaのみ）ではなく、
  `alpha` と `luma` の積で近似できる2次元境界として現れる。
- そのため、`candidate_probe_alpha_luma_matrix.png` では
  「左下(低alpha/低luma)は不発、右上(高alpha/高luma)は発光、
  中間に斜めの境界」が観測されると予測する。

この結果が得られれば、次段は境界近傍のみを高解像度サンプリングした
細密マトリクス（例えば8x8→16x16局所拡大）へ進む。

## 8. 今回追加した30分イテレーション仮説（isoeff triplet）

追加プローブ:

- `candidate_probe_isoeff_triplet.png`
  - 列方向: alpha(8bit)を段階化
  - 行方向: 目標 `effective=(alpha/255)*(luma/65535)` を3水準（低/中/高）で固定
  - lane定義は `generated/isoeff_triplet_spec.md` を参照

仮説:

- もし積モデルが一次近似として有効なら、**同じ行（同じtarget effective）内では**
  左右でalphaが変わっても見え方は概ね揃う。
- 逆に、同一行で左右差が大きい場合は、
  alpha固有の非線形要因（合成経路・量子化・トーンマップ分岐）が強いことを示唆する。

観測ポイント:

- 低/中/高の3行で「全体が不発→境界→発光」と段階が出るか
- 各行の中で、特定alpha帯だけ崩れる（白化/黒化する）箇所があるか


## 人間検証結果（X投稿）

- `probe_isoeff_triplet`
  - https://x.com/kurehajime/status/2030279978156515406
  - → Githubに上げられた時点では左が白、右が黒っぽく見えた。しかしXに投稿したら全体的に黒っぽくなってしまった。上より真ん中、真ん中より下がわすかに白っぽい。
## 9. 今回の30分イテレーション仮説（threshold zoom matrix）

追加プローブ:

- `candidate_probe_threshold_zoom_matrix.png`
  - x軸: alpha(8bit) = [12,16,20,24,28,32,40,48,56,64,80,96]
  - y軸: luma(16bit) = [4096,6144,8192,10240,12288,14336,16384,20480,24576,28672,32768,40960]
  - lane定義は `generated/threshold_zoom_matrix_spec.md` を参照

仮説:

- alphaラダー観測（6本目付近から変化）を前提に、境界近傍を粗い2Dマトリクスより細かく再サンプリングする。
- もし積モデルが支配的なら、境界はなめらかな斜線として現れる。
- 逆に、alpha≈24前後で境界が折れ曲がる/段差化するなら、
  alpha固有の非線形要因（合成経路・トーンマップ分岐）を強く示唆する。

観測ポイント:

- 既存 `alpha_luma_matrix` と比べて、境界線トレースの再現性が上がるか
- `isoeff_triplet` で見えた「X投稿後に全体が黒化」傾向と矛盾しないか
- 境界近傍のセルで白化/黒化の局所的な飛びが発生するか
