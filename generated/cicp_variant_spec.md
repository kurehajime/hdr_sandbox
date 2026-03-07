# CICP Variant Spec (auto-generated)

`candidate_probe_cicp_*.png` は、同一ピクセル（alpha=64固定）で ICC 内 cicp だけを切り替える比較セットです。

| probe | primaries | transfer | matrix | range | cicp |
|---|---:|---:|---:|---:|---|
| `candidate_probe_cicp_bt2020_pq.png` | 9 | 16 | 0 | 1 | [9, 16, 0, 1] |
| `candidate_probe_cicp_bt2020_srgb.png` | 9 | 13 | 0 | 1 | [9, 13, 0, 1] |
| `candidate_probe_cicp_bt709_pq.png` | 1 | 16 | 0 | 1 | [1, 16, 0, 1] |
| `candidate_probe_cicp_bt709_srgb.png` | 1 | 13 | 0 | 1 | [1, 13, 0, 1] |

観測ポイント:
- `bt2020_pq` を基準に、`bt2020_srgb` で非発光化するか（transfer要因）
- `bt709_pq` / `bt709_srgb` の差で primaries 要因が見えるか
- 4条件の見え方が transfer 主導か、primaries 主導か、交互作用かを判定する