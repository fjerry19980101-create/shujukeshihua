# -*- coding: utf-8 -*-
"""
03_analysis_cohort.py —— 同期群（Cohort）留存分析
================================================
口径说明（论文 4.3 节）:
  同期群 = 按"首次购买月份"分组的客户集合；对每个群跟踪其后每月是否再次下单。
  留存率(m) = 第 m 个相对月仍有下单的客户数 / 该群客户总数。
  同时给出"GMV 留存"（第 m 月 GMV / 首月 GMV），因为客单价波动会让人数留存失真。

样本截断处理：只保留首次购买在 2017-01 至 2018-02 的群（保证至少有 6 个完整观察月），
避免"越新的群看起来留存越低"的右截断偏差。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from _common import TBL, load_orders, save_table
import os

MIN_COHORT = "2017-01"
MAX_COHORT = "2018-02"
MAX_MONTH_INDEX = 12


def main() -> None:
    fo = load_orders(with_window=True)

    # 客户首购月份 = 同期群标签
    first = fo.groupby("customer_unique_id").agg(
        cohort=("purchase_month", "min"),
        last=("purchase_month", "max"),
        orders=("order_id", "nunique"),
    ).reset_index()
    first = first[(first.cohort >= MIN_COHORT) & (first.cohort <= MAX_COHORT)]

    df = fo.merge(first[["customer_unique_id", "cohort"]], on="customer_unique_id", how="inner")
    df["cohort_idx"] = ((df.purchase_month.str[:4].astype(int) - df.cohort.str[:4].astype(int)) * 12
                        + (df.purchase_month.str[5:7].astype(int) - df.cohort.str[5:7].astype(int)))

    size = first.groupby("cohort").customer_unique_id.nunique().rename("cohort_size").reset_index()

    # ---------------- 人数留存 ----------------
    act = (df.groupby(["cohort", "cohort_idx"]).customer_unique_id.nunique()
             .rename("active").reset_index())
    act = act.merge(size, on="cohort")
    act["retention_pct"] = (act.active / act.cohort_size * 100).round(4)
    save_table(act[act.cohort_idx <= MAX_MONTH_INDEX], "cohort_retention_long.csv")

    mat = act.pivot(index="cohort", columns="cohort_idx", values="retention_pct")
    mat = mat.reindex(columns=range(0, MAX_MONTH_INDEX + 1))
    mat.index.name = "cohort"
    mat.to_csv(os.path.join(TBL, "cohort_retention_matrix.csv"), encoding="utf-8-sig")
    print(f"[table] cohort_retention_matrix.csv        {mat.shape[0]} 群 x {mat.shape[1]} 月")

    # ---------------- GMV 留存 ----------------
    gmv = df.groupby(["cohort", "cohort_idx"]).gmv.sum().rename("gmv").reset_index()
    base = gmv[gmv.cohort_idx == 0].set_index("cohort").gmv
    gmv["gmv_retention_pct"] = (gmv.apply(lambda r: r.gmv / base.get(r.cohort, np.nan), axis=1) * 100).round(3)
    gmat = gmv.pivot(index="cohort", columns="cohort_idx", values="gmv_retention_pct")
    gmat = gmat.reindex(columns=range(0, MAX_MONTH_INDEX + 1))
    gmat.to_csv(os.path.join(TBL, "cohort_gmv_matrix.csv"), encoding="utf-8-sig")

    # ---------------- 群摘要 ----------------
    summary = size.copy()
    for m in (1, 3, 6):
        col = m
        s = act[act.cohort_idx == col].set_index("cohort").retention_pct
        summary[f"m{m}_pct"] = summary.cohort.map(s).round(3)
    summary["repeat_rate_pct"] = summary.cohort.map(
        first.groupby("cohort").apply(lambda d: (d.orders >= 2).mean() * 100, include_groups=False)
    ).round(3)
    save_table(summary, "cohort_summary.csv")

    # ---------------- 复购间隔 ----------------
    dx = fo[fo.is_delivered == 1].sort_values(["customer_unique_id", "purchase_date"])
    gap = (dx.groupby("customer_unique_id").purchase_date.diff().dt.days.dropna())
    gap = gap[(gap > 0) & (gap <= 365)]
    save_table(pd.DataFrame({"repurchase_gap_days": gap}), "repurchase_gap.csv")

    print(f"\n[cohort] 群数 {len(size)}，客户 {size.cohort_size.sum():,}")
    print(f"         平均 M+1 留存 {act[act.cohort_idx==1].retention_pct.mean():.2f}% | "
          f"M+3 {act[act.cohort_idx==3].retention_pct.mean():.2f}% | "
          f"M+6 {act[act.cohort_idx==6].retention_pct.mean():.2f}%")
    print(f"         复购间隔中位数 {gap.median():.0f} 天（n={len(gap):,}）")


if __name__ == "__main__":
    main()
