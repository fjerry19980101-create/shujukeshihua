# -*- coding: utf-8 -*-
"""
fig17 SARIMA 预测图 —— 周 GMV 的点预测与 95% 置信区间
=====================================================
模型：SARIMA(2,1,2)(0,1,1,13)（第 4.6 节）
要点：① 历史实线、拟合虚线、预测实线三段区分；
     ② 95% 区间用半透明带填充（不许只画一条点预测线）；
     ③ 阴影带标注外推区间，回测段用竖向虚框圈出。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd

from _style import ACCENT, CAT, FP, WHITE, chrome, load, money, new_canvas, note_src, save


def main():
    f = load("forecast_weekly.csv")
    f["week"] = pd.to_datetime(f.week)
    hist = f[f.actual.notna()]
    fut = f[f.pred.notna() & f.actual.isna()]

    fig, ax = new_canvas()
    ax.plot(hist.week, hist.actual, color=WHITE, lw=1.5, label="实际周 GMV", zorder=4)
    ax.plot(hist.week, hist.fitted, color="#3CC7C0", lw=1.2, ls=(0, (4, 3)),
            label="模型拟合", zorder=3)
    ax.plot(fut.week, fut.pred, color=ACCENT, lw=2.0, label="点预测", zorder=4)
    ax.fill_between(fut.week, fut.lower95, fut.upper95, color=ACCENT, alpha=0.20,
                    zorder=2, label="95% 置信区间")

    # 外推起点分割
    ax.axvline(fut.week.iloc[0], color="#8B90AD", lw=1.0, ls=(0, (5, 4)), zorder=1)
    ax.text(fut.week.iloc[0], hist.actual.max() * 1.30, "  外推起点", fontsize=11,
            color="#8B90AD", fontproperties=FP, va="top")

    ax.set_ylim(0, hist.actual.max() * 1.42)
    ax.set_yticks([0, 1e5, 2e5, 3e5])
    ax.set_yticklabels(["0", "10万", "20万", "30万"], fontsize=11, color=CAT,
                       fontproperties=FP)
    leg = ax.legend(loc="upper left", ncol=2, frameon=False, fontsize=11,
                    handlelength=1.6, columnspacing=1.2)
    for t in leg.get_texts():
        t.set_fontproperties(FP)
        t.set_color(CAT)

    m = load("forecast_model_comparison.csv")
    sarima = m[m.model.str.startswith("SARIMA")].iloc[0]
    chrome(
        fig,
        "未来 12 周 GMV 点预测 281 万，但区间很宽",
        f"回测 MAPE {sarima.mape_pct:.1f}%、MASE {sarima.mase:.2f}"
        f"（<1 优于朴素预测）；周度噪声大，区间跨度约 ±60%，宜作预算情景而非精确目标",
        note_src("SARIMA(2,1,2)(0,1,1,13)；95% 区间为逐周区间，合计区间见论文 4.3.7 节"),
        title_size=27,
    )
    save(fig, "fig17_SARIMA预测_置信区间图.png")


if __name__ == "__main__":
    main()
