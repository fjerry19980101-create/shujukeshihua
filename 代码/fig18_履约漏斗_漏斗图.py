# -*- coding: utf-8 -*-
"""
fig18 履约漏斗图 —— 订单生命周期逐级漏损
=======================================
模型：漏斗转化分析（第 4.7 节）
读法：自上而下五级，块宽按留存比例收缩，右侧标"环节转化率"，
     最后一跳（妥投→好评）是最大漏口，也是本项目的核心命题。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from matplotlib.patches import Polygon

from _style import ACCENT, CAT, FP, WHITE, chrome, load, new_canvas, note_src, save

COLORS = ["#1F4E79", "#2E75B6", "#2E86DE", "#3CC7C0", "#ED7D31"]


def main():
    st = load("funnel_stages.csv")
    n = len(st)
    fig, ax = new_canvas(plot=(0.10, 0.13, 0.62, 0.58))

    base = st.orders.iloc[0]
    h = 0.62
    for i, r in st.iterrows():
        w = r.orders / base
        y = n - i
        ax.add_patch(Polygon([[-w / 2, y + h / 2], [w / 2, y + h / 2],
                              [w / 2 * 0.94, y - h / 2], [-w / 2 * 0.94, y - h / 2]],
                             closed=True, facecolor=COLORS[i], alpha=0.92,
                             edgecolor="none", zorder=2))
        ax.text(0, y, f"{r.stage}", ha="center", va="center", fontsize=13,
                color=WHITE, fontproperties=FP, zorder=4)
        ax.text(w / 2 + 0.035, y, f"{r.orders:,}", ha="left", va="center",
                fontsize=12.5, color=WHITE, fontproperties=FP)
        if i > 0:
            ax.text(0.20, y + 0.31, f"↓ {r.stage_rate_pct:.1f}%", ha="left", va="center",
                    fontsize=11.5, color=ACCENT, fontproperties=FP)

    ax.set_xlim(-0.62, 0.78)
    ax.set_ylim(0.25, n + 0.85)
    ax.axis("off")

    d = st.iloc[-1]
    convert = d.orders / base * 100
    chrome(
        fig,
        "五级漏斗：最后一步掉了 22 个百分点",
        f"下单→妥投转化 {st.iloc[3].overall_rate_pct:.1f}%，但妥投→好评仅 "
        f"{d.stage_rate_pct:.1f}%；末端体验才是转化率的真正瓶颈，端到端 {convert:.1f}%",
        note_src("好评定义为评分 4–5 分；样本为观察窗内 99,092 单"),
        title_size=28,
    )
    save(fig, "fig18_履约漏斗_漏斗图.png")


if __name__ == "__main__":
    main()
