# -*- coding: utf-8 -*-
"""
fig11 单值圆环图 —— 准时交付率
=============================
复现模板：教材第 2 章《14 单值圆环图》
复现要点：整张图只讲一个数：粗环 + 中央巨号数字 + 环缺口指示剩余比例，
         没有任何坐标轴。适用于大屏 KPI 卡与报告"一句话结论"页。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from matplotlib.patches import Wedge

from _style import ACCENT, CAT, FP, FPB, WHITE, chrome, kpi, new_canvas, note_src, save


def main():
    k = kpi()
    val = 100 - k["late_rate_pct"]          # 准时率
    fig = __import__("matplotlib").pyplot.figure(figsize=(1088 / 100, 794 / 100), dpi=100,
                                                facecolor="#1A1E43")
    ax = fig.add_axes([0.22, 0.03, 0.56, 0.76])
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.35)
    ax.axis("off")
    ax.set_aspect("equal")

    R, w = 1.0, 0.20
    # 底环
    ax.add_patch(Wedge((0, 0), R, 0, 360, width=w, facecolor="#2B3160", edgecolor="none"))
    # 进度环：从 90° 顺时针
    theta = val / 100 * 360
    ax.add_patch(Wedge((0, 0), R, 90 - theta, 90, width=w,
                       facecolor="#2E86DE", edgecolor="none"))
    # 进度环末端加一个高亮小段，强化"进度感"
    ax.add_patch(Wedge((0, 0), R, 90 - theta - 3, 90 - theta, width=w,
                       facecolor=ACCENT, edgecolor="none"))

    ax.text(0, 0.10, f"{val:.1f}%", ha="center", va="center", fontsize=64,
            color=WHITE, fontproperties=FPB)
    ax.text(0, -0.24, "准时交付率", ha="center", va="center", fontsize=19,
            color=CAT, fontproperties=FP)
    ax.text(0, -0.50, f"延迟 {k['late_rate_pct']}%｜{k['late_orders']:,} 单",
            ha="center", va="center", fontsize=13.5, color=ACCENT, fontproperties=FP)

    chrome(
        fig,
        "每 12 单就有 1 单超出承诺时间",
        f"准时率 {val:.1f}% 看似健康，但延迟单的评分是 {k['review_late']} 分，"
        f"比准时单低 {k['review_ontime']-k['review_late']:.2f} 分",
        note_src("口径：已妥投且未截尾订单，延迟=实际妥投日晚于承诺日"),
    )
    save(fig, "fig11_准时交付率_单值圆环图.png")


if __name__ == "__main__":
    main()
