# -*- coding: utf-8 -*-
"""
fig22 反事实曲线 —— 承诺放宽到几天，延迟率能降到 5%
==================================================
模型：SLA 反事实模拟（第 4.7 节，基于 logistic 剂量-反应标定）
读法：横轴=统一承诺天数（自下单起），左轴=延迟率，右轴=期望差评率。
标记：橙色竖线=2018-08 的实际承诺中位数（13.4 天）。
关键：把承诺从 13 天放宽到 15 天，延迟率从 10.4% 降到 6.0%——
     只改"承诺"不改"运力"，就能拿回 4 个百分点的准时率。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from _style import ACCENT, CAT, FP, WHITE, chrome, load, new_canvas, note_src, save


def main():
    s = load("buffer_scenario.csv")
    t = load("late_trend_monthly.csv")
    cur_promise = float(t.estimated_days.iloc[-1])
    cur_late = float(t.late_rate.iloc[-1])

    fig, ax = new_canvas(plot=(0.115, 0.175, 0.735, 0.50))
    ax.plot(s.promised_days, s.late_rate_pct, color="#2E86DE", lw=2.6, label="延迟率 %")
    ax.fill_between(s.promised_days, s.late_rate_pct, color="#2E86DE", alpha=0.12)
    ax.set_xlabel("统一承诺时效（自下单起，天）", fontsize=11.5, color=CAT, labelpad=8,
                  fontproperties=FP)
    ax.set_ylabel("延迟率（%）", fontsize=11.5, color=CAT, labelpad=6,
                  fontproperties=FP)

    ax2 = ax.twinx()
    ax2.plot(s.promised_days, s.expected_bad_rate_pct, color=ACCENT, lw=1.8,
             ls=(0, (5, 3)), label="期望差评率 %")
    ax2.set_ylabel("期望差评率（%）", fontsize=11.5, color=CAT, labelpad=6,
                   fontproperties=FP)
    ax2.tick_params(labelsize=10)
    for sp in ax2.spines.values():
        sp.set_visible(False)

    ax.axvline(cur_promise, color=ACCENT, lw=1.6, ls=(0, (4, 3)), zorder=1)
    ax.scatter([cur_promise], [cur_late], s=110, color=ACCENT, zorder=7,
               edgecolors=WHITE, linewidths=1.0)
    ax.annotate(f"当前 {cur_promise:.1f} 天\n延迟 {cur_late:.1f}%",
                (cur_promise, cur_late), textcoords="offset points", xytext=(24, 34),
                fontsize=11.5, color=ACCENT, fontproperties=FP,
                arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1.0))

    # 5% 目标线
    target_day = float(s.loc[(s.late_rate_pct <= 5).idxmax(), "promised_days"]) \
        if (s.late_rate_pct <= 5).any() else np.nan
    if not np.isnan(target_day):
        ax.axhline(5, color="#3CC7C0", lw=1.2, ls=(0, (3, 3)), zorder=1)
        ax.annotate(f"承诺 {target_day:.0f} 天 → 延迟率 5%", (target_day, 5),
                    textcoords="offset points", xytext=(-10, 26), ha="right",
                    fontsize=11.5, color="#3CC7C0", fontproperties=FP,
                    arrowprops=dict(arrowstyle="->", color="#3CC7C0", lw=1.0))

    leg = ax.legend(loc="upper right", frameon=False, fontsize=11)
    for x in leg.get_texts():
        x.set_fontproperties(FP)
        x.set_color(CAT)

    chrome(
        fig,
        "只改承诺不改运力，也能把延迟率砍半",
        f"2018-08 实际承诺中位 {cur_promise:.1f} 天、延迟率 {cur_late:.1f}%；"
        f"若统一承诺 {target_day:.0f} 天，延迟率降至 5%、期望差评率同步下降",
        note_src("以 2018-08 实际时效分布为样本，配合 P(差评|c延迟天数) logistic 曲线"),
        title_size=27,
    )
    save(fig, "fig22_承诺时效反事实_曲线图.png")


if __name__ == "__main__":
    main()
