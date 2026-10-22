# -*- coding: utf-8 -*-
"""
fig23 州级四象限 —— 市场贡献 vs 履约风险
=======================================
模型：地理聚类的组合管理视角（第 4.7 节延伸）
读法：X=GMV 占比（%），Y=延迟率（%），气泡=订单量，颜色=是否核心三州。
分界：X=3%（可称为"主力市场"的门槛），Y=全国平均延迟率 8.1%。
右上=大市场但履约差 → 优先级最高的整改对象。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from _style import ACCENT, CAT, FP, WHITE, chrome, load, new_canvas, note_src, save


def main():
    s = load("state_stats.csv").merge(
        load("state_delivery.csv")[["state", "late_rate", "delivery_days"]], on="state", how="inner")
    s = s[s.orders >= 300]
    avg_late = float((s.orders * s.late_rate).sum() / s.orders.sum())

    fig, ax = new_canvas()
    core = s.state.isin(["SP", "RJ", "MG"])
    ax.scatter(s.gmv_share_pct[core], s.late_rate[core],
               s=260 + 1600 * (s.orders[core] / s.orders.max()),
               color=ACCENT, alpha=0.62, edgecolors=WHITE, linewidths=0.8, zorder=3)
    ax.scatter(s.gmv_share_pct[~core], s.late_rate[~core],
               s=260 + 1600 * (s.orders[~core] / s.orders.max()),
               color="#2E86DE", alpha=0.55, edgecolors=WHITE, linewidths=0.8, zorder=3)

    for r in s.sort_values("gmv_share_pct", ascending=False).head(6).itertuples():
        ax.annotate(r.state, (r.gmv_share_pct, r.late_rate), textcoords="offset points",
                    xytext=(0, 15), ha="center", fontsize=11, color=WHITE,
                    fontproperties=FP, zorder=5)
    for r in s.sort_values("late_rate", ascending=False).head(5).itertuples():
        if r.gmv_share_pct > 8:
            continue
        ax.annotate(r.state, (r.gmv_share_pct, r.late_rate), textcoords="offset points",
                    xytext=(0, 15), ha="center", fontsize=11, color=WHITE,
                    fontproperties=FP, zorder=5)

    ax.axhline(avg_late, color="#8B90AD", lw=1.0, ls=(0, (5, 4)), zorder=1)
    ax.axvline(3, color="#8B90AD", lw=1.0, ls=(0, (5, 4)), zorder=1)
    ax.text(0.2, avg_late + 0.8, f"全国平均 {avg_late:.1f}%", fontsize=11, color="#8B90AD",
            fontproperties=FP)

    ax.set_xlabel("GMV 占比（%）", fontsize=12, color=CAT, labelpad=8, fontproperties=FP)
    ax.set_ylabel("延迟率（%）", fontsize=12, color=CAT, labelpad=8, fontproperties=FP)
    ax.set_xlim(0, s.gmv_share_pct.max() * 1.15)
    ax.set_ylim(0, s.late_rate.max() * 1.18)
    ax.tick_params(labelsize=11)

    hot = s[(s.gmv_share_pct >= 3) & (s.late_rate > avg_late)]
    chrome(
        fig,
        "大市场里只有 RJ 在拖后腿",
        f"SP 占 {s[s.state=='SP'].gmv_share_pct.iloc[0]:.1f}% GMV、延迟率 "
        f"{s[s.state=='SP'].late_rate.iloc[0]:.1f}%；RJ 占 "
        f"{s[s.state=='RJ'].gmv_share_pct.iloc[0]:.1f}% 却达 "
        f"{s[s.state=='RJ'].late_rate.iloc[0]:.1f}%，是唯一「大且差」的市场",
        note_src("仅含样本 ≥300 单的州；延迟率为已妥投订单口径"),
        title_size=28,
    )
    save(fig, "fig23_州级市场与履约_四象限.png")


if __name__ == "__main__":
    main()
