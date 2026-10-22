# -*- coding: utf-8 -*-
"""
fig02 带均值柱形图 —— 各州客单价与全国基准
==========================================
复现模板：教材第 2 章《2 带均值柱形图》
复现要点：① 柱体渐变 ② 一条贯穿全图的黄色均值基准线
         ③ 线尾橙色"平均值：xxx"标注 ④ 高低柱分别用白/浅灰数值标签强调差异
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _style import (ACCENT, CAT, FP, FP, FPB, WHITE, chrome, gradient_vbar,
                    load, new_canvas, note_src, save)

TOPN = 10


def main():
    st = load("state_stats.csv").sort_values("orders", ascending=False).head(TOPN)
    names, vals = st.state.tolist(), st.aov.tolist()
    # 全国客单价必须用"总GMV/总订单"加权计算，不能对各州客单价取简单平均（会被小州拉高）
    allst = load("state_stats.csv")
    overall = allst.gmv.sum() / allst.orders.sum()

    fig, ax = new_canvas()
    for i, v in enumerate(vals):
        gradient_vbar(ax, i, v, width=0.5)
        ax.text(i, v + max(vals) * 0.03, f"{v:,.0f}", ha="center", va="bottom",
                fontsize=14, color=WHITE, fontproperties=FP)

    ax.axhline(overall, color=ACCENT, linewidth=2.2, zorder=4)
    ax.text(-0.62, overall + max(vals) * 0.03, f"全国平均：{overall:,.0f}",
            ha="left", va="bottom", fontsize=14, color=ACCENT, fontproperties=FP)

    ax.set_xlim(-0.7, len(vals) - 0.3)
    ax.set_ylim(0, max(vals) * 1.28)
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(names, fontsize=15, color=CAT, fontproperties=FP)
    ax.set_yticks([])
    ax.grid(False)

    hi = st.sort_values("aov").iloc[-1]      # 客单价最高
    lo = st.sort_values("aov").iloc[0]
    chrome(
        fig,
        "客单价：东北部与中西部更高，圣保罗反而垫底",
        f"{hi.state} 客单价 {hi.aov:,.0f} 雷亚尔居首，最大市场 SP 仅 "
        f"{float(st[st.state=='SP'].aov.iloc[0]):,.0f}，低于全国加权均值 {overall:,.0f}",
        note_src("按订单量取前十州；客单价 = GMV / 订单数"),
    )
    save(fig, "fig02_各州客单价对比_带均值柱形图.png")


if __name__ == "__main__":
    main()
