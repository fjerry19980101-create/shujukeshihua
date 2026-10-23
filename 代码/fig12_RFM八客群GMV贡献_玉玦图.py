# -*- coding: utf-8 -*-
"""
fig12 玉玦图 —— RFM 八客群的 GMV 贡献
=====================================
复现模板：教材第 2 章《17 玉玦图》（深色环形分段 + 引线标注）
复现要点：
  ① 环形按占比切分，段间留 2° 缺口；每段内部用 4 条同心细节线叠出
     "玉玦"的分层质感（不靠透明度堆叠，避免颜色糊成一片）；
  ② 引线统一走"折线 + 水平短横线"，标签固定在左右两侧的槽位上，互不压字；
  ③ 四个复购型客群合计仅 5.9% GMV，环上几乎不可见，用一条合并说明点破。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

from _style import CAT, FP, FPB, WHITE, chrome, load, note_src, save

COLORS = ["#6C5CE7", "#4B7BE5", "#2E86DE", "#3CC7C0", "#F2B705", "#ED7D31",
          "#D64550", "#8E7CF0"]


def main():
    seg = load("rfm_segments.csv").sort_values("gmv_share_pct", ascending=False)
    seg = seg.reset_index(drop=True)
    vals = seg.gmv_share_pct.tolist()
    names = seg.segment.tolist()

    fig = plt.figure(figsize=(1088 / 100, 794 / 100), dpi=100, facecolor="#1A1E43")
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0, 1088)
    ax.set_ylim(0, 794)
    ax.axis("off")

    cx, cy = 544, 400
    r_out, r_in = 196, 112
    gap = 2.0
    start = 90.0
    spans = [max(v, 0.35) / 100 * 360 for v in vals]

    # ---------- 环：实色段 + 三条同心细节线 ----------
    for i, span in enumerate(spans):
        # 缺口必须小于段角，否则 a0 > a1，Wedge 会反向画出整个圆（曾导致整环变单色）
        g = min(gap, max(span * 0.45, 0.15))
        a0, a1 = start - span + g / 2, start - g / 2
        ax.add_patch(Wedge((cx, cy), r_out, a0, a1, width=r_out - r_in,
                           facecolor=COLORS[i], edgecolor="none", zorder=3))
        for k in (0.28, 0.5, 0.72):        # 细节线，制造玉玦的分层感
            rr = r_in + (r_out - r_in) * k
            ax.add_patch(Wedge((cx, cy), rr, a0, a1, width=1.1,
                               facecolor="none", edgecolor="#0E1229",
                               alpha=0.35, zorder=4))
        start -= span

    # ---------- 引线标签：左右分槽，避开标题区 ----------
    ang = 90.0
    mids = []
    for i, span in enumerate(spans):
        mids.append((i, ang - span / 2))
        ang -= span
    right = sorted([m for m in mids if np.cos(np.deg2rad(m[1])) >= 0], key=lambda t: -t[1])
    left = sorted([m for m in mids if np.cos(np.deg2rad(m[1])) < 0], key=lambda t: -t[1])
    slots = [430, 330, 230, 140]

    def place(items, side: int):
        for j, (i, a) in enumerate(items[:4]):
            y = slots[j]
            rad = np.deg2rad(a)
            x0 = cx + np.cos(rad) * (r_out + 4)
            y0 = cy + np.sin(rad) * (r_out + 4)
            x1 = cx + side * 330
            ax.plot([x0, x1 - side * 26, x1], [y0, y, y], color="#7C82A6",
                    lw=1.0, zorder=6, solid_joinstyle="miter")
            ax.plot([x0], [y0], marker="o", ms=4.5, color=COLORS[i], zorder=7)
            ha = "left" if side > 0 else "right"     # 标签落在引线端点外侧
            ax.text(x1 + side * 8, y + 13, names[i], ha=ha, va="bottom",
                    fontsize=12, color=WHITE, fontproperties=FP)
            ax.text(x1 + side * 8, y - 13, f"GMV {vals[i]:.1f}%", ha=ha, va="top",
                    fontsize=11.5, color=COLORS[i], fontproperties=FP)

    place(right, +1)
    place(left, -1)

    # ---------- 圆心 ----------
    ax.text(cx, cy + 26, f"{vals[0] + vals[1]:.0f}%", ha="center", va="center",
            fontsize=44, color=WHITE, fontproperties=FPB)
    ax.text(cx, cy - 26, "GMV 来自两类客群", ha="center", va="center",
            fontsize=11, color=CAT, fontproperties=FP)

    small = sum(vals[4:])
    ax.text(cx, 78, f"其余 4 类复购型客群合计仅 {small:.1f}% GMV（环上几乎不可见）",
            ha="center", va="center", fontsize=11.5, color="#8B90AD", fontproperties=FP)

    chrome(
        fig,
        "RFM 八分类：钱在两个「快要走」的客群里",
        f"两类客群合计贡献 {vals[0]+vals[1]:.1f}% GMV，"
        f"其中「{names[1]}」平均已沉睡 "
        f"{seg[seg.segment==names[1]].avg_recency.iloc[0]:.0f} 天",
        note_src("R/M 以中位数二分、F 以 2 单为界（依据见论文 4.2.2 节）"),
        title_size=35, sub_size=21,
    )
    save(fig, "fig12_RFM八客群GMV贡献_玉玦图.png")


if __name__ == "__main__":
    main()
