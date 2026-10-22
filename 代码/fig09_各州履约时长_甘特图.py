# -*- coding: utf-8 -*-
"""
fig09 甘特图 —— 各州履约的三段时间
==================================
复现模板：教材第 2 章《10 甘特图》
复现要点：每个州一行，用两段色块表示"卖家备货段"与"干线末端段"，
         两段首尾相接形成完整交付周期；段内标天数，行末标总时长。
业务含义：色块越靠左越短 = 卖家反应快；越靠右越长 = 物流半径大。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from matplotlib.patches import Rectangle

from _style import CAT, FP, ORANGE, TEAL, WHITE, chrome, load, new_canvas, note_src, save


def main():
    sg = load("state_stage_days.csv").sort_values("total", ascending=False).head(12)
    sg = sg.iloc[::-1]
    y = np.arange(len(sg))

    fig, ax = new_canvas(plot=(0.145, 0.155, 0.755, 0.545))
    for i, r in enumerate(sg.itertuples()):
        ax.add_patch(Rectangle((0, i - 0.28), r.handover, 0.56,
                               facecolor=TEAL, edgecolor="none", zorder=2))
        ax.add_patch(Rectangle((r.handover, i - 0.28), r.transit, 0.56,
                               facecolor=ORANGE, edgecolor="none", zorder=2))
        ax.text(r.handover / 2, i, f"{r.handover:.1f}", ha="center", va="center",
                fontsize=10.5, color="#0E3B38", fontproperties=FP)
        ax.text(r.handover + r.transit / 2, i, f"{r.transit:.1f}", ha="center", va="center",
                fontsize=10.5, color="#4A1F00", fontproperties=FP)
        ax.text(r.handover + r.transit + 0.35, i, f"{r.total:.1f} 天", ha="left", va="center",
                fontsize=11.5, color=WHITE, fontproperties=FP)

    ax.set_yticks(y)
    ax.set_yticklabels(sg.state, fontsize=13, color=CAT, fontproperties=FP)
    ax.set_xlim(0, sg.total.max() * 1.28)
    ax.set_xticks([])
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)

    # 图例
    for x, c, t in [(0.0, TEAL, "卖家备货段"), (0.13, ORANGE, "干线+末端段")]:
        ax.add_patch(Rectangle((x, 1.10), 0.020, 0.045, transform=ax.transAxes,
                               facecolor=c, edgecolor="none", clip_on=False))
        ax.text(x + 0.028, 1.122, t, transform=ax.transAxes, fontsize=12.5,
                color=CAT, va="center", fontproperties=FP)

    fast = sg.iloc[0]
    slow = sg.iloc[-1]
    share = slow.transit / slow.total * 100
    chrome(
        fig,
        "延迟的 93% 发生在承运之后，不在卖家手里",
        f"{fast.state} 全程 {fast.total:.1f} 天，{slow.state} {slow.total:.1f} 天；"
        f"{slow.state} 的 {share:.0f}% 耗在干线段——瓶颈是物流半径，不是备货",
        note_src("中位数；仅含已妥投订单，样本≥200 单的州"),
    )
    save(fig, "fig09_各州履约时长_甘特图.png")


if __name__ == "__main__":
    main()
