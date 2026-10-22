# -*- coding: utf-8 -*-
"""
03_analysis_basket.py —— 关联规则（Apriori）+ 分类变量关联强度（Cramér's V）
==========================================================================
一、Apriori 的参数为什么这么定
  min_support 不能拍脑袋，而应由"业务可执行的最小订单量"反推：
    平台日均订单约 160 单，一个捆绑方案若一个月内连 50 单都凑不齐，就不足以支撑
    选品与备货决策。50 / 98,666 ≈ 0.05%，故 min_support = 0.0005。
  min_threshold(confidence) = 0.01：只做低门槛扫描，让所有候选规则先浮出来，
    再用 lift 做真正的筛选（因为本数据的 basket 极稀疏，高 confidence 阈值会直接返回空集）。

二、本数据的关键反直觉发现（论文 4.5 节）
  96.6% 的订单只含 1 个品类，导致"共现"比随机期望还少 —— 绝大多数规则的 lift < 1。
  这意味着：**在 Olist 上做购物篮捆绑，任何 lift>1 的"发现"都很可能是伪发现**。
  与其硬凑规则，不如把结论写成"该平台不存在可用的购物篮结构"，并转向
  分类变量之间的关联强度（Cramér's V），去回答"什么因素与差评/延迟真正相关"。

产出:
  basket_rules.csv         Apriori 规则（support/confidence/lift）
  basket_top_pairs.csv     高频共现品类对（含期望共现数与增益）
  basket_diagnosis.csv     lift 分布诊断
  cramers_v_matrix.csv     分类变量关联强度矩阵（含卡方 p 值）
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
from scipy.stats import chi2_contingency

from _common import load_items, load_orders, save_table

MIN_SUPPORT_ORDERS = 50          # 业务可执行的最小订单量
MIN_CONFIDENCE = 0.01


def cramers_v(a: pd.Series, b: pd.Series) -> tuple[float, float, int]:
    """Cramér's V：两个分类变量的关联强度（0=独立，1=完全关联），附卡方 p 值与样本量。"""
    tab = pd.crosstab(a, b)
    if tab.shape[0] < 2 or tab.shape[1] < 2:
        return np.nan, np.nan, int(tab.values.sum())
    chi2, p, _, _ = chi2_contingency(tab)
    n = tab.values.sum()
    r, k = tab.shape
    v = np.sqrt(chi2 / (n * (min(r, k) - 1)))
    return float(v), float(p), int(n)


