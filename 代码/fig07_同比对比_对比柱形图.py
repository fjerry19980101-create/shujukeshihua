# -*- coding: utf-8 -*-
"""
fig07 对比柱形图 —— 2018 与 2017 同期 GMV
=========================================
复现模板：教材第 2 章《9 对比柱形图》
复现要点：同月两柱并排、深浅双色区分年份、柱顶标同比增速（不只标数值），
         图例在绘图区上方右对齐。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from matplotlib.patches import Rectangle

from _style import CAT, FP, chrome, load, money, new_canvas, note_src, save


def main():
    mo = load("monthly_kpi.csv")
    mo["ym"] = mo.purchase_month.str[5:7]
    mo["purchase_year"] = mo.purchase_month.str[:4].astype(int)
    a = mo[mo.purchase_year == 2017].set_index("ym").gmv
    b = mo[mo.purchase_year == 2018].set_index("ym").gmv
    months = [m for m in b.index if m in a.index]
    va = [a[m] for m in months]
    vb = [b[m] for m in months]
    top = max(max(va), max(vb))

    fig, ax = new_canvas()
    w = 0.34
    for i, m in enumerate(months):
        ax.add_patch(Rectangle(
            (i - w, 0), w, va[i], facecolor="#5B9BD5", edgecolor="none", zorder=2))
        ax.add_patch(Rectangle(
            (i, 0), w, vb[i], facecolor="#1F4E79", edgecolor="none", zorder=2))
        yoy = (vb[i] / va[i] - 1) * 100
        ax.text(i + w / 2, vb[i] + top * 0.03, f"+{yoy:.0f}%", ha="center", va="bottom",
                fontsize=12.5, color="#F2B705", fontproperties=FP)
        ax.text(i - w / 2, va[i] + top * 0.03, money(va[i]), ha="center", va="bottom",
                fontsize=10.5, color=CAT, fontproperties=FP)

    ax.set_xlim(-0.7, len(months) - 0.2)
    ax.set_ylim(0, top * 1.26)
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels([f"{int(m)}月" for m in months], fontsize=13, color=CAT,
                       fontproperties=FP)
    ax.set_yticks([])
    ax.grid(False)

    # 手绘图例（模板做法：不用 legend 框，直接画色块 + 文字）
    for x, c, t in [(0.02, "#5B9BD5", "2017 年"), (0.13, "#1F4E79", "2018 年")]:
        ax.add_patch(Rectangle(
            (x, 1.13), 0.022, 0.05, transform=ax.transAxes,
            facecolor=c, edgecolor="none", clip_on=False))
        ax.text(x + 0.032, 1.155, t, transform=ax.transAxes, fontsize=12.5,
                color=CAT, va="center", fontproperties=FP)

    g = (sum(vb) / sum(va) - 1) * 100
    chrome(
        fig,
        "同比翻倍，但增速在逐月收窄",
        f"1–8 月合计 {money(sum(vb))} 雷亚尔、同比 +{g:.0f}%，"
        f"增速从 +{((vb[0]/va[0])-1)*100:.0f}% 一路收窄到 "
        f"+{((vb[-1]/va[-1])-1)*100:.0f}%",
        note_src("名义 GMV（含运费），同月对同月比较"),
    )
    save(fig, "fig07_同比对比_对比柱形图.png")


if __name__ == "__main__":
    main()
