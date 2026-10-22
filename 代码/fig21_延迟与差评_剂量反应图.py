# -*- coding: utf-8 -*-
"""
fig21 剂量-反应图 —— 延迟几天，差评率就翻倍
==========================================
模型：延迟归因 + 满意度关联（第 4.7 节）
读法：横轴=相对承诺日的延迟天数分箱，左轴=差评率（柱），右轴=平均评分（线）。
关键：延迟 1–3 天差评率 19%，到 4–7 天直接跳到 60%——存在明确的"阈值效应"，
     这为"3 天内可控"的 SLA 目标提供了量化依据。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from _style import ACCENT, CAT, FP, WHITE, chrome, load, new_canvas, note_src, save


def main():
    b = load("late_vs_review_bins.csv")
    x = np.arange(len(b))

    fig, ax = new_canvas(plot=(0.115, 0.175, 0.735, 0.50))
    colors = ["#3CC7C0", "#3CC7C0", "#3CC7C0", ACCENT, "#ED7D31", "#D64550", "#D64550"]
    ax.bar(x, b.bad_rate, width=0.58, color=colors, edgecolor="none", zorder=2)
    for i, v in enumerate(b.bad_rate):
        ax.text(i, v + 2.2, f"{v:.0f}%", ha="center", va="bottom", fontsize=12,
                color=WHITE, fontproperties=FP)
    ax.set_ylabel("差评率（1–2 分，%）", fontsize=11.5, color=CAT, labelpad=6,
                  fontproperties=FP)
    ax.set_ylim(0, 92)
    ax.set_xticks(x)
    ax.set_xticklabels(b.delay_bin, rotation=22, ha="right", fontsize=11, color=CAT,
                       fontproperties=FP)

    ax2 = ax.twinx()
    ax2.plot(x, b.review, color="#F2F2F2", lw=2.0, marker="o", ms=5, zorder=6)
    ax2.set_ylim(1.2, 5.0)
    ax2.set_ylabel("平均评分", fontsize=11.5, color=CAT, labelpad=6, fontproperties=FP)
    ax2.tick_params(labelsize=10)
    for s in ax2.spines.values():
        s.set_visible(False)

    # 阈值分界
    ax.axvline(3.5, color="#8B90AD", lw=1.2, ls=(0, (5, 4)), zorder=1)
    ax.text(3.58, 82, "3 天是分水岭", fontsize=11.5, color="#8B90AD", fontproperties=FP)

    chrome(
        fig,
        "延迟 3 天内还能救，超过 4 天差评率翻三倍",
        f"延迟 1–3 天差评率 {b.bad_rate.iloc[3]:.0f}%，4–7 天升至 "
        f"{b.bad_rate.iloc[4]:.0f}%、8 天以上 {b.bad_rate.iloc[5]:.0f}%；"
        f"而准时订单仅 {b.bad_rate.iloc[0]:.0f}%",
        note_src("按实际妥投日 − 承诺日分箱；样本为已妥投订单"),
        title_size=27,
    )
    save(fig, "fig21_延迟与差评_剂量反应图.png")


if __name__ == "__main__":
    main()
