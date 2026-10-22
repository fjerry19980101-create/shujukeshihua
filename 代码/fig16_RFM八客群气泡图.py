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

from _style import ACCENT, CAT, FP, WHITE, chrome, load, new_canvas, note_src, save

COLORS = {"重要价值客户": "#F2B705", "重要唤回客户": "#ED7D31",
          "重要深耕客户": "#2E86DE", "重要挽留客户": "#6C5CE7",
          "一般价值客户": "#3CC7C0", "一般保持客户": "#7FB3D5",
          "一般发展客户": "#8E7CF0", "一般挽留客户": "#6C7293"}


def main():
    s = load("rfm_segments.csv")

    fig, ax = new_canvas()
    # 逐个指定标签偏移：高价值四群标在上方，低价值四群分列左右，彻底避免压字
    OFF = {"重要价值客户": (0, 30, "center"), "重要唤回客户": (0, 30, "center"),
           "重要深耕客户": (0, 34, "center"), "重要挽留客户": (0, 34, "center"),
           "一般价值客户": (46, 6, "left"), "一般发展客户": (-46, 6, "right"),
           "一般保持客户": (46, 6, "left"), "一般挽留客户": (-46, 6, "right")}

    for r in s.itertuples():
        ax.scatter(r.avg_recency, r.avg_monetary,
                   s=260 + 2600 * (r.customers / s.customers.max()),
                   color=COLORS.get(r.segment, "#8B90AD"), alpha=0.62,
                   edgecolors=WHITE, linewidths=0.9, zorder=3)
        dx, dy, ha = OFF.get(r.segment, (0, 26, "center"))
        ax.annotate(f"{r.segment}\n{r.customer_share_pct:.1f}% 客户 / {r.gmv_share_pct:.1f}% GMV",
                    (r.avg_recency, r.avg_monetary), textcoords="offset points",
                    xytext=(dx, dy), ha=ha, fontsize=9.8, color=WHITE,
                    fontproperties=FP, zorder=5)

    ax.axvline(s.avg_recency.median(), color="#8B90AD", lw=1.0, ls=(0, (5, 4)), zorder=1)
    ax.axhline(s.avg_monetary.median(), color="#8B90AD", lw=1.0, ls=(0, (5, 4)), zorder=1)
    ax.set_xlabel("平均最近购买间隔 R（天，越左越活跃）", fontsize=12, color=CAT, labelpad=8,
                  fontproperties=FP)
    ax.set_ylabel("平均累计消费 M（雷亚尔）", fontsize=12, color=CAT, labelpad=8,
                  fontproperties=FP)
    ax.set_xlim(-15, s.avg_recency.max() * 1.18)
    ax.set_ylim(0, s.avg_monetary.max() * 1.30)
    ax.tick_params(labelsize=11)

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
