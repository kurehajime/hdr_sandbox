# Position Quadrant Spec (auto-generated)

`candidate_probe_position_quadrant_alpha64.png` は 4象限に同一パッチを置き、
画面位置依存のバイアス（右側だけ光る等）を直接確認するプローブです。

固定条件:
- patch luma: 65535 (RGBすべて最大)
- patch alpha: 64 (8bit) / 16448 (16bit)
- 背景: luma=1024, alpha=65535

観測ポイント:
- 4象限で同一条件にも関わらず発光差が出るか
- 右側のみ光るなら、alpha値ではなく位置依存要因を優先疑い
- 4象限すべて同等なら、`alpha_gradient` の偏りは連続勾配条件固有の可能性