# -*- coding: utf-8 -*-
"""
03_analysis_overview.py —— 经营总览 + 环比/同比 + 名义-实际-美元三口径拆解
=======================================================================
产出:
  outputs/tables/kpi_overview.json   核心 KPI（论文摘要与商业建议引用）
  outputs/tables/monthly_kpi.csv     月度经营表（环比 MoM / 同比 YoY / 三口径）
  outputs/tables/order_status_share.csv 订单状态结构
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

from _common import (ANALYSIS_END, BASE, delivered_only, load_orders, save_json,
                     save_table)


def nps(score: pd.Series) -> float:
    """NPS = 推荐者(5分) 占比 − 贬损者(1-2分) 占比。"""
    s = score.dropna()
    return float(((s == 5).mean() - (s <= 2).mean()) * 100)


def main() -> None:
    fo_all = load_orders(with_window=False)
    fo = load_orders(with_window=True)          # 趋势观察窗
    dv = delivered_only(fo)

    # ---------------- 核心 KPI ----------------
    buyer = fo.groupby("customer_unique_id").agg(
        orders=("order_id", "nunique"), gmv=("gmv", "sum"))
    repeat_rate = float((buyer.orders >= 2).mean() * 100)

    kpi = {
        "window": [str(fo.purchase_date.min().date()), str(fo.purchase_date.max().date())],
        "orders": int(len(fo)),
        "customers": int(buyer.shape[0]),
        "gmv_brl": round(float(fo.gmv.sum()), 2),
        "gmv_real_brl": round(float(fo.gmv_real.sum()), 2),
        "gmv_usd": round(float(fo.gmv_usd.sum()), 2),
        "aov_brl": round(float(fo.gmv.mean()), 2),
        "aov_median_brl": round(float(fo.gmv.median()), 2),
        "repeat_rate_pct": round(repeat_rate, 2),
        "orders_per_customer": round(float(buyer.orders.mean()), 3),
        "delivered_rate_pct": round(float(fo.is_delivered.mean() * 100), 2),
        "avg_delivery_days": round(float(dv.delivery_days.mean()), 2),
        "median_delivery_days": round(float(dv.delivery_days.median()), 2),
        "late_rate_pct": round(float(dv.is_late.mean() * 100), 2),
        "avg_delay_days_when_late": round(float(dv.loc[dv.is_late == 1, "delay_days"].mean()), 2),
        "review_mean": round(float(fo.review_score.mean()), 3),
        "bad_review_rate_pct": round(float((fo.review_score <= 2).mean() * 100), 2),
        "nps": round(nps(fo.review_score), 2),
        "avg_freight_ratio_pct": round(float((fo.freight_total / fo.gmv).mean() * 100), 2),
        "states": int(fo.state.nunique()),
        "categories": int(fo.main_category.nunique()),
    }

    # 延迟对满意度的杀伤（论文核心论据，逐条给数）
    grp = dv.groupby("is_late").agg(review=("review_score", "mean"),
                                    n=("order_id", "size"),
                                    bad=("review_score", lambda s: (s <= 2).mean() * 100))
    kpi["review_ontime"] = round(float(grp.loc[0, "review"]), 3)
    kpi["review_late"] = round(float(grp.loc[1, "review"]), 3)
    kpi["bad_rate_ontime_pct"] = round(float(grp.loc[0, "bad"]), 2)
    kpi["bad_rate_late_pct"] = round(float(grp.loc[1, "bad"]), 2)
    kpi["late_orders"] = int(grp.loc[1, "n"])
    kpi["ontime_orders"] = int(grp.loc[0, "n"])

    # 复购客 vs 一次性客的价值差
    buyer2 = buyer.copy()
    buyer2["seg"] = np.where(buyer2.orders >= 2, "复购客", "一次性客")
    v = buyer2.groupby("seg").agg(n=("gmv", "size"), gmv_mean=("gmv", "mean"),
                                  gmv_sum=("gmv", "sum"))
    kpi["repeat_customer_share_pct"] = round(float(v.loc["复购客", "n"] / v.n.sum() * 100), 2)
    kpi["repeat_gmv_share_pct"] = round(float(v.loc["复购客", "gmv_sum"] / v.gmv_sum.sum() * 100), 2)
    kpi["repeat_aov_multiple"] = round(float(v.loc["复购客", "gmv_mean"] / v.loc["一次性客", "gmv_mean"]), 2)

    save_json(kpi, "kpi_overview.json")

    # ---------------- 月度经营表 ----------------
    mo = fo.groupby("purchase_month").agg(
        orders=("order_id", "size"),
        customers=("customer_unique_id", "nunique"),
        gmv=("gmv", "sum"),
        gmv_real=("gmv_real", "sum"),
        gmv_usd=("gmv_usd", "sum"),
        aov=("gmv", "mean"),
        delivered_rate=("is_delivered", "mean"),
        review_mean=("review_score", "mean"),
    ).reset_index()
    dv_m = dv.groupby("purchase_month").agg(
        late_rate=("is_late", "mean"), delivery_days=("delivery_days", "mean")).reset_index()
    mo = mo.merge(dv_m, how="left", on="purchase_month")
    for c in ["delivered_rate", "late_rate"]:
        mo[c] = (mo[c] * 100).round(2)
    mo["review_mean"] = mo["review_mean"].round(3)
    mo["aov"] = mo["aov"].round(2)

    # 环比：与上月比（月度序列，1 月环比需 12 月基数，跨年连续计算）
    mo = mo.sort_values("purchase_month").reset_index(drop=True)
    for col, tag in [("gmv", "gmv"), ("orders", "orders"), ("aov", "aov")]:
        mo[f"mom_{tag}_pct"] = (mo[col].pct_change() * 100).round(2)
    # 同比：与去年同月比（2018 年才有 12 个月前基数）
    mo["yoy_gmv_pct"] = (mo.gmv.pct_change(12) * 100).round(2)
    mo["yoy_real_pct"] = (mo.gmv_real.pct_change(12) * 100).round(2)
    mo["yoy_usd_pct"] = (mo.gmv_usd.pct_change(12) * 100).round(2)
    save_table(mo, "monthly_kpi.csv")

    # 全窗口同比（2018年1-8月 vs 2017年1-8月）
    def sum_span(year: int) -> dict:
        s = fo[fo.purchase_year == year]
        s = s[s.purchase_date.dt.month <= 8]
        return {"gmv": s.gmv.sum(), "gmv_real": s.gmv_real.sum(),
                "gmv_usd": s.gmv_usd.sum(), "orders": len(s)}

    a, b = sum_span(2017), sum_span(2018)
    kpi["ytd_2018_vs_2017"] = {
        "gmv_yoy_pct": round((b["gmv"] / a["gmv"] - 1) * 100, 2),
        "gmv_real_yoy_pct": round((b["gmv_real"] / a["gmv_real"] - 1) * 100, 2),
        "gmv_usd_yoy_pct": round((b["gmv_usd"] / a["gmv_usd"] - 1) * 100, 2),
        "orders_yoy_pct": round((b["orders"] / a["orders"] - 1) * 100, 2),
    }
    save_json(kpi, "kpi_overview.json")

    # ---------------- 订单状态结构 ----------------
    st = fo_all.order_status.value_counts().rename_axis("order_status").reset_index(name="orders")
    st["share_pct"] = (st.orders / st.orders.sum() * 100).round(2)
    save_table(st, "order_status_share.csv")

    # ---------------- 品类 / 州 维度的基础画像（供作图复用） ----------------
    cat = (fo.groupby("main_category")
             .agg(orders=("order_id", "size"),
                  items=("item_count", "sum"),
                  gmv=("gmv", "sum"),
                  aov=("gmv", "mean"),
                  review=("review_score", "mean"),
                  late_rate=("is_late", "mean"))
             .reset_index())
    cat["gmv_share_pct"] = (cat.gmv / cat.gmv.sum() * 100).round(2)
    cat["late_rate"] = (cat.late_rate * 100).round(2)
    cat[["gmv", "aov"]] = cat[["gmv", "aov"]].round(2)
    cat["review"] = cat.review.round(3)
    cat = cat.sort_values("gmv", ascending=False)
    save_table(cat, "category_stats.csv")

    stt = (fo.groupby("state")
             .agg(orders=("order_id", "size"),
                  customers=("customer_unique_id", "nunique"),
                  gmv=("gmv", "sum"),
                  aov=("gmv", "mean"),
                  review=("review_score", "mean"))
             .reset_index())
    stt["gmv_share_pct"] = (stt.gmv / stt.gmv.sum() * 100).round(2)
    stt["aov"] = stt.aov.round(2)
    stt["review"] = stt.review.round(3)
    stt = stt.sort_values("gmv", ascending=False)
    save_table(stt, "state_stats.csv")

    # ---------------- 卖家画像（作 Top 卖家排名图用） ----------------
    it = pd.read_csv(os.path.join(BASE, "data", "clean", "fact_items.csv"))
    sl = (it.groupby("seller_id")
            .agg(orders=("order_id", "nunique"), items=("order_item_id", "size"),
                 gmv=("gmv", "sum"), sellers_state=("seller_state", "first"))
            .reset_index()
            .sort_values("gmv", ascending=False))
    sl["gmv_share_pct"] = (sl.gmv / sl.gmv.sum() * 100).round(3)
    sl["gmv"] = sl.gmv.round(2)
    save_table(sl.head(200), "seller_stats_top200.csv")

    # ---------------- 支付结构（季度 × 支付方式） ----------------
    pay = fo.dropna(subset=["payment_type"]).copy()
    pay["quarter_label"] = (pay.purchase_year.astype(str) + "Q"
                            + pay.purchase_date.dt.quarter.astype(str))
    pq = (pay.groupby(["quarter_label", "payment_type"])
             .agg(value=("payment_value", "sum"), orders=("order_id", "size"))
             .reset_index())
    pq["value"] = pq.value.round(2)
    save_table(pq, "payment_quarter.csv")

    # ---------------- 周度序列（平滑折线图、波动分析用） ----------------
    wk = (fo.groupby("purchase_week")
            .agg(gmv=("gmv", "sum"), orders=("order_id", "size"),
                 aov=("gmv", "mean"))
            .reset_index())
    wk["gmv"] = wk.gmv.round(2)
    wk["aov"] = wk.aov.round(2)
    save_table(wk, "weekly_kpi.csv")

    # ---------------- 控制台摘要 ----------------
    print("\n[overview] 观察窗", kpi["window"])
    print(f"  GMV {kpi['gmv_brl']:,.0f} BRL | 实际价 {kpi['gmv_real_brl']:,.0f} | "
          f"美元 {kpi['gmv_usd']:,.0f}")
    print(f"  订单 {kpi['orders']:,} | 客户 {kpi['customers']:,} | 客单价 {kpi['aov_brl']}")
    print(f"  复购率 {kpi['repeat_rate_pct']}% | 复购客贡献 GMV {kpi['repeat_gmv_share_pct']}%")
    print(f"  延迟率 {kpi['late_rate_pct']}% | 准时评分 {kpi['review_ontime']} vs "
          f"延迟评分 {kpi['review_late']}")
    print(f"  同比：名义 {kpi['ytd_2018_vs_2017']['gmv_yoy_pct']}% / "
          f"实际 {kpi['ytd_2018_vs_2017']['gmv_real_yoy_pct']}% / "
          f"美元 {kpi['ytd_2018_vs_2017']['gmv_usd_yoy_pct']}%")


if __name__ == "__main__":
    main()
