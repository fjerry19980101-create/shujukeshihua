# -*- coding: utf-8 -*-
"""
02_clean.py —— 数据清洗与治理
=============================
输入 : data/raw/*.csv（01_load.py 原样落盘的 9 张表）
输出 :
  data/clean/*.csv          清洗后的星型模型（事实表 + 维度表）
  data/clean/olist.db       SQLite 单文件库（评分项 1④：CSV/JSON/SQLite 可复用）
  data/clean/_clean_manifest.json
  outputs/tables/data_quality_report.csv   治理台账（每一步处理了多少行、为什么）

治理顺序（每一步都记账，便于论文第 3 章逐条引用）：
  S1 结构体检 → S2 主键/重复 → S3 时间字段 → S4 缺失 → S5 异常
  → S6 多表对齐 → S7 派生指标 → S8 落库
"""
from __future__ import annotations

import json
import os
import sqlite3

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
CLEAN = os.path.join(BASE, "data", "clean")
TBL = os.path.join(BASE, "outputs", "tables")
os.makedirs(CLEAN, exist_ok=True)
os.makedirs(TBL, exist_ok=True)

RANDOM_SEED = 42                     # 全项目统一随机种子（K-Means / bootstrap / 抽样校验）
np.random.seed(RANDOM_SEED)

# 巴西本土经纬度合理范围，用于剔除地理表越界点
BR_LAT = (-34.0, 5.5)
BR_LNG = (-74.0, -34.0)
# 履约时长上限：超过 180 天视为录入/极端异常，保留记录但不参与均值类统计
DELIVERY_CAP_DAYS = 180
# 趋势分析的观察窗：Olist 2016-09 上线，2016 年样本稀疏；2018-09 起数据截断
ANALYSIS_START = pd.Timestamp("2017-01-01")
ANALYSIS_END = pd.Timestamp("2018-08-31")

AUDIT: list[dict] = []


def audit(step: str, table: str, before: int, after: int, note: str) -> None:
    """记录一条治理台账。"""
    AUDIT.append({
        "step": step,
        "table": table,
        "rows_before": before,
        "rows_after": after,
        "rows_removed": before - after,
        "removed_pct": round((before - after) / before * 100, 3) if before else 0.0,
        "note": note,
    })


def read(name: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(RAW, name))


def to_dt(s: pd.Series) -> pd.Series:
    """统一时间解析：原表是 'YYYY-MM-DD HH:MM:SS' 字符串，非法值转 NaT。"""
    return pd.to_datetime(s, errors="coerce", format="%Y-%m-%d %H:%M:%S")


# =====================================================================
# S1 结构体检
# =====================================================================
def s1_profile() -> dict:
    prof = {}
    for f in sorted(os.listdir(RAW)):
        if not f.endswith(".csv"):
            continue
        d = pd.read_csv(os.path.join(RAW, f))
        prof[f] = {
            "rows": int(len(d)),
            "cols": int(d.shape[1]),
            "dup_full_row": int(d.duplicated().sum()),
            "missing_cells": int(d.isna().sum().sum()),
            "columns": list(d.columns),
        }
    return prof


# =====================================================================
# S2 维度表：客户 / 商品 / 卖家 / 地理
# =====================================================================
def build_customers() -> pd.DataFrame:
    c = read("olist_customers_dataset.csv")
    n0 = len(c)
    c = c.drop_duplicates(subset=["customer_id"])
    audit("S2 去重", "dim_customers", n0, len(c), "customer_id 为主键，重复即脏数据")

    geo = read("olist_geolocation_dataset.csv")
    n_geo0 = len(geo)
    geo = geo.drop_duplicates()
    # 越界经纬度剔除（巴西国土范围）
    geo = geo[geo.geolocation_lat.between(*BR_LAT) & geo.geolocation_lng.between(*BR_LNG)]
    # 同一邮编前缀多点采集中位数，消除 1M 行冗余（zip 前缀 -> 一个代表坐标）
    g = (geo.groupby("geolocation_zip_code_prefix", as_index=False)
            .agg(lat=("geolocation_lat", "median"),
                 lng=("geolocation_lng", "median"),
                 geo_points=("geolocation_lat", "size")))
    audit("S5 异常+聚合", "olist_geolocation", n_geo0, len(g),
          f"剔除越界点后按邮编中位数聚合（点集 {len(geo):,} 条 -> {len(g):,} 个邮编坐标）")

    c = c.merge(g, how="left",
                left_on="customer_zip_code_prefix", right_on="geolocation_zip_code_prefix")
    miss_geo = int(c["lat"].isna().sum())
    audit("S4 缺失", "dim_customers.geo", len(c), len(c) - miss_geo,
          f"{miss_geo} 个邮编无地理匹配；保留客户行、坐标留空（仅地图类图剔除）")
    c["city"] = c["customer_city"].str.strip().str.lower()
    c["state"] = c["customer_state"].str.strip().str.upper()
    return c.rename(columns={
        "customer_zip_code_prefix": "zip_prefix",
        "customer_city": "city_raw",
        "customer_state": "state_raw",
    })[["customer_id", "customer_unique_id", "zip_prefix", "city", "state", "lat", "lng"]]


