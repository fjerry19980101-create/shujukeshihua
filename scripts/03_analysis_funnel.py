# -*- coding: utf-8 -*-
"""
03_analysis_funnel.py —— 履约漏斗 + 延迟归因 + 州际差异
=====================================================
漏斗定义（订单生命周期，逐级收窄）：
  L1 下单创建 → L2 支付通过 → L3 交运（卖家发货交接承运商） → L4 妥投 → L5 好评(4-5 分)

延迟归因（论文 4.7 节的方法学要点）：
  总时长 = 卖家备货段(handover_days) + 干线末端段(transit_days)。
  把延迟订单与准时订单的两段时长分别取中位数比较，即可判断"延迟是谁的责任"：
  若延迟单的备货段显著更长 → 卖家侧；若干线段更长 → 物流侧。
  这是替代"拍脑袋归因"的可验证做法。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from _common import delivered_only, load_orders, save_table


def main() -> None:
    fo_all = load_orders(with_window=False)
    fo = load_orders(with_window=True)
    dv = delivered_only(fo)
    dv["buffer_days"] = dv.estimated_days - dv.delivery_days

    # ---------------- 履约漏斗 ----------------
    l1 = len(fo)
    l2 = int(fo.order_approved_at.notna().sum())
    l3 = int(fo.order_delivered_carrier_date.notna().sum())
    l4 = int((fo.is_delivered == 1).sum())
    l5 = int(((fo.is_delivered == 1) & (fo.review_score >= 4)).sum())
    stages = pd.DataFrame({
        "stage": ["L1 下单创建", "L2 支付通过", "L3 卖家交运", "L4 成功妥投", "L5 好评(4-5分)"],
        "orders": [l1, l2, l3, l4, l5],
    })
    stages["overall_rate_pct"] = (stages.orders / l1 * 100).round(2)
    stages["stage_rate_pct"] = (stages.orders / stages.orders.shift(1) * 100).round(2)
    stages.loc[0, "stage_rate_pct"] = 100.0
    stages["drop_orders"] = stages.orders.shift(1) - stages.orders
    save_table(stages, "funnel_stages.csv")

    # ---------------- 延迟归因 ----------------
    rows = []
    for flag, name in [(0, "准时"), (1, "延迟")]:
        s = dv[dv.is_late == flag]
        rows.append({
            "group": name,
            "orders": int(len(s)),
            "handover_days_median": round(float(s.handover_days.median()), 2),
            "transit_days_median": round(float(s.transit_days.median()), 2),
            "total_days_median": round(float(s.delivery_days.median()), 2),
            "estimated_days_median": round(float(s.estimated_days.median()), 2),
            "review_mean": round(float(s.review_score.mean()), 3),
        })
    att = pd.DataFrame(rows)
    # 归因结论：两段时长相对准时单的增量占比
    d_hand = att.loc[1, "handover_days_median"] - att.loc[0, "handover_days_median"]
    d_tran = att.loc[1, "transit_days_median"] - att.loc[0, "transit_days_median"]
    att["increment_vs_ontime"] = [np.nan, round(d_hand + d_tran, 2)]
    save_table(att, "delay_attribution.csv")

    share_hand = d_hand / (d_hand + d_tran) * 100 if (d_hand + d_tran) else np.nan
    print(f"[funnel] 延迟单比准时单多耗 {d_hand + d_tran:.1f} 天："
          f"备货段 +{d_hand:.1f} 天（{share_hand:.0f}%），干线段 +{d_tran:.1f} 天（{100-share_hand:.0f}%）")

    # ---------------- 州际差异 ----------------
    st = (dv.groupby("state")
            .agg(orders=("order_id", "size"),
                 gmv=("gmv", "sum"),
                 delivery_days=("delivery_days", "median"),
                 late_rate=("is_late", "mean"),
                 review=("review_score", "mean"),
                 freight_ratio=("freight_ratio", "mean"))
            .reset_index())
    st = st[st.orders >= 100]                      # 样本过少的州不参与排名
    st["late_rate"] = (st.late_rate * 100).round(2)
    st["freight_ratio"] = (st.freight_ratio * 100).round(2)
    st["delivery_days"] = st.delivery_days.round(1)
    st["review"] = st.review.round(3)
    st["gmv_share_pct"] = (st.gmv / st.gmv.sum() * 100).round(2)
    st = st.sort_values("gmv", ascending=False)
    save_table(st, "state_delivery.csv")

    # 距离代理：客户坐标与卖家州首府坐标的直线距离（仅用于解释延迟，不做精确物流计算）
    # 这里用"客户所在州到圣保罗(SP)的球面距离"作为干线距离代理
    sp = (-23.55, -46.63)

    def hav(lat, lng) -> np.ndarray:
        r = 6371.0
        la1, lo1, la2, lo2 = map(np.radians, [lat, lng, sp[0], sp[1]])
        dla, dlo = la2 - la1, lo2 - lo1
        a = np.sin(dla / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin(dlo / 2) ** 2
        return 2 * r * np.arcsin(np.sqrt(a))

    # ---------------- 州级履约三段时长（甘特图用） ----------------
    sg = (dv.groupby("state")
            .agg(orders=("order_id", "size"),
                 handover=("handover_days", "median"),
                 transit=("transit_days", "median"),
                 total=("delivery_days", "median"))
            .reset_index())
    sg = sg[sg.orders >= 200].sort_values("total", ascending=False)
    for c in ["handover", "transit", "total"]:
        sg[c] = sg[c].round(2)
    save_table(sg, "state_stage_days.csv")

    # ---------------- 月度延迟趋势（是否正确：延迟率在恶化？） ----------------
    trend = (dv.groupby("purchase_month")
               .agg(orders=("order_id", "size"),
                    late_rate=("is_late", "mean"),
                    delivery_days=("delivery_days", "median"),
                    estimated_days=("estimated_days", "median"),
                    buffer_median=("buffer_days", "median"),
                    review=("review_score", "mean"))
               .reset_index())
    trend["late_rate"] = (trend.late_rate * 100).round(2)
    trend["delivery_days"] = trend.delivery_days.round(1)
    trend["estimated_days"] = trend.estimated_days.round(1)
    # 缓冲（逐单计算后取中位）：承诺时效 − 实际时效。这个值越小，承诺越激进，
    # 尾部订单越容易击穿承诺，是延迟率的先行指标。
    trend["promise_buffer_days"] = trend.buffer_median.round(1)
    trend = trend.drop(columns=["buffer_median"])
    trend["review"] = trend.review.round(3)
    save_table(trend, "late_trend_monthly.csv")

    # ---------------- 延迟天数分箱 vs 差评率 ----------------
    b = dv.dropna(subset=["delay_days"]).copy()
    b["delay_bin"] = pd.cut(b.delay_days,
                            bins=[-999, -15, -7, 0, 3, 7, 15, 999],
                            labels=["提前15天以上", "提前7-15天", "提前0-7天",
                                    "延迟1-3天", "延迟4-7天", "延迟8-15天", "延迟15天以上"])
    bin_tab = (b.groupby("delay_bin", observed=True)
                 .agg(orders=("order_id", "size"),
                      bad_rate=("review_score", lambda s: (s <= 2).mean() * 100),
                      review=("review_score", "mean"))
                 .reset_index())
    bin_tab["bad_rate"] = bin_tab.bad_rate.round(2)
    bin_tab["review"] = bin_tab.review.round(3)
    bin_tab["order_share_pct"] = (bin_tab.orders / bin_tab.orders.sum() * 100).round(2)
    save_table(bin_tab, "late_vs_review_bins.csv")

    # ---------------- 反事实：承诺缓冲 vs 延迟率/差评率 ----------------
    # 机制：客户只在"实际时效 > 承诺时效"时判为延迟，即 delay = delivery_days − buffer。
    # 先用全部订单拟合 P(差评 | delay天数) 的 logistic 曲线（剂量-反应关系），
    # 再把 2018-08 的实际时效分布代入不同 buffer，得到"若承诺放宽到 X 天"的期望差评率。
    # 这样得到的不是阶梯式拍脑袋映射，而是由 9.4 万条真实评价标定出的反事实。
    from sklearn.linear_model import LogisticRegression

    fit_df = dv.dropna(subset=["delay_days", "review_score"]).copy()
    fit_df["bad"] = (fit_df.review_score <= 2).astype(int)
    Xd = fit_df[["delay_days"]].values
    lr_model = LogisticRegression().fit(Xd, fit_df.bad.values)

    last_month = trend.iloc[-1].purchase_month
    dm = dv[dv.purchase_month == last_month].delivery_days.dropna().values
    rows = []
    for buf in range(3, 31):
        late_rate = float((dm > buf).mean() * 100)
        # 该 buffer 下每条订单的延迟天数 -> 期望差评概率 -> 求均值
        bad_rate = float(lr_model.predict_proba((dm - buf).reshape(-1, 1))[:, 1].mean() * 100)
        rows.append({"promised_days": buf, "late_rate_pct": round(late_rate, 2),
                     "expected_bad_rate_pct": round(bad_rate, 2)})
    save_table(pd.DataFrame(rows), "buffer_scenario.csv")

    b6 = rows[6 - 3]["late_rate_pct"]
    b15 = rows[15 - 3]["late_rate_pct"]
    print(f"[funnel] {last_month} 实际时效中位 {np.median(dm):.1f} 天；"
          f"缓冲 6 天延迟率 {b6:.2f}%，放宽到 15 天降至 {b15:.2f}%")

    # ---------------- 摘要 ----------------
    print("\n[funnel] 履约漏斗")
    for _, r in stages.iterrows():
        print(f"        {r.stage:<12} {r.orders:>7,}  总体 {r.overall_rate_pct:>6.2f}%  "
              f"环节 {r.stage_rate_pct:>6.2f}%")
    print(f"\n[funnel] 延迟最重的州：")
    for _, r in st.sort_values("late_rate", ascending=False).head(4).iterrows():
        print(f"        {r.state}  延迟率 {r.late_rate:>5.2f}%  中位时效 {r.delivery_days:>4.1f} 天  "
              f"评分 {r.review}")
    print(f"[funnel] 延迟率趋势：{trend.iloc[0].purchase_month} {trend.iloc[0].late_rate}% → "
          f"{trend.iloc[-1].purchase_month} {trend.iloc[-1].late_rate}%")


if __name__ == "__main__":
    main()
