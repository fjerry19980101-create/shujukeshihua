# -*- coding: utf-8 -*-
"""
fig04 标注柱形图 —— 月度订单量的双峰
====================================
复现模板：教材第 2 章《4 标注柱形图》
复现要点：柱体渐变 + 关键柱的引线标注（折线 + 圆点 + 文字），
         只标注"值得说"的那几根，其余不标——这是模板的克制原则。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt

from _style import ACCENT, CAT, FP, WHITE, chrome, gradient_vbar, load, new_canvas, note_src, save


def main():
    mo = load("monthly_kpi.csv")
    x = range(len(mo))
    vals = mo.orders.tolist()
    peak = int(mo.orders.idxmax())
    last = len(mo) - 1

    fig, ax = new_canvas()
    for i, v in enumerate(vals):
        gradient_vbar(ax, i, v, width=0.62)
    # 峰值柱单独用暖色强调（重绘一次覆盖）
    ax.add_patch(plt.Rectangle((peak - 0.31, 0), 0.62, vals[peak],
                               facecolor=ACCENT, edgecolor="none", alpha=0.92, zorder=2))

    # 峰值：竖线引到上方，文字居中于柱顶
    ax.plot([peak, peak], [vals[peak] + max(vals) * 0.02, vals[peak] * 1.24],
            color=ACCENT, lw=1.2, ls=(0, (4, 3)), zorder=5)
    ax.text(peak, vals[peak] * 1.27, f"黑五脉冲 {vals[peak]:,} 单",
            ha="center", va="bottom", fontsize=13.5, color=ACCENT, fontproperties=FP)
    # 末月：引到右上方，避免与峰值标注重叠
    ax.plot([last, last], [vals[last] + max(vals) * 0.02, max(vals) * 1.16],
            color=WHITE, lw=1.0, ls=(0, (3, 3)), zorder=5)
    ax.text(last + 0.15, max(vals) * 1.17, f"{vals[last]:,} 单\n（8 月完整月）",
            ha="right", va="bottom", fontsize=12.5, color=WHITE, fontproperties=FP)

    ax.set_xlim(-0.8, len(vals) - 0.2)
    ax.set_ylim(0, max(vals) * 1.55)
    ax.set_xticks(list(x))
    ax.set_xticklabels([m[2:] for m in mo.purchase_month], fontsize=11, color=CAT,
                       rotation=0, fontproperties=FP)
    ax.set_yticks([])
    ax.grid(False)

    chrome(
        fig,
        "订单量的两个台阶：黑五脉冲与年度翻倍",
        f"{mo.purchase_month[peak]} 单月 {vals[peak]:,} 单为全期峰值，是月均 "
        f"{mo.orders.mean():,.0f} 单的 {vals[peak]/mo.orders.mean():.1f} 倍",
        note_src("横轴为月份（年份后两位），观察窗 2017.01–2018.08"),
    )
    save(fig, "fig04_月度订单量_标注柱形图.png")


if __name__ == "__main__":
    main()
