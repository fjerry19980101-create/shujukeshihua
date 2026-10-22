# -*- coding: utf-8 -*-
"""
fig06 蝴蝶图 —— 各州准时与延迟的结构对比
========================================
复现模板：教材第 2 章《6/7 蝴蝶图》
复现要点：左右对称的双向条形（左侧取负值），州名置于中轴，
         两翼分别用蓝/橙对比色，两端标数值与延迟率。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from _style import CAT, FP, ORANGE, WHITE, chrome, load, new_canvas, note_src, save


def main():
    st = load("state_delivery.csv").sort_values("orders", ascending=False).head(10)
    st = st.iloc[::-1]                       # 由下往上排，最大的在最上方
    on_time = (st.orders * (1 - st.late_rate / 100)).round(0).astype(int)
    late = (st.orders - on_time).astype(int)

    fig, ax = new_canvas(plot=(0.145, 0.155, 0.755, 0.55))
    y = np.arange(len(st))
    ax.barh(y, -on_time, height=0.62, color="#2E86DE", edgecolor="none", zorder=2)
    ax.barh(y, late, height=0.62, color=ORANGE, edgecolor="none", zorder=2)

    for i, (o, l) in enumerate(zip(on_time, late)):
        ax.text(-o - max(on_time) * 0.012, i, f"{o:,}", ha="right", va="center",
                fontsize=11.5, color=WHITE, fontproperties=FP)
        ax.text(l + max(on_time) * 0.012, i, f"{l:,}（{st.iloc[i].late_rate:.1f}%）",
                ha="left", va="center", fontsize=11.5, color=ORANGE, fontproperties=FP)

    ax.set_yticks(y)
    ax.set_yticklabels(st.state, fontsize=14, color=CAT, fontproperties=FP)
    ax.set_xlim(-max(on_time) * 1.30, max(on_time) * 0.42)
    ax.set_xticks([])
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)
    ax.axvline(0, color="#6C6F8A", lw=1.0, zorder=3)

    ax.text(max(on_time) * 0.40, len(st) - 0.35, "延迟单", ha="right", va="bottom",
            fontsize=13, color=ORANGE, fontproperties=FP)
    ax.text(-max(on_time) * 1.28, len(st) - 0.35, "准时单", ha="left", va="bottom",
            fontsize=13, color="#2E86DE", fontproperties=FP)

    worst = st.sort_values("late_rate", ascending=False).iloc[0]
    chrome(
        fig,
        "单量在 SP，延迟在东北部",
        f"SP 贡献 {st.loc[st.state=='SP','orders'].iloc[0]:,} 单却仅 "
        f"{st.loc[st.state=='SP','late_rate'].iloc[0]:.1f}% 延迟；"
        f"{worst.state} 延迟率高达 {worst.late_rate:.1f}%，是 SP 的 "
        f"{worst.late_rate/st.loc[st.state=='SP','late_rate'].iloc[0]:.1f} 倍",
        note_src("仅统计已妥投订单，按订单量取前十州"),
    )
    save(fig, "fig06_各州准时与延迟_蝴蝶图.png")


if __name__ == "__main__":
    main()
