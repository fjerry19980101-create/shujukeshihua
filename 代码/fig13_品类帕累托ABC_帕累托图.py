# -*- coding: utf-8 -*-
"""
fig13 帕累托图（ABC 分类）—— 品类贡献的"二八"验证
=================================================
模型：帕累托 / ABC 分类（第 4.4 节）
读法：柱=单品类 GMV（降序），折线=累计占比；80% 处画横线，
     线与折线的交点左侧即 A 类（重点保供），80–95% 为 B 类，其余 C 类。
要点：帕累托图必须"柱 + 累计线 + 阈值线"三件套齐全，缺一则不可读。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from _style import ACCENT, CAT, FP, WHITE, chrome, cn, load, new_canvas, note_src, save


def main():
    p = load("pareto_categories.csv").head(22)
    x = np.arange(len(p))
    fig, ax = new_canvas()

    bars = ax.bar(x, p.share_pct, width=0.62, color="#2E86DE", edgecolor="none", zorder=2)
    for i, b in enumerate(bars):
        if p.abc.iloc[i] == "A":
            b.set_color("#1F4E79")
    ax.set_xticks(x)
    ax.set_xticklabels([cn(c) for c in p.category], rotation=38, ha="right",
                       fontsize=11, color=CAT, fontproperties=FP)
    ax.set_yticks([])
    ax.set_ylim(0, p.share_pct.max() * 1.35)

    ax2 = ax.twinx()
    ax2.plot(x, p.cum_share_pct, color=ACCENT, lw=2.2, marker="o", ms=4, zorder=6)
    ax2.axhline(80, color="#D64550", lw=1.4, ls=(0, (6, 4)), zorder=5)
    ax2.axhline(95, color="#8B90AD", lw=1.0, ls=(0, (3, 3)), zorder=5)
    ax2.set_ylim(0, 108)
    ax2.set_yticks([0, 25, 50, 80, 95, 100])
    ax2.set_yticklabels(["0", "25%", "50%", "80%", "95%", "100%"], fontsize=11, color=CAT,
                        fontproperties=FP)
    ax2.tick_params(length=0, pad=6)
    for s in ax2.spines.values():
        s.set_visible(False)
    ax2.text(len(p) - 0.4, 81.6, "80% 分界", ha="right", va="bottom", fontsize=11,
             color="#D64550", fontproperties=FP)

    n_a = int((p.abc == "A").sum())
    ax2.annotate(f"{n_a} 个品类到达 80%", xy=(n_a - 1, 80), xytext=(n_a + 1.2, 62),
                 fontsize=12, color=ACCENT, fontproperties=FP,
                 arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1.2))

    chrome(
        fig,
        "帕累托成立：17 个品类贡献八成 GMV",
        f"56 个品类中 A 类 {n_a} 个（占 30%）、贡献 80% 成交额；"
        f"后 39 个长尾品类合计不足 20%，应转为按需采购",
        note_src("A 类累计 ≤80%、B 类 80–95%、C 类 >95%；仅列前 22 个品类"),
    )
    save(fig, "fig13_品类帕累托ABC_帕累托图.png")


if __name__ == "__main__":
    main()