def build_products() -> pd.DataFrame:
    p = read("olist_products_dataset.csv")
    trans = read("product_category_name_translation.csv")
    n0 = len(p)
    p = p.drop_duplicates(subset=["product_id"])
    audit("S2 去重", "dim_products", n0, len(p), "product_id 为主键")

    # 类目缺失：610 行（占 1.85%）—— 不猜类目，统一标 'unknown'，避免污染品类排名
    miss_cat = int(p["product_category_name"].isna().sum())
    p["product_category_name"] = p["product_category_name"].fillna("unknown")
    audit("S4 缺失", "dim_products.category", len(p), len(p),
          f"{miss_cat} 条缺失类目标记为 unknown（占 {miss_cat/len(p)*100:.2f}%），不参与品类 Top 排名")

    # 物理属性缺失：用类目中位数插补（同类商品规格相近，比全局中位数更稳）
    for col in ["product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"]:
        m = int(p[col].isna().sum())
        if m:
            p[col] = p.groupby("product_category_name")[col].transform(
                lambda s: s.fillna(s.median()))
            p[col] = p[col].fillna(p[col].median())
            audit("S4 缺失", f"dim_products.{col}", len(p), len(p),
                  f"{m} 条缺失，按类目中位数插补（次级回退全局中位数）")

    p = p.merge(trans, how="left", on="product_category_name")
    p["category"] = (p["product_category_name_english"]
                     .fillna(p["product_category_name"]).str.replace("_", " ", regex=False))
    p["volume_cm3"] = p["product_length_cm"] * p["product_height_cm"] * p["product_width_cm"]
    p.loc[p["volume_cm3"] <= 0, "volume_cm3"] = np.nan
    return p.rename(columns={
        "product_name_lenght": "name_len",
        "product_description_lenght": "desc_len",
        "product_photos_qty": "photos_qty",
        "product_weight_g": "weight_g",
    })[["product_id", "category", "weight_g", "volume_cm3", "photos_qty", "name_len", "desc_len"]]


def build_sellers() -> pd.DataFrame:
    s = read("olist_sellers_dataset.csv")
    n0 = len(s)
    s = s.drop_duplicates(subset=["seller_id"])
    audit("S2 去重", "dim_sellers", n0, len(s), "seller_id 为主键")
    s["seller_state"] = s["seller_state"].str.upper()
    return s.rename(columns={"seller_zip_code_prefix": "seller_zip",
                             "seller_city": "seller_city",
                             "seller_state": "seller_state"})[
        ["seller_id", "seller_zip", "seller_city", "seller_state"]]


