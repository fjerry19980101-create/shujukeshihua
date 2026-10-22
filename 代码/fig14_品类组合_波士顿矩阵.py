# -*- coding: utf-8 -*-
"""
fig14 波士顿矩阵 —— 品类组合的份额 × 增速定位
=============================================
模型：波士顿矩阵（第 4.4 节）
坐标：X = 相对份额（品类 GMV 份额 / 最大品类份额，线性 0–1），
     Y = 相对增速（品类实际增速 − 平台实际增速，百分点），0 线 = 跑赢大盘。
     分界 X=0.15（约对应"份额 1%"这一可运营门槛）、Y=0。
气泡：品类 GMV 规模。
排版：只用小板式图例（不用散点图例，否则图例圆点会大到压住副标题）；
     仅标注规模最大的 8 个品类，标签左右交替偏移，避免糊在一起。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from matplotlib.lines import Line2D

from _style import CAT, FP, WHITE, chrome, cn, load, new_canvas, note_src, save

QCOLOR = {"明星（Star）": "#F2B705", "现金牛（Cash Cow）": "#2E86DE",
          "问题（Question）": "#3CC7C0", "瘦狗（Dog）": "#6C7293"}


def main():
    b = load("bcg_matrix.csv").sort_values("gmv_total", ascending=False)
    plot_df = b.head(30).copy()
    label_df = b.head(8)

    fig, ax = new_canvas(plot=(0.115, 0.175, 0.775, 0.50))
    for q, g in plot_df.groupby("quadrant"):
        ax.scatter(g.rel_share, g.growth_rel_pct,
                   s=90 + 1500 * (g.gmv_total / b.gmv_total.max()),
                   color=QCOLOR.get(q, "#8B90AD"), alpha=0.55,
                   edgecolors=WHITE, linewidths=0.7, zorder=3)

    # 低份额 / 低增长区域压暗，形成四象限的空间感
    ax.axvspan(0, 0.15, color="#000000", alpha=0.12, zorder=0)
    ax.axhspan(-95, 0, color="#000000", alpha=0.12, zorder=0)

    for i, r in enumerate(label_df.itertuples()):
        dx, dy = (13, 7) if i % 2 == 0 else (-13, -21)
        ax.annotate(cn(r.category), (r.rel_share, r.growth_rel_pct),
                    textcoords="offset points", xytext=(dx, dy),
                    fontsize=10.5, color=WHITE, fontproperties=FP, zorder=6,
                    ha="left" if dx > 0 else "right")

    ax.axhline(0, color="#8B90AD", lw=1.0, ls=(0, (5, 4)), zorder=1)
    ax.axvline(0.15, color="#8B90AD", lw=1.0, ls=(0, (5, 4)), zorder=1)

    ax.set_xlim(-0.02, 1.15)
    ax.set_ylim(-95, 400)
    ax.set_xlabel("相对份额（最大品类 = 1）", fontsize=12, color=CAT, labelpad=8,
                  fontproperties=FP)
    ax.set_ylabel("相对增速 vs 大盘（百分点）", fontsize=12, color=CAT, labelpad=8,
                  fontproperties=FP)
    ax.tick_params(labelsize=11)

    for x, y, t in [(0.02, 372, "问题：高增长·低份额"), (0.32, 372, "明星：高增长·高份额"),
                    (0.02, -58, "瘦狗：低增长·低份额"), (0.32, -58, "现金牛：低增长·高份额")]:
        ax.text(x, y, t, fontsize=10.5, color="#5E6480", fontproperties=FP,
                va="top", ha="left", zorder=1)

    handles = [Line2D([], [], marker="o", ls="", markersize=9, markerfacecolor=c,
                      markeredgecolor=WHITE, markeredgewidth=0.7, label=q)
               for q, c in QCOLOR.items()]
    leg = ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.0, 1.005),
                    ncol=4, frameon=False, fontsize=11.5, handletextpad=0.35,
                    columnspacing=1.6)
    for t in leg.get_texts():
        t.set_fontproperties(FP)
        t.set_color(CAT)

    star = b[b.quadrant == "明星（Star）"]
    cow = b[b.quadrant == "现金牛（Cash Cow）"]
    dog = b[b.quadrant == "瘦狗（Dog）"]
    chrome(
        fig,
        "四个明星品类撑起三成 GMV，现金牛太少",
        f"明星 {len(star)} 个占 {star.gmv_total.sum()/b.gmv_total.sum()*100:.0f}%，"
        f"现金牛仅 {len(cow)} 个；瘦狗 {len(dog)} 个却仍占 "
        f"{dog.gmv_total.sum()/b.gmv_total.sum()*100:.0f}%，长尾需收缩",
        note_src("增速为 2018 年 1–8 月 vs 2017 年同期实际价 GMV；仅展示规模前 30 品类"),
        title_size=28,
    )
    save(fig, "fig14_品类组合_波士顿矩阵.png")


if __name__ == "__main__":
    main()