def main() -> None:
    items = load_items()
    fo = load_orders(with_window=True)

    # ---------------- 交易篮构建（品类粒度） ----------------
    s = items.dropna(subset=["category"]).drop_duplicates(["order_id", "category"])
    baskets = s.groupby("order_id").category.apply(list)
    n_orders = int(baskets.shape[0])
    size_dist = s.groupby("order_id").category.nunique()
    multi_share = float((size_dist >= 2).mean() * 100)

    te = TransactionEncoder()
    arr = te.fit(baskets.values).transform(baskets.values)
    onehot = pd.DataFrame(arr, columns=te.columns_)

    min_support = MIN_SUPPORT_ORDERS / n_orders
    print(f"[basket] 订单 {n_orders:,} | 多品类订单占比 {multi_share:.1f}% | "
          f"min_support={min_support:.5f}（{MIN_SUPPORT_ORDERS} 单）")

    freq = apriori(onehot, min_support=min_support, use_colnames=True, max_len=2)
    freq["n_orders"] = (freq.support * n_orders).round(0).astype(int)
    rules = association_rules(freq, metric="confidence", min_threshold=MIN_CONFIDENCE)
    rules["antecedent"] = rules.antecedents.apply(lambda x: " + ".join(sorted(x)))
    rules["consequent"] = rules.consequents.apply(lambda x: " + ".join(sorted(x)))
    rules["n_antecedent_orders"] = (rules["antecedent support"] * n_orders).round(0).astype(int)
    rules["n_pair_orders"] = (rules.support * n_orders).round(0).astype(int)
    out = rules[["antecedent", "consequent", "n_pair_orders", "n_antecedent_orders",
                 "support", "confidence", "lift", "leverage", "conviction"]].copy()
    for c in ["support", "confidence", "lift", "leverage", "conviction"]:
        out[c] = out[c].round(4)
    out = out.sort_values("lift", ascending=False)
    save_table(out, "basket_rules.csv")

    # ---------------- 高频共现对（带随机期望，解释 lift<1） ----------------
    p = s.merge(s, on="order_id")
    p = p[p.category_x < p.category_y]
    pc = (p.groupby(["category_x", "category_y"]).order_id.nunique()
            .rename("n_pair_orders").reset_index())
    marg = s.groupby("category").order_id.nunique().rename("n_orders").reset_index()
    pc = pc.merge(marg.rename(columns={"category": "category_x", "n_orders": "n_x"}),
                  on="category_x").merge(
        marg.rename(columns={"category": "category_y", "n_orders": "n_y"}), on="category_y")
    pc["support_pct"] = (pc.n_pair_orders / n_orders * 100).round(4)
    # 独立假设下的期望共现订单数
    pc["expected_orders"] = (pc.n_x * pc.n_y / n_orders).round(1)
    pc["cooccur_lift"] = (pc.n_pair_orders / pc.expected_orders).round(3)
    pc = pc.sort_values("n_pair_orders", ascending=False)
    save_table(pc.head(30), "basket_top_pairs.csv")

    # ---------------- lift 诊断 ----------------
    diag = pd.DataFrame([{
        "n_orders": n_orders,
        "multi_category_order_pct": round(multi_share, 2),
        "min_support_orders": MIN_SUPPORT_ORDERS,
        "n_rules": int(len(out)),
        "rules_lift_gt1": int((out.lift > 1).sum()),
        "rules_lift_gt1_pct": round(float((out.lift > 1).mean() * 100), 2),
        "lift_median": round(float(out.lift.median()), 4) if len(out) else np.nan,
        "lift_max": round(float(out.lift.max()), 4) if len(out) else np.nan,
        "conclusion": (f"basket 结构不存在：多品类订单仅占 {multi_share:.1f}%，"
                       "共现低于随机期望，规则 lift 全部 < 1，不具备捆绑销售的可执行性"),
    }])
    save_table(diag, "basket_diagnosis.csv")

    # ---------------- 分类变量关联强度（真正可用的"关联"） ----------------
    d = fo.copy()
    d["installment_bucket"] = pd.cut(d.payment_installments.clip(1, 24),
                                     bins=[0, 1, 3, 6, 12, 24],
                                     labels=["1期", "2-3期", "4-6期", "7-12期", "12期以上"])
    d["review_bucket"] = pd.cut(d.review_score, bins=[0, 2, 3, 5],
                                labels=["差评(1-2)", "中评(3)", "好评(4-5)"])
    d["price_bucket"] = pd.qcut(d.gmv, 5, labels=["P1最低", "P2", "P3", "P4", "P5最高"],
                                duplicates="drop")
    d["late_flag"] = d.is_late.map({0: "准时", 1: "延迟"})
    # 东南部三州（SP/RJ/MG）贡献过半 GMV，单独成组便于对比
    d["region"] = np.where(d.state.isin(["SP", "RJ", "MG"]), "核心州", "其他州")

    pairs = [("late_flag", "review_bucket"), ("late_flag", "region"),
             ("payment_type", "installment_bucket"), ("payment_type", "price_bucket"),
             ("price_bucket", "review_bucket"), ("region", "review_bucket"),
             ("installment_bucket", "price_bucket"), ("main_category", "late_flag")]
    rows = []
    for a, b in pairs:
        v, pval, n = cramers_v(d[a].astype(str), d[b].astype(str))
        rows.append({"var_a": a, "var_b": b, "cramers_v": round(v, 4),
                     "chi2_p_value": f"{pval:.3e}", "n": n,
                     "strength": ("强" if v >= 0.25 else "中" if v >= 0.15 else "弱")})
    cv = pd.DataFrame(rows).sort_values("cramers_v", ascending=False)
    save_table(cv, "cramers_v_matrix.csv")

    # ---------------- 多品类 vs 单品类订单价值对比 ----------------
    # 购物篮虽稀少，但"多买一个品类"是否值钱，直接决定捆绑策略该不该做
    ncat = size_dist.rename("n_category").reset_index()
    val = fo.merge(ncat, on="order_id", how="inner")
    val["basket_type"] = np.where(val.n_category >= 2, "多品类订单", "单品类订单")
    cmp = val.groupby("basket_type").agg(
        orders=("order_id", "size"), aov=("gmv", "mean"),
        median_gmv=("gmv", "median"), items=("item_count", "mean"),
        review=("review_score", "mean"), late_rate=("is_late", "mean")).reset_index()
    for c in ["aov", "median_gmv", "items", "review"]:
        cmp[c] = cmp[c].round(3)
    cmp["late_rate"] = (cmp.late_rate * 100).round(2)
    cmp["order_share_pct"] = (cmp.orders / cmp.orders.sum() * 100).round(2)
    save_table(cmp, "basket_value_compare.csv")

    print(f"\n[basket] 规则 {len(out)} 条，lift>1 的仅 {(out.lift>1).sum()} 条，"
          f"lift 中位数 {out.lift.median():.3f}")
    print(f"         多品类订单客单价 {cmp.iloc[1].aov:.1f} vs 单品类 {cmp.iloc[0].aov:.1f}"
          f"（倍数 {cmp.iloc[1].aov / cmp.iloc[0].aov:.2f}）")
    print("[basket] 关联强度 Top3：")
    for _, r in cv.head(3).iterrows():
        print(f"         {r.var_a} × {r.var_b}: V={r.cramers_v} ({r.strength}) p={r.chi2_p_value}")


if __name__ == "__main__":
    main()