# =====================================================================
# S3/S4/S5 订单主表
# =====================================================================
def build_orders() -> pd.DataFrame:
    o = read("olist_orders_dataset.csv")
    n0 = len(o)
    o = o.drop_duplicates(subset=["order_id"])
    audit("S2 去重", "fact_orders", n0, len(o), "order_id 为主键")

    for c in ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
              "order_delivered_customer_date", "order_estimated_delivery_date"]:
        o[c] = to_dt(o[c])
    audit("S3 类型统一", "fact_orders.time", len(o), len(o),
          "5 个时间字段由字符串统一转为 datetime64；无法解析置 NaT")

    # 时间逻辑校验：审批早于下单、妥投早于发货 属录入错误
    bad_approve = (o.order_approved_at < o.order_purchase_timestamp).sum()
    o.loc[o.order_approved_at < o.order_purchase_timestamp, "order_approved_at"] = pd.NaT
    bad_deliver = (o.order_delivered_customer_date < o.order_delivered_carrier_date).sum()
    o.loc[o.order_delivered_customer_date < o.order_delivered_carrier_date,
          "order_delivered_customer_date"] = pd.NaT
    audit("S5 逻辑校验", "fact_orders", len(o), len(o),
          f"审批早于下单 {bad_approve} 条、妥投早于交运 {bad_deliver} 条，时间字段置空待补")

    o["is_delivered"] = (o.order_status == "delivered").astype(int)

    # 履约时长（天，保留 2 位）
    def days(a, b):
        return (b - a).dt.total_seconds() / 86400

    o["delivery_days"] = days(o.order_purchase_timestamp, o.order_delivered_customer_date)
    o["estimated_days"] = days(o.order_purchase_timestamp, o.order_estimated_delivery_date)
    o["handover_days"] = days(o.order_approved_at, o.order_delivered_carrier_date)   # 卖家备货
    o["transit_days"] = days(o.order_delivered_carrier_date, o.order_delivered_customer_date)  # 干线+末端
    o["delay_days"] = o["delivery_days"] - o["estimated_days"]      # >0 即超时
    o["is_late"] = (o["delay_days"] > 0).astype("Int64")

    # 负时长（妥投早于下单）属明显异常，置空
    # 注意：delay_days = 实际时长 − 承诺时长，为负表示"提前送达"，属正常业务情形，
    # 绝不能与"时长为负"混为一谈——这里只清理三个真正的时长字段。
    neg = int((o["delivery_days"] < 0).sum())
    for c in ["delivery_days", "handover_days", "transit_days"]:
        o.loc[o[c] < 0, c] = np.nan
    o.loc[o["delivery_days"].isna(), "delay_days"] = np.nan
    audit("S5 异常", "fact_orders.duration", len(o), len(o),
          f"{neg} 条负时长置空；另设 {DELIVERY_CAP_DAYS} 天上限标记 delivery_is_capped")

    # 长尾截尾标记：不删除（避免幸存者偏差），仅标记，均值类统计按标记过滤
    o["delivery_is_capped"] = (o["delivery_days"] > DELIVERY_CAP_DAYS).astype(int)
    cap_n = int(o["delivery_is_capped"].sum())

    # 日期维度派生
    o["purchase_date"] = o.order_purchase_timestamp.dt.normalize()
    o["purchase_month"] = o.order_purchase_timestamp.dt.to_period("M").astype(str)
    o["purchase_week"] = (o.order_purchase_timestamp
                          .dt.to_period("W-SUN").dt.start_time)
    o["purchase_year"] = o.order_purchase_timestamp.dt.year
    o["purchase_hour"] = o.order_purchase_timestamp.dt.hour
    o["purchase_dow"] = o.order_purchase_timestamp.dt.dayofweek

    audit("S7 派生", "fact_orders", len(o), len(o),
          f"派生 delivery_days/estimated_days/delay_days/handover_days/transit_days/is_late；"
          f"超 {DELIVERY_CAP_DAYS} 天 {cap_n} 条仅标记不删除")
    return o


def build_items() -> pd.DataFrame:
    it = read("olist_order_items_dataset.csv")
    n0 = len(it)
    it = it.drop_duplicates(subset=["order_id", "order_item_id"])
    audit("S2 去重", "fact_items", n0, len(it), "(order_id, order_item_id) 复合主键")

    it["shipping_limit_date"] = to_dt(it["shipping_limit_date"])
    n_price = int((it.price <= 0).sum())
    it = it[it.price > 0]
    audit("S5 异常", "fact_items.price", n0, len(it), f"删除 price<=0 的 {n_price} 条（价格不可能非正）")

    it["gmv"] = it["price"] + it["freight_value"]
    return it


