# -*- coding: utf-8 -*-
"""
fig01 渐变柱形图 —— 品类 GMV 六强
=================================
复现模板：教材第 2 章《1 渐变柱形图》
复现要点：① 竖向蓝色渐变柱（顶亮底深）② 柱顶白色数值标签
         ③ 底部浅灰类目标签、无刻度线 ④ 深蓝底 + 白色粗体标题 + 一句话副标题
         ⑤ 左下角灰色*注脚*
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt
from _style import (CAT, FP, WHITE, chrome, cn, gradient_vbar, load,
                    money, new_canvas, note_src, save)


def main():
    cat = load("category_stats.csv").head(6)
    names = [cn(c) for c in cat.main_category]
    vals = cat.gmv.tolist()
    total = load("category_stats.csv").gmv.sum()

    fig, ax = new_canvas()
    ax.set_xlim(-0.6, 5.6)
    ax.set_ylim(0, max(vals) * 1.28)

    for i, v in enumerate(vals):
        gradient_vbar(ax, i, v, width=0.52)
        ax.text(i, v * 1.03, money(v), ha="center", va="bottom",
                fontsize=15, color=WHITE, fontproperties=FP)
    ax.set_xticks(range(6))
    ax.set_xticklabels(names, fontsize=14.5, color=CAT, fontproperties=FP)
    ax.set_yticks([])
    ax.grid(False)

    top_share = vals[0] / total * 100
    chrome(
        fig,
        "品类 GMV 六强：健康美妆一骑绝尘",
        f"健康美妆贡献 {money(vals[0])} 雷亚尔、占全站 {top_share:.1f}%，"
        f"第六名仅为头部的 {vals[-1]/vals[0]*100:.0f}%",
        note_src("金额为含运费的商品成交额，观察窗 2017.01–2018.08"),
    )
    save(fig, "fig01_品类GMV六强_渐变柱形图.png")


if __name__ == "__main__":
    main()
