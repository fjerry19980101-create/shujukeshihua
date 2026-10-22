# -*- coding: utf-8 -*-
"""
fig08 数值百分比 —— 订单状态构成
================================
复现模板：教材第 2 章《8 数值百分比》
复现要点：横向条形 + 右端百分比标签 + 条形按占比排序，
         用"百分号"直接替代坐标轴，读者一眼拿到结构信息。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _style import CAT, FP, WHITE, chrome, gradient_hbar, load, new_canvas, note_src, save

LABEL = {"delivered": "已妥投", "shipped": "运输中", "canceled": "已取消",
         "unavailable": "缺货无法履约", "invoiced": "已开票待发", "processing": "处理中",
         "created": "仅创建", "approved": "已审批待发"}


def main():
    st = load("order_status_share.csv").sort_values("orders")
    n = len(st)
    labels = [LABEL.get(s, s) for s in st.order_status]
    vals = st.share_pct.tolist()

    fig, ax = new_canvas(plot=(0.245, 0.155, 0.655, 0.525))
    for i, v in enumerate(vals):
        # 条形长度按占比归一（最大 100%），已妥投会几乎占满
        gradient_hbar(ax, i, v / 100, height=0.55)
        ax.text(v / 100 + 0.012, i, f"{v:.2f}%", ha="left", va="center",
                fontsize=13, color=WHITE if v > 1 else CAT, fontproperties=FP)

    ax.set_yticks(range(n))
    ax.set_yticklabels(labels, fontsize=13.5, color=CAT, fontproperties=FP)
    ax.set_xlim(0, 1.22)
    ax.set_xticks([])
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)

    d = st[st.order_status == "delivered"].iloc[0]
    chrome(
        fig,
        "97% 的订单走完了全程，真正的漏损只有 2.98%",
        f"已妥投 {d.orders:,} 单、占 {d.share_pct:.2f}%；"
        f"取消与缺货合计 {(st[st.order_status.isin(['canceled','unavailable'])].share_pct.sum()):.2f}%，"
        f"是平台可控的最大流失口",
        note_src("样本为观察窗内 99,092 个订单"),
    )
    save(fig, "fig08_订单状态构成_数值百分比.png")


if __name__ == "__main__":
    main()