def build_payments() -> pd.DataFrame:
    p = read("olist_order_payments_dataset.csv")
    n0 = len(p)
    p = p.drop_duplicates()
    audit("S2 去重", "fact_payments", n0, len(p), "完全重复行去重")

    # 同一订单可能多笔支付（分期/混合支付），聚合到订单粒度
    p["payment_value"] = pd.to_numeric(p["payment_value"], errors="coerce")
    p = p[p.payment_value.notna()]
    agg = (p.sort_values("payment_value", ascending=False)
             .groupby("order_id", as_index=False)
             .agg(payment_value=("payment_value", "sum"),
                  payment_installments=("payment_installments", "max"),
                  payment_type=("payment_type", "first")))
    audit("S6 聚合", "fact_payments", len(p), len(agg),
          "多笔支付按订单汇总：金额求和、分期取最大、主支付方式取金额最大者")
    return agg


def build_reviews() -> pd.DataFrame:
    r = read("olist_order_reviews_dataset.csv")
    n0 = len(r)
    # 一个订单可能有多条评价，保留最新一条（便于与订单一对一对齐）
    r["review_creation_date"] = to_dt(r["review_creation_date"])
    r = (r.sort_values("review_creation_date")
           .drop_duplicates(subset=["order_id"], keep="last"))
    audit("S2 去重", "fact_reviews", n0, len(r),
          f"同一订单多条评价保留最新一条（原始 {n0:,} 条 -> {len(r):,} 条）")
    r["has_comment"] = r["review_comment_message"].notna().astype(int)
    return r[["order_id", "review_id", "review_score", "review_creation_date", "has_comment"]]


