# -*- coding: utf-8 -*-
"""
fig24 K-Means 分群评估 —— 为什么选 k=4
======================================
模型：用户分群 K-Means（第 4.2 节，与 RFM 互为交叉验证）
读法：左图=轮廓系数随 k 的变化（统计最优在 k=2），右图=k=4 时四群的画像。
说明：k=2 的轮廓系数最高，但那只是"一次性 vs 复购"的二分，无法指导运营；
     k=4 轮廓系数 0.40，仍属可接受结构，且四群能一一对应动作——
     这是"统计最优"与"业务可用"之间的显式取舍，论文中如实披露。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from matplotlib.patches import Rectangle

from _style import ACCENT, CAT, FP, SEQ, WHITE, chrome, load, new_canvas, note_src, save


def main():
    sil = load("kmeans_silhouette.csv")
    prof = load("kmeans_profile.csv").sort_values("monetary", ascending=False)

    # 双面板：先建画布，再手工铺两个 axes（new_canvas 的默认单轴不适用）
    fig, _ = new_canvas()
    _.remove()
    ax1 = fig.add_axes([0.075, 0.175, 0.32, 0.50])
    ax2 = fig.add_axes([0.50, 0.175, 0.40, 0.50])
    for a in (ax1, ax2):
        a.set_facecolor("#1A1E43")
        for sp in ("top", "right"):
            a.spines[sp].set_visible(False)
        for sp in ("left", "bottom"):
            a.spines[sp].set_color("#404361")
        a.tick_params(colors=CAT, labelsize=10.5, length=0, pad=6)
        a.grid(axis="y", color="#404361", linestyle=(0, (8, 3)), linewidth=0.8)
        a.set_axisbelow(True)

    # ---- 左：轮廓系数 ----
    ax1.plot(sil.k, sil.silhouette, color="#2E86DE", lw=2.2, marker="o", ms=6)
    best = sil.loc[sil.silhouette.idxmax()]
    ax1.scatter([best.k], [best.silhouette], s=130, color=ACCENT, zorder=5,
                edgecolors=WHITE, linewidths=1.0)
    ax1.annotate(f"统计最优 k={int(best.k)}", (best.k, best.silhouette),
                 textcoords="offset points", xytext=(12, -2), fontsize=10.5,
                 color=ACCENT, fontproperties=FP)
    k4 = sil[sil.k == 4].iloc[0]
    ax1.scatter([4], [k4.silhouette], s=110, color="#3CC7C0", zorder=5,
                edgecolors=WHITE, linewidths=1.0)
    ax1.annotate(f"业务采用 k=4\n轮廓 {k4.silhouette:.2f}", (4, k4.silhouette),
                 textcoords="offset points", xytext=(10, 18), fontsize=10.5,
                 color="#3CC7C0", fontproperties=FP)
    ax1.set_xlabel("聚类数 k", fontsize=11, color=CAT, labelpad=6, fontproperties=FP)
    ax1.set_ylabel("轮廓系数", fontsize=11, color=CAT, labelpad=6, fontproperties=FP)
    ax1.set_title("轮廓系数随 k 变化", fontsize=12, color=WHITE, pad=10,
                  fontproperties=FP)

    # ---- 右：四群画像（人均消费 & GMV 占比） ----
    y = np.arange(len(prof))
    ax2.barh(y - 0.18, prof.monetary, height=0.34, color="#2E86DE", edgecolor="none",
             label="人均消费（雷亚尔）")
    for i, v in enumerate(prof.monetary):
        ax2.text(v + 6, i - 0.18, f"{v:.0f}", va="center", fontsize=10, color=WHITE,
                 fontproperties=FP)
    ax3 = ax2.twiny()
    ax3.barh(y + 0.18, prof.gmv_share_pct, height=0.34, color=ACCENT, edgecolor="none",
             alpha=0.85, label="GMV 占比（%）")
    for i, v in enumerate(prof.gmv_share_pct):
        ax3.text(v + 1.0, i + 0.18, f"{v:.1f}%", va="center", fontsize=10, color=ACCENT,
                 fontproperties=FP)
    ax2.set_yticks(y)
    ax2.set_yticklabels(prof.cluster_label, fontsize=11, color=CAT, fontproperties=FP)
    ax2.set_xlim(0, prof.monetary.max() * 1.30)
    ax3.set_xlim(0, prof.gmv_share_pct.max() * 1.35)
    ax3.tick_params(colors=CAT, labelsize=10, length=0)
    for sp in ax3.spines.values():
        sp.set_visible(False)
    ax2.set_title("四群画像（k=4）", fontsize=12, color=WHITE, pad=10,
                  fontproperties=FP)
    ax2.grid(False)

    chrome(
        fig,
        "K-Means 与 RFM 互相印证：高客单沉睡客是最大金矿",
        f"k=4 下「复购型高价值」仅 {prof[prof.cluster_label=='复购型高价值'].customers_pct.iloc[0]:.1f}% 客户，"
        f"却贡献 {prof[prof.cluster_label=='复购型高价值'].gmv_share_pct.iloc[0]:.1f}% GMV；"
        f"「高客单沉睡客」占 {prof[prof.cluster_label=='高客单沉睡客'].customers_pct.iloc[0]:.0f}% 客户、"
        f"{prof[prof.cluster_label=='高客单沉睡客'].gmv_share_pct.iloc[0]:.1f}% GMV",
        note_src("特征取 log(R)、log(F)、log(M) 后标准化；轮廓系数在 1 万抽样上估计"),
        title_size=26,
    )
    save(fig, "fig24_KMeans分群评估_双面板.png")


if __name__ == "__main__":
    main()
