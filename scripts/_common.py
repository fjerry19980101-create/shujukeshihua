# -*- coding: utf-8 -*-
"""
_common.py —— 全项目共用的路径、加载器与写盘工具
=================================================
所有分析/作图脚本只从这里取数据，保证"洗一次、处处一致"。
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN = os.path.join(BASE, "data", "clean")
RAW_AUX = os.path.join(BASE, "data", "raw_aux")
TBL = os.path.join(BASE, "outputs", "tables")
FIG = os.path.join(BASE, "outputs", "figures")
DASH = os.path.join(BASE, "outputs", "dashboard")
for d in (TBL, FIG, DASH):
    os.makedirs(d, exist_ok=True)

# 观察窗（2016 年样本稀疏、2018-09 起截断，趋势/预测只用窗内数据）
ANALYSIS_END = pd.Timestamp("2018-08-31")
CUTOFF_DATE = ANALYSIS_END          # RFM 的 Recency 基准日

# 统一配色（与教材模板的深蓝主色系一致，全书图表共用一套色板）
PALETTE = {
    "primary": "#1F4E79",       # 主色：深蓝
    "secondary": "#2E75B6",     # 次色：中蓝
    "accent": "#ED7D31",        # 强调色：橙
    "warm": "#F2B705",          # 暖黄
    "teal": "#2A9D8F",
    "red": "#C00000",
    "grey": "#7F7F7F",
    "light": "#D6E4F0",
    "dark_bg": "#1B1F3B",       # 大屏深色背景
}
SEQ_BLUE = ["#D6E4F0", "#9DC3E6", "#5B9BD5", "#2E75B6", "#1F4E79", "#153B5B"]


def load_orders(with_window: bool = True) -> pd.DataFrame:
    """订单事实表。with_window=True 时只保留趋势观察窗内的订单。
    注意：RFM/同期群/漏斗等"存量类"分析用全量，趋势/预测用窗内。
    """
    fo = pd.read_csv(
        os.path.join(CLEAN, "fact_orders.csv"),
        parse_dates=["order_purchase_timestamp", "order_approved_at",
                     "order_delivered_carrier_date", "order_delivered_customer_date",
                     "order_estimated_delivery_date", "purchase_date", "purchase_week"],
        low_memory=False,
    )
    if with_window:
        fo = fo[fo.in_window == 1].copy()
    return fo


def load_items() -> pd.DataFrame:
    return pd.read_csv(os.path.join(CLEAN, "fact_items.csv"))


def load_dim(name: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(CLEAN, f"dim_{name}.csv"))


def load_macro() -> pd.DataFrame:
    p = os.path.join(RAW_AUX, "bcb_macro_monthly.csv")
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()


def save_table(df: pd.DataFrame, name: str) -> None:
    df.to_csv(os.path.join(TBL, name), index=False, encoding="utf-8-sig")
    print(f"[table] {name:<34} {len(df):>7,} 行")


def save_json(obj: dict, name: str) -> None:
    with open(os.path.join(TBL, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)
    print(f"[json ] {name}")


def delivered_only(fo: pd.DataFrame) -> pd.DataFrame:
    """履约分析口径：已妥投且未超 180 天截尾。"""
    return fo[(fo.is_delivered == 1) & (fo.delivery_is_capped == 0)].copy()