# =====================================================================
# S6 多表对齐 + S7 指标汇总
# =====================================================================
def build_fact_orders(cust: pd.DataFrame, prod: pd.DataFrame,
                      sell: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """事实表构建：维度表由 main() 统一构建一次后传入，避免重复记账。"""
    orders = build_orders()
    items = build_items()
    pay = build_payments()
    rev = build_reviews()

    # 商品明细带类目与卖家
    items_full = (items.merge(prod[["product_id", "category", "weight_g", "volume_cm3"]],
                              how="left", on="product_id")
                       .merge(sell[["seller_id", "seller_state"]], how="left", on="seller_id"))
    items_full["gmv"] = items_full["price"] + items_full["freight_value"]

    # 订单粒度汇总：商品数、卖家数、金额、主类目（按金额最大）
    main_cat = (items_full.groupby(["order_id", "category"], as_index=False)["gmv"].sum()
                          .sort_values("gmv", ascending=False)
                          .drop_duplicates("order_id")[["order_id", "category"]]
                          .rename(columns={"category": "main_category"}))
    item_agg = items_full.groupby("order_id", as_index=False).agg(
        item_count=("order_item_id", "size"),
        seller_count=("seller_id", "nunique"),
        price_total=("price", "sum"),
        freight_total=("freight_value", "sum"),
        gmv=("gmv", "sum"),
        weight_g=("weight_g", "sum"),
    ).merge(main_cat, how="left", on="order_id")

    fo = (orders.merge(cust, how="left", on="customer_id")
                .merge(item_agg, how="left", on="order_id")
                .merge(pay, how="left", on="order_id")
                .merge(rev[["order_id", "review_score", "has_comment"]], how="left", on="order_id"))

    # 对齐诊断：有订单无商品明细 = 未成单/取消，属业务事实而非脏数据
    no_item = int(fo["gmv"].isna().sum())
    audit("S6 对齐", "fact_orders x fact_items", len(fo), len(fo),
          f"{no_item} 个订单无商品明细（多为 canceled/unavailable），保留订单行、金额留空，"
          f"金额类统计自动剔除")

    # 金额缺失回填：极少数订单无明细但有支付流水，用支付金额兜底
    fo["gmv"] = fo["gmv"].fillna(fo["payment_value"])
    fo["item_count"] = fo["item_count"].fillna(0).astype(int)
    fo["seller_count"] = fo["seller_count"].fillna(0).astype(int)
    fo["main_category"] = fo["main_category"].fillna("unknown")
    fo["freight_ratio"] = fo["freight_total"] / fo["gmv"].replace(0, np.nan)

    return fo, items_full


def build_dim_date(fo: pd.DataFrame) -> pd.DataFrame:
    days = pd.date_range(fo.purchase_date.min(), fo.purchase_date.max(), freq="D")
    d = pd.DataFrame({"date": days})
    d["year"] = d.date.dt.year
    d["month"] = d.date.dt.month
    d["month_str"] = d.date.dt.to_period("M").astype(str)
    d["quarter"] = d.date.dt.quarter
    d["week"] = d.date.dt.isocalendar().week.astype(int)
    d["weekday"] = d.date.dt.dayofweek
    d["is_weekend"] = (d.weekday >= 5).astype(int)
    d["in_analysis_window"] = d.date.between(ANALYSIS_START, ANALYSIS_END).astype(int)
    return d


def attach_macro(fo: pd.DataFrame) -> pd.DataFrame:
    """并入辅助数据源（BCB 宏观月度序列），派生实际价与美元口径 GMV。

    这一步是论文"批判性思维"支点的数据基础：名义 GMV 的增速里含通胀与汇率成分，
    必须拆出来才能判断真实经营质量。辅助源缺失时自动降级（不阻断主流程）。
    """
    p = os.path.join(BASE, "data", "raw_aux", "bcb_macro_monthly.csv")
    if not os.path.exists(p):
        print("[clean] 未找到宏观辅助表，跳过（如需请先运行 scripts/01b_aux.py）")
        return fo
    m = pd.read_csv(p).rename(columns={"month": "purchase_month"})
    keep = ["purchase_month", "ipca_pct", "selic_pct", "usdbrl", "deflator"]
    fo = fo.merge(m[keep], how="left", on="purchase_month")
    fo["gmv_real"] = fo["gmv"] / fo["deflator"]      # 2018-08 不变价
    fo["gmv_usd"] = fo["gmv"] / fo["usdbrl"]         # 美元口径
    audit("S8 辅助并入", "fact_orders.macro", len(fo), len(fo),
          "并入 BCB 月度 IPCA/Selic/USD-BRL，派生 gmv_real（2018-08 不变价）与 gmv_usd")
    return fo


# =====================================================================
# S8 落库
# =====================================================================
def save_all(tables: dict[str, pd.DataFrame]) -> None:
    for name, df in tables.items():
        df.to_csv(os.path.join(CLEAN, f"{name}.csv"), index=False, encoding="utf-8-sig")
    db = os.path.join(CLEAN, "olist.db")
    if os.path.exists(db):
        os.remove(db)
    con = sqlite3.connect(db)
    for name, df in tables.items():
        df.to_sql(name, con, index=False)
    con.execute("CREATE INDEX IF NOT EXISTS idx_orders_cust ON fact_orders(customer_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_items_order ON fact_items(order_id)")
    con.commit()
    con.close()
    print(f"[clean] SQLite 落库完成 -> {db}")


def main() -> None:
    prof = s1_profile()

    dim_c = build_customers()
    dim_p = build_products()
    dim_s = build_sellers()
    fo, items = build_fact_orders(dim_c, dim_p, dim_s)
    fo = attach_macro(fo)
    dim_d = build_dim_date(fo)

    # 观察窗标记（趋势/预测类只用窗口内数据，避免首尾截断月份造成假拐点）
    fo["in_window"] = fo.purchase_date.between(ANALYSIS_START, ANALYSIS_END).astype(int)

    tables = {
        "fact_orders": fo,
        "fact_items": items,
        "dim_customers": dim_c,
        "dim_products": dim_p,
        "dim_sellers": dim_s,
        "dim_date": dim_d,
    }
    save_all(tables)

    rep = pd.DataFrame(AUDIT)
    rep.to_csv(os.path.join(TBL, "data_quality_report.csv"), index=False, encoding="utf-8-sig")

    man = {
        "random_seed": RANDOM_SEED,
        "analysis_window": [str(ANALYSIS_START.date()), str(ANALYSIS_END.date())],
        "delivery_cap_days": DELIVERY_CAP_DAYS,
        "tables": {k: {"rows": int(len(v)), "cols": int(v.shape[1])} for k, v in tables.items()},
        "raw_profile": prof,
        "audit": AUDIT,
    }
    with open(os.path.join(CLEAN, "_clean_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=2, default=str)

    print("\n[clean] 清洗结果")
    for k, v in man["tables"].items():
        print(f"        {k:<16} {v['rows']:>8,} 行 x {v['cols']:>3} 列")
    print("\n[clean] 治理台账")
    for a in AUDIT:
        print(f"        {a['step']:<18} {a['table']:<26} {a['rows_before']:>8,} -> "
              f"{a['rows_after']:>8,}  {a['note']}")


if __name__ == "__main__":
    main()
