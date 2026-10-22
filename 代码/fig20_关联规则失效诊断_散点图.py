# -*- coding: utf-8 -*-
"""
fig20 关联规则散点图 —— 为什么 Apriori 在这份数据上失效
=====================================================
模型：Apriori / 关联规则（第 4.5 节）
读法：X=共现支持度（%），Y=共现增益（实际共现 / 独立假设下的期望共现），
     气泡=共现订单数，红色虚线=1.0（独立）。
关键：所有点都在 1.0 以下——共现比随机还少，这是"单件购买"结构的必然结果。
     与其硬凑 lift>1 的规则，不如直接说"这个平台没有购物篮"。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from _style import ACCENT, CAT, FP, WHITE, chrome, cn, load, new_canvas, note_src, save


def main():
    p = load("basket_top_pairs.csv").head(24)
    fig, ax = new_canvas()

    sizes = 300 + 2400 * (p.n_pair_orders / p.n_pair_orders.max())
    ax.scatter(p.support_pct, p.cooccur_lift, s=sizes, color="#2E86DE", alpha=0.55,
               edgecolors=WHITE, linewidths=0.7, zorder=3)
    ax.axhline(1.0, color="#D64550", lw=1.4, ls=(0, (6, 4)), zorder=2)
    ax.text(ax.get_xlim()[1], 1.02, "独立基准 lift=1", ha="right", va="bottom",
            fontsize=11.5, color="#D64550", fontproperties=FP)

    for i, r in enumerate(p.head(6).itertuples()):
        ax.annotate(f"{cn(r.category_x)}+{cn(r.category_y)}",
                    (r.support_pct, r.cooccur_lift), textcoords="offset points",
                    xytext=(0, 18), ha="center", fontsize=9.5, color=WHITE,
                    fontproperties=FP, zorder=5)

    ax.set_xlabel("共现支持度（占全部订单 %）", fontsize=12, color=CAT, labelpad=8,
                  fontproperties=FP)
    ax.set_ylabel("共现增益（实际 / 随机期望）", fontsize=12, color=CAT, labelpad=8,
                  fontproperties=FP)
    ax.set_ylim(0, max(1.15, p.cooccur_lift.max() * 1.25))
    ax.set_xlim(0, p.support_pct.max() * 1.15)
    ax.tick_params(labelsize=11)

    d = load("basket_diagnosis.csv").iloc[0]
    chrome(
        fig,
        "所有品类对都落在 lift=1 以下：这不是关联，是互斥",
        f"多品类订单仅占 {d.multi_category_order_pct}%，最高共现对只有 "
        f"{int(p.n_pair_orders.max())} 单；唯一通过门槛的规则 lift={d.lift_median:.2f}，"
        f"不具捆绑可执行性",
        note_src("支持度门槛由「至少 50 单」反推为 0.05%；气泡大小=共现订单数"),
        title_size=27,
    )
    save(fig, "fig20_关联规则失效诊断_散点图.png")


if __name__ == "__main__":
    main()
