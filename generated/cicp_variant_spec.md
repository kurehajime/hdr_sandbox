# CICP Variant Spec (auto-generated)

`candidate_probe_cicp_*.png` は、同一ピクセル（alpha=64固定）で ICC 内 cicp だけを切り替える比較セットです。
primaries / transfer / matrix / range の寄与を分離観測します。

| probe | primaries | transfer | matrix | range | cicp |
|---|---:|---:|---:|---:|---|
| `candidate_probe_cicp_bt2020_pq.png` | 9 | 16 | 0 | 1 | [9, 16, 0, 1] |
| `candidate_probe_cicp_bt2020_srgb.png` | 9 | 13 | 0 | 1 | [9, 13, 0, 1] |
| `candidate_probe_cicp_bt709_pq.png` | 1 | 16 | 0 | 1 | [1, 16, 0, 1] |
| `candidate_probe_cicp_bt709_srgb.png` | 1 | 13 | 0 | 1 | [1, 13, 0, 1] |
| `candidate_probe_cicp_bt2020_pq_limited.png` | 9 | 16 | 0 | 0 | [9, 16, 0, 0] |
| `candidate_probe_cicp_bt2020_pq_matrix_1.png` | 9 | 16 | 1 | 1 | [9, 16, 1, 1] |

観測ポイント:
- `bt2020_pq` を基準に、`bt2020_srgb` で非発光化するか（transfer要因）
- `bt2020_pq` と `bt709_pq` の差で primaries 要因を判定する
- `bt2020_pq` と `bt2020_pq_limited` の差で range 要因を判定する
- `bt2020_pq` と `bt2020_pq_matrix_1` の差で matrix 要因を判定する
- 6条件の見え方から、どのcicp要素が支配的かを判定する