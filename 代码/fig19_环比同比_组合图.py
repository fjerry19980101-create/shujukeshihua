# -*- coding: utf-8 -*-
"""
fig19 环比/同比组合图 —— 增速的两个口径
======================================
模型：环比（MoM）/ 同比（YoY）（第 4.1 节）+ 名义-实际-美元三口径拆解
读法：柱=月度 GMV（万雷亚尔），左轴折线=环比%，右轴折线=同比%；
     2017 年没有同比基数，故同比线从 2018-01 才开始。
业务含义：同比 137% 看着漂亮，但其中 7.4 个百分点是通胀、24.6 个百分点是汇率——
        真实增长要打折。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from _style import ACCENT, CAT, FP, WHITE, chrome, load, kpi, new_canvas, note_src, save


def main():
    m = load("monthly_kpi.csv")
    x = np.arange(len(m))

    fig, ax = new_canvas(plot=(0.115, 0.175, 0.735, 0.50))
    ax.bar(x, m.gmv / 1e4, width=0.6, color="#1F4E79", edgecolor="none", zorder=2)
    ax.set_ylabel("月度 GMV（万雷亚尔）", fontsize=11.5, color=CAT, labelpad=6,
                  fontproperties=FP)
    ax.set_xticks(x)
    ax.set_xticklabels(m.purchase_month, rotation=42, ha="right", fontsize=9.5,
                       color=CAT, fontproperties=FP)
    ax.tick_params(labelsize=10)

    ax2 = ax.twinx()
    ax2.plot(x, m.mom_gmv_pct, color=ACCENT, lw=1.8, marker="o", ms=3.5, label="环比 %")
    mask = m.yoy_gmv_pct.notna()
    ax2.plot(x[mask], m.yoy_gmv_pct[mask], color="#3CC7C0", lw=2.2, marker="s", ms=4,
             label="同比 %")
    ax2.axhline(0, color="#8B90AD", lw=0.9, ls=(0, (4, 3)))
    ax2.set_ylabel("增速（%）", fontsize=11.5, color=CAT, labelpad=6, fontproperties=FP)
    ax2.tick_params(labelsize=10)
    for s in ax2.spines.values():
        s.set_visible(False)

    leg = ax2.legend(loc="upper left", ncol=2, frameon=False, fontsize=11)
    for t in leg.get_texts():
        t.set_fontproperties(FP)
        t.set_color(CAT)

    k = kpi()
    y = k["ytd_2018_vs_2017"]
    chrome(
        fig,
        "同比 137%？先扣掉通胀和汇率再说话",
        f"2018 年 1–8 月名义 GMV 同比 +{y['gmv_yoy_pct']:.0f}%，"
        f"实际价 +{y['gmv_real_yoy_pct']:.0f}%、美元口径 +{y['gmv_usd_yoy_pct']:.0f}%——"
        f"汇率吃掉了约 25 个百分点",
        note_src("实际价用 IPCA 平减至 2018-08 不变价；美元按 BCB 月均汇率折算"),
        title_size=28,
    )
    save(fig, "fig19_环比同比_组合图.png")


if __name__ == "__main__":
    main()
