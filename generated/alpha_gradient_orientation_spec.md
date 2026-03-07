# Alpha Gradient Orientation Spec (auto-generated)

`candidate_probe_alpha_gradient*.png` は alphaグラデーションの向きだけを変えた比較セットです。

| file | alpha direction | purpose |
|---|---|---|
| `candidate_probe_alpha_gradient.png` | left -> right | 基準（既観測: 右半分のみ発光） |
| `candidate_probe_alpha_gradient_rl.png` | right -> left | 左右位置バイアス vs alpha依存の切り分け |
| `candidate_probe_alpha_gradient_tb.png` | top -> bottom | 左右固定UI要因（オーバーレイ等）の切り分け |

観測ポイント:
- `gradient` と `gradient_rl` で発光側が反転するか
  - 反転する: alpha値依存が主因
  - 反転しない: 画面位置依存（UI/表示パイプライン）を疑う
- `gradient_tb` で上半分/下半分の偏りが出るか
  - 上下でも偏る: 軸非依存のしきい値要因
  - 左右だけ偏る: 左右固定UI要因の疑いが強い