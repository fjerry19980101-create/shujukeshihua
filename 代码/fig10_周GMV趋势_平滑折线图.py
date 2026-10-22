# -*- coding: utf-8 -*-
"""
fig10 平滑折线图 —— 周 GMV 的噪声与趋势
=======================================
复现模板：教材第 2 章《11 平滑折线图》
复现要点：原始折线压暗作背景、平滑曲线（三次样条）作前景、
         关键区间用竖向色带标记（黑五前后），让"趋势"与"波动"同时可见。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from scipy.interpolate import make_interp_spline

from _style import ACCENT, CAT, FP, WHITE, chrome, load, money, new_canvas, note_src, save


def main():
    wk = load("weekly_kpi.csv")
    wk["week"] = pd.to_datetime(wk.purchase_week)
    wk = wk.iloc[1:-1].reset_index(drop=True)      # 去首尾不完整周
    x = np.arange(len(wk))
    y = wk.gmv.values
    smooth = make_interp_spline(x, y, k=3)(np.linspace(0, len(wk) - 1, 400))
    xs = np.linspace(0, len(wk) - 1, 400)

    fig, ax = new_canvas()
    ax.plot(x, y, color="#3A4470", lw=1.2, zorder=2)
    ax.fill_between(xs, smooth, smooth.min() * 0.55, color="#2E86DE", alpha=0.10, zorder=1)
    ax.plot(xs, smooth, color="#2E86DE", lw=2.6, zorder=3)

    # 黑五区间竖带
    bf = wk[wk.week.between("2017-11-20", "2017-11-27")]
    if len(bf):
        i0 = int(bf.index[0])
        ax.axvspan(i0 - 0.4, i0 + 0.4, color=ACCENT, alpha=0.16, zorder=0)
        ax.text(i0, y.max() * 1.10, "黑五周", ha="center", va="bottom",
                fontsize=12.5, color=ACCENT, fontproperties=FP)

    ax.set_xlim(-1, len(wk))
    ax.set_ylim(y.min() * 0.55, y.max() * 1.24)
    step = 12
    ax.set_xticks(list(range(0, len(wk), step)))
    ax.set_xticklabels([wk.week.iloc[i].strftime("%y-%m") for i in range(0, len(wk), step)],
                       fontsize=12, color=CAT, fontproperties=FP)
    ax.set_yticks([])
    ax.grid(False)

    cv = y.std() / y.mean() * 100
    chrome(
        fig,
        "周 GMV 的锯齿是常态，趋势线才是决策依据",
        f"周均 {money(y.mean())} 雷亚尔、变异系数 {cv:.0f}%；"
        f"平滑后可见 2017 年末到 2018 年初的一次台阶式跃迁",
        note_src("灰线为原始周序列，蓝线为三次样条平滑；已剔除首尾不完整周"),
    )
    save(fig, "fig10_周GMV趋势_平滑折线图.png")


if __name__ == "__main__":
    main()
