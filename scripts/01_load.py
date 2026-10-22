# -*- coding: utf-8 -*-
"""
01_load.py —— 数据获取（白名单方式，全程无爬虫）
================================================
数据源 : Kaggle · Brazilian E-Commerce Public Dataset by Olist
主页   : https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
方式   : Kaggle 官方 Dataset API（https://www.kaggle.com/api/v1/datasets/download/<owner>/<dataset>）
         —— 与 Kaggle 官方 CLI(`kaggle datasets download`) 同一后端，属课程附件 A 白名单第 2 类
         "官方或社区维护的 Python/CLI 数据接口库"，不涉及任何网页解析、模拟登录或抓取。
许可   : CC BY-NC-SA 4.0（数据集主页 License 字段）

产物:
  data/raw/*.csv                9 张原始表（原样落盘，不做任何修改）
  data/raw/_manifest.json       下载溯源清单（URL / 时间 / 字节数 / SHA256 / 行数）
"""
from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
import os
import sys
import urllib.request
import zipfile

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
DATASET = "olistbr/brazilian-ecommerce"
URL = f"https://www.kaggle.com/api/v1/datasets/download/{DATASET}"
LICENSE = "CC BY-NC-SA 4.0"
EXPECTED_TABLES = [
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def already_ok() -> bool:
    """9 张表都在就不再重复下载（幂等，便于 run_all.py 反复执行）。"""
    return all(os.path.exists(os.path.join(RAW, t)) for t in EXPECTED_TABLES)


def download() -> None:
    os.makedirs(RAW, exist_ok=True)
    print(f"[load] 下载 {URL}")
    req = urllib.request.Request(URL, headers={"User-Agent": "olist-coursework/1.0"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        payload = resp.read()
    print(f"[load] 收到 {len(payload)/1e6:.1f} MB，校验 zip 结构")
    zf = zipfile.ZipFile(io.BytesIO(payload))
    names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
    missing = set(EXPECTED_TABLES) - set(names)
    if missing:
        raise RuntimeError(f"压缩包缺少表: {missing}")

    # 原样解压到 data/raw（不解码、不改列名，保证原始层可追溯）
    for n in names:
        with zf.open(n) as src, open(os.path.join(RAW, n), "wb") as dst:
            dst.write(src.read())
    zpath = os.path.join(RAW, "_olist_raw.zip")
    with open(zpath, "wb") as f:
        f.write(payload)
    print(f"[load] 已解压 {len(names)} 张表 -> {RAW}")


def build_manifest() -> dict:
    rows = {}
    for t in EXPECTED_TABLES:
        p = os.path.join(RAW, t)
        # 注意：评价表正文含换行符，按物理行数统计会虚高，必须交由 CSV 解析器计数
        n_rows = int(pd.read_csv(p, usecols=[0]).shape[0])
        rows[t] = {
            "rows": n_rows,
            "bytes": os.path.getsize(p),
            "sha256": sha256_of(p)[:16],
        }
    return {
        "dataset": DATASET,
        "homepage": f"https://www.kaggle.com/datasets/{DATASET}",
        "download_api": URL,
        "license": LICENSE,
        "download_time": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "tables": rows,
        "total_rows": int(sum(v["rows"] for v in rows.values())),
    }


def main() -> None:
    if not already_ok():
        download()
    else:
        print("[load] data/raw 已完整，跳过下载（如需重下请删除该目录）")

    man = build_manifest()
    with open(os.path.join(RAW, "_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=2)

    print(f"[load] 合计 {man['total_rows']:,} 行 / {len(man['tables'])} 表")
    for k, v in man["tables"].items():
        print(f"        {k:<42} {v['rows']:>9,} 行  {v['bytes']/1e6:>7.2f} MB")

    # 规模校验：课程要求主表 ≥ 500 行
    main_rows = man["tables"]["olist_orders_dataset.csv"]["rows"]
    assert main_rows >= 500, "主表行数未达课程要求"
    print(f"[load] 主表 {main_rows:,} 行，满足 ≥500 行要求")


if __name__ == "__main__":
    sys.exit(main())
