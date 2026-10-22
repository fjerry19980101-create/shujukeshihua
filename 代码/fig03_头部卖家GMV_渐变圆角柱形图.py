# -*- coding: utf-8 -*-
"""
fig03 渐变圆角柱形图 —— 头部卖家 GMV
====================================
复现模板：教材第 2 章《3 渐变圆角柱形图》
复现要点：顶部圆角的竖向渐变柱（imshow + 圆角裁剪路径），
         柱顶白色数值、底部卖家序号标签、无 Y 轴刻度。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _style import (CAT, FP, WHITE, chrome, gradient_vbar_rounded, load, money,
                    new_canvas, note_src, save)

TOPN = 8


def main():
    sl = load("seller_stats_top200.csv").head(TOPN)
    vals = sl.gmv.tolist()
    labels = [f"S{i+1}" for i in range(len(vals))]
    top10 = load("seller_concentration.csv").cr10_pct.iloc[0]

    fig, ax = new_canvas()
    for i, v in enumerate(vals):
        gradient_vbar_rounded(ax, i, v, width=0.52, rounding=0.10)
        ax.text(i, v + max(vals) * 0.025, money(v), ha="center", va="bottom",
                fontsize=14.5, color=WHITE, fontproperties=FP)

    ax.set_xlim(-0.7, len(vals) - 0.3)
    ax.set_ylim(0, max(vals) * 1.26)
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(labels, fontsize=15, color=CAT, fontproperties=FP)
    ax.set_yticks([])
    ax.grid(False)

    chrome(
        fig,
        "头部卖家并不「头部」：CR10 仅 12.8%",
        f"GMV 第一名卖家仅占全站 {sl.gmv_share_pct.iloc[0]:.2f}%，"
        f"前十合计 {top10}%；卖家侧高度分散，议价权在平台",
        note_src("卖家 GMV 按订单明细归属，含运费；S1–S8 为 GMV 排名"),
    )
    save(fig, "fig03_头部卖家GMV_渐变圆角柱形图.png")


if __name__ == "__main__":
    main()
