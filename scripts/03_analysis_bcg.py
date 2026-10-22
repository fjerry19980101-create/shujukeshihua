# -*- coding: utf-8 -*-
"""
03_analysis_bcg.py —— 波士顿矩阵（份额 × 增速）+ 帕累托/ABC 分类
==============================================================
一、波士顿矩阵（品类组合）
  横轴：相对市场份额 = 品类 GMV 份额 / 最大品类份额（经典 BCG 以"相对最大竞争对手=1"为分界）
  纵轴：实际增速 = 2018年1-8月实际价 GMV / 2017年1-8月实际价 GMV − 1
        （用实际价而非名义价，剔除通胀，避免把涨价当增长）
  分界：增速阈值取"市场整体实际增速"，而不是拍脑袋的 0%——高于大盘才算跑赢市场。
  气泡：品类 GMV 规模。

二、帕累托/ABC
  按品类 GMV 降序累计，累计占比 ≤80% 为 A 类（重点）、80%-95% 为 B 类、其余 C 类。
  同时算卖家集中度（CR10 / HHI），回答"平台是否被少数卖家绑架"。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from _common import load_items, load_orders, save_table


def gini_coef(values: np.ndarray) -> float:
    """基尼系数：卖家 GMV 分布的集中程度（0=完全均等，1=极致集中）。"""
    v = np.sort(np.asarray(values, dtype=float))
    n = v.size
    cum = np.cumsum(v) / v.sum()
    # 洛伦兹曲线下面积，用梯形法
    area = np.sum((cum[1:] + cum[:-1]) / 2) / n
    return float(1 - 2 * area + 1 / n)


def ytd(df: pd.DataFrame, year: int) -> pd.Series:
    s = df[(df.purchase_year == year) & (df.purchase_date.dt.month <= 8)]
    return s.groupby("main_category").gmv_real.sum()


def main() -> None:
    fo = load_orders(with_window=True)

    # ---------------- 波士顿矩阵 ----------------
    cur, pre = ytd(fo, 2018), ytd(fo, 2017)
    cat = pd.DataFrame({"gmv_2018": cur, "gmv_2017": pre}).fillna(0.0)
    cat = cat[(cat.gmv_2017 >= 1000) & (cat.gmv_2018 >= 1000)]   # 剔除极小类目，避免增速爆炸
    cat["gmv_total"] = cat.gmv_2018 + cat.gmv_2017
    cat["share_pct"] = cat.gmv_2018 / cat.gmv_2018.sum() * 100
    cat["rel_share"] = cat.gmv_2018 / cat.gmv_2018.max()
    cat["growth_pct"] = (cat.gmv_2018 / cat.gmv_2017 - 1) * 100

    market_growth = (cat.gmv_2018.sum() / cat.gmv_2017.sum() - 1) * 100
    # Olist 处于高速扩张期，若直接用绝对增速做纵轴，几乎所有品类都会落在"高增长"，
    # 矩阵失去区分度。故纵轴改为"相对增速" = 品类增速 − 平台整体增速（单位：百分点），
    # 以 0 为分界：>0 表示跑赢大盘。这是快速增长市场中 BCG 的通行修正做法。
    cat["growth_rel_pct"] = cat.growth_pct - market_growth
    share_cut, growth_cut = 0.5, 0.0      # 相对份额 0.5 等价于"份额为领导者一半"

    def quadrant(r: pd.Series) -> str:
        if r.rel_share >= share_cut and r.growth_rel_pct >= growth_cut:
            return "明星（Star）"
        if r.rel_share >= share_cut and r.growth_rel_pct < growth_cut:
            return "现金牛（Cash Cow）"
        if r.rel_share < share_cut and r.growth_rel_pct >= growth_cut:
            return "问题（Question）"
        return "瘦狗（Dog）"

    cat = cat.reset_index().rename(columns={"main_category": "category"})
    cat["quadrant"] = cat.apply(quadrant, axis=1)
    cat["share_pct"] = cat.share_pct.round(3)
    cat["rel_share"] = cat.rel_share.round(4)
    cat["growth_pct"] = cat.growth_pct.round(2)
    cat["growth_rel_pct"] = cat.growth_rel_pct.round(2)
    cat["gmv_total"] = cat.gmv_total.round(0)
    cat = cat.sort_values("gmv_total", ascending=False)
    save_table(cat, "bcg_matrix.csv")

    quad = cat.groupby("quadrant").agg(
        categories=("category", "size"),
        gmv=("gmv_total", "sum"),
        avg_growth=("growth_pct", "mean"),
        avg_growth_rel=("growth_rel_pct", "mean"),
    ).reset_index()
    quad["gmv_share_pct"] = (quad.gmv / quad.gmv.sum() * 100).round(2)
    quad["avg_growth"] = quad.avg_growth.round(2)
    quad["avg_growth_rel"] = quad.avg_growth_rel.round(2)
    save_table(quad, "bcg_quadrant_summary.csv")

    # ---------------- 帕累托 / ABC（品类） ----------------
    par = cat.sort_values("gmv_2018", ascending=False)[["category", "gmv_2018"]].copy()
    par["share_pct"] = (par.gmv_2018 / par.gmv_2018.sum() * 100).round(3)
    par["cum_share_pct"] = par.share_pct.cumsum().round(3)
    par["abc"] = np.where(par.cum_share_pct <= 80, "A",
                          np.where(par.cum_share_pct <= 95, "B", "C"))
    par["rank"] = range(1, len(par) + 1)
    save_table(par, "pareto_categories.csv")

    n_a = int((par.abc == "A").sum())
    abc_sum = par.groupby("abc").agg(n=("category", "size"), gmv=("gmv_2018", "sum")).reset_index()
    abc_sum["gmv_share_pct"] = (abc_sum.gmv / abc_sum.gmv.sum() * 100).round(2)
    save_table(abc_sum, "abc_summary.csv")

    # ---------------- 卖家集中度 ----------------
    # 卖家维度需回到明细层：一个订单可能多卖家，按明细行的 gmv 归属
    items = load_items()
    sl = items.groupby("seller_id").gmv.sum().sort_values(ascending=False)
    total = sl.sum()
    conc = {
        "sellers": int(sl.size),
        "cr1_pct": round(float(sl.iloc[0] / total * 100), 2),
        "cr10_pct": round(float(sl.iloc[:10].sum() / total * 100), 2),
        "cr50_pct": round(float(sl.iloc[:50].sum() / total * 100), 2),
        "hhi": round(float(((sl / total) ** 2).sum() * 10000), 1),
        "gini": round(float(gini_coef(sl.values)), 4),
    }
    save_table(pd.DataFrame([conc]), "seller_concentration.csv")

    print(f"\n[bcg] 品类 {len(cat)} 个 | 市场实际增速 {market_growth:.1f}% | 份额分界 {share_cut}")
    for _, r in quad.iterrows():
        print(f"      {r.quadrant:<14} {r.categories:>3} 类  GMV 占比 {r.gmv_share_pct:>5.2f}%  "
              f"平均增速 {r.avg_growth:>6.1f}%")
    print(f"[pareto] A 类 {n_a} 个品类贡献 80% GMV；卖家 CR10={conc['cr10_pct']}%  HHI={conc['hhi']}")


if __name__ == "__main__":
    main()
