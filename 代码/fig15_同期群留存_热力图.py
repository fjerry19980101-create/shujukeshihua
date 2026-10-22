# -*- coding: utf-8 -*-
"""
fig15 同期群留存热力图 —— 复购到底漏在哪个月
===========================================
模型：Cohort 同期群分析（第 4.3 节）
读法：行=首购月份（同期群），列=首购后第 m 个月，
     格子深浅=该月仍有下单的客户占比。
结论：M+1 留存就跌破 1%——不是"慢慢流失"，而是"一次性交易"。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from matplotlib.colors import LinearSegmentedColormap

from _style import CAT, FP, WHITE, chrome, load, new_canvas, note_src, save

CMAP = LinearSegmentedColormap.from_list(
    "cohort", ["#1A1E43", "#24406B", "#2E86DE", "#3CC7C0", "#F2B705"])


def main():
    m = load("cohort_retention_matrix.csv").set_index("cohort")
    m = m.drop(columns=[c for c in m.columns if c == "Unnamed: 0"], errors="ignore")
    vals = m.values.astype(float)

    fig, ax = new_canvas(plot=(0.115, 0.20, 0.735, 0.475))
    im = ax.imshow(vals, aspect="auto", cmap=CMAP, vmin=0, vmax=1.2)
    ax.set_xticks(range(m.shape[1]))
    ax.set_xticklabels(["M+0"] + [f"M+{i}" for i in range(1, m.shape[1])],
                       fontsize=10.5, color=CAT, fontproperties=FP)
    ax.set_yticks(range(m.shape[0]))
    ax.set_yticklabels(m.index, fontsize=10.5, color=CAT, fontproperties=FP)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)

    # 只给 M+1..M+3 标数值，其余靠色阶（避免满屏数字）
    for i in range(m.shape[0]):
        for j in range(min(4, m.shape[1])):
            v = vals[i, j]
            if np.isnan(v):
                continue
            ax.text(j, i, f"{v:.1f}" if j else "100", ha="center", va="center",
                    fontsize=8.2, color="#0B1020" if v > 0.55 else WHITE,
                    fontproperties=FP)

    cb = fig.colorbar(im, ax=ax, fraction=0.020, pad=0.012)
    cb.set_label("留存率（%）", color=CAT, fontsize=11, fontproperties=FP)
    cb.ax.tick_params(colors=CAT, labelsize=9, length=0)
    cb.outline.set_visible(False)

    chrome(
        fig,
        "同期群留存：M+1 就跌破 1%，这不是漏，是不来",
        f"14 个同期群平均 M+1 留存 0.49%、M+6 仅 0.27%；"
        f"2017-11 群（黑五拉新）首月留存反而最低",
        note_src("仅保留首购于 2017.01–2018.02 的群，保证至少 6 个完整观察月"),
    )
    save(fig, "fig15_同期群留存_热力图.png")


if __name__ == "__main__":
    main()
