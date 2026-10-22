# -*- coding: utf-8 -*-
"""
fig16 RFM 客群气泡图 —— 八分类的坐标定位
========================================
模型：RFM 八分类（第 4.2 节）
读法：X=平均最近购买间隔 R（天，越左越活跃），Y=平均累计消费 M（雷亚尔），
     气泡大小=客群人数，颜色=八个分类。
     右上=（近、贵）→ 核心；左上=（远、贵）→ 沉睡的高价值，最该召回。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from matplotlib.lines import Line2D

from _style import ACCENT, CAT, FP, WHITE, chrome, load, new_canvas, note_src, save

COLORS = {"重要价值客户": "#F2B705", "重要唤回客户": "#ED7D31",
          "重要深耕客户": "#2E86DE", "重要挽留客户": "#6C5CE7",
          "一般价值客户": "#3CC7C0", "一般保持客户": "#7FB3D5",
          "一般发展客户": "#8E7CF0", "一般挽留客户": "#6C7293"}


def main():
    s = load("rfm_segments.csv")

    # 右侧留出图例位置，气泡上只标两个最大的客群，避免标签互相压字
    fig, ax = new_canvas(plot=(0.095, 0.175, 0.56, 0.50))
    # 逐个指定标签偏移：高价值四群标在上方，低价值四群分列左右，彻底避免压字
    # 两个大泡泡的标签往两侧让，小泡泡在上方/两侧，避免任何压字

    for r in s.itertuples():
        ax.scatter(r.avg_recency, r.avg_monetary,
                   s=260 + 2600 * (r.customers / s.customers.max()),
                   color=COLORS.get(r.segment, "#8B90AD"), alpha=0.62,
                   edgecolors=WHITE, linewidths=0.9, zorder=3,
                   label=f"{r.segment}  {r.customer_share_pct:.1f}% / {r.gmv_share_pct:.1f}%")
        # 只给两个最大的气泡加直接标注，其余交给图例，避免任何压字
        if r.segment in ("重要深耕客户", "重要挽留客户"):
            ax.annotate(r.segment, (r.avg_recency, r.avg_monetary),
                        textcoords="offset points", xytext=(0, 92), ha="center",
                        fontsize=11, color=WHITE, fontproperties=FP, zorder=6)

    ax.axvline(s.avg_recency.median(), color="#8B90AD", lw=1.0, ls=(0, (5, 4)), zorder=1)
    ax.axhline(s.avg_monetary.median(), color="#8B90AD", lw=1.0, ls=(0, (5, 4)), zorder=1)
    ax.set_xlabel("平均最近购买间隔 R（天，越左越活跃）", fontsize=12, color=CAT, labelpad=8,
                  fontproperties=FP)
    ax.set_ylabel("平均累计消费 M（雷亚尔）", fontsize=12, color=CAT, labelpad=8,
                  fontproperties=FP)
    ax.set_xlim(-15, s.avg_recency.max() * 1.18)
    ax.set_ylim(0, s.avg_monetary.max() * 1.30)
    ax.tick_params(labelsize=11)

    # 自绘图例句柄（散点自带的图例圆点会跟随气泡尺寸，大到压住文字）
    handles = [Line2D([], [], marker="o", ls="", markersize=8,
                      markerfacecolor=COLORS.get(r.segment, "#8B90AD"),
                      markeredgecolor="white", markeredgewidth=0.6,
                      label=f"{r.segment}  {r.customer_share_pct:.1f}% / {r.gmv_share_pct:.1f}%")
               for r in s.sort_values("gmv_share_pct", ascending=False).itertuples()]
    leg = ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.02, 0.5),
                    frameon=False, fontsize=9.5, handletextpad=0.4, labelspacing=0.85,
                    title="客群  客户占比 / GMV 占比")
    leg.get_title().set_fontproperties(FP)
    leg.get_title().set_color(CAT)
    leg.get_title().set_fontsize(10)
    for t in leg.get_texts():
        t.set_fontproperties(FP)
        t.set_color("#C9D0EE")

    key = s.sort_values("gmv_share_pct", ascending=False).head(2)
    chrome(
        fig,
        "RFM 气泡：最有价值的两群，一群近、一群远",
        f"{key.iloc[0].segment}（{key.iloc[0].gmv_share_pct:.1f}% GMV）平均 "
        f"{key.iloc[0].avg_recency:.0f} 天未复购；"
        f"{key.iloc[1].segment}则已沉睡 {key.iloc[1].avg_recency:.0f} 天",
        note_src("气泡大小=客群人数；虚线=各维度中位数；R 越小越活跃"),
        title_size=28,
    )
    save(fig, "fig16_RFM八客群气泡图.png")


if __name__ == "__main__":
    main()
