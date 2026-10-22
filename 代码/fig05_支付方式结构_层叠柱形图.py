# -*- coding: utf-8 -*-
"""
fig05 层叠柱形图 —— 支付方式的结构迁移
======================================
复现模板：教材第 2 章《5 层叠柱形图》
复现要点：同一根柱内按系列堆叠、段内不描边、图例置于绘图区上方左侧、
         只在最上层标总数，避免"每段都标数字"的视觉噪声。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from _style import CAT, FP, SEQ, WHITE, chrome, load, money, new_canvas, note_src, save

ORDER = ["credit_card", "boleto", "voucher", "debit_card"]
LABEL = {"credit_card": "信用卡", "boleto": "Boleto 票据", "voucher": "代金券",
         "debit_card": "借记卡"}


def main():
    pq = load("payment_quarter.csv")
    pq = pq[pq.payment_type.isin(ORDER)]
    piv = pq.pivot_table(index="quarter_label", columns="payment_type",
                         values="value", aggfunc="sum").fillna(0)
    piv = piv.reindex(columns=[c for c in ORDER if c in piv.columns])
    # 剔除样本极少的 2016Q4（数据起点不完整）
    piv = piv[piv.index >= "2017Q1"]

    fig, ax = new_canvas()
    bottom = np.zeros(len(piv))
    for j, col in enumerate(piv.columns):
        v = piv[col].values / 1e4
        ax.bar(range(len(piv)), v, bottom=bottom, width=0.6,
               color=SEQ[j], edgecolor="none", zorder=2,
               label=f"{LABEL.get(col, col)}")
        bottom += v

    for i, tot in enumerate(bottom):
        ax.text(i, tot + bottom.max() * 0.02, f"{tot:,.0f}", ha="center", va="bottom",
                fontsize=13, color=WHITE, fontproperties=FP)

    ax.set_xlim(-0.7, len(piv) - 0.3)
    ax.set_ylim(0, bottom.max() * 1.2)
    ax.set_xticks(range(len(piv)))
    ax.set_xticklabels(piv.index, fontsize=13, color=CAT, fontproperties=FP)
    ax.set_yticks([])
    ax.grid(False)
    leg = ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=4, frameon=False,
                    fontsize=12.5, handlelength=1.0, handleheight=0.9,
                    columnspacing=1.6, labelcolor=CAT)
    for t in leg.get_texts():
        t.set_fontproperties(FP)

    cc_share = piv["credit_card"].sum() / piv.sum().sum() * 100
    last_cc = piv["credit_card"].iloc[-1] / piv.iloc[-1].sum() * 100
    chrome(
        fig,
        "支付结构：信用卡稳定在七成，票据支付持续萎缩",
        f"信用卡全期占 {cc_share:.1f}%，{piv.index[-1]} 为 {last_cc:.1f}%；"
        f"Boleto（巴西特有银行票据）份额由 "
        f"{piv['boleto'].iloc[0]/piv.iloc[0].sum()*100:.1f}% 降至 "
        f"{piv['boleto'].iloc[-1]/piv.iloc[-1].sum()*100:.1f}%",
        note_src("单位：万雷亚尔；按季度汇总支付流水"),
    )
    save(fig, "fig05_支付方式结构_层叠柱形图.png")


if __name__ == "__main__":
    main()
