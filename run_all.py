# -*- coding: utf-8 -*-
"""
run_all.py —— 一键复现入口
=========================
按依赖顺序跑完整条链路：取数 → 清洗 → 建模 → 出图 → 大屏 → 论文。

用法:
  python run_all.py                 # 全链路
  python run_all.py --skip-data     # 已有 data/raw 时跳过下载
  python run_all.py --only figures  # 只重跑某一阶段（data/clean/analysis/figures/dashboard/paper）

设计说明:
  每个阶段用 subprocess 调独立脚本，而不是 import，
  这样单步失败时能直接看到是哪个脚本、哪一行报错，也方便单独重跑。
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

STAGES = {
    "data": [
        ("scripts/01_load.py", "下载并校验 9 张原始表", None),
        ("scripts/01b_aux.py", "拉取 BCB 宏观序列（辅助源，可选）", "warn"),
    ],
    "clean": [
        ("scripts/02_clean.py", "清洗治理 → CSV + SQLite + 治理台账", None),
    ],
    "analysis": [
        ("scripts/03_analysis_overview.py", "经营总览 / 环比同比 / 三口径", None),
        ("scripts/03_analysis_rfm.py", "RFM 八分类 + K-Means 交叉验证", None),
        ("scripts/03_analysis_cohort.py", "同期群留存", None),
        ("scripts/03_analysis_bcg.py", "波士顿矩阵 + 帕累托 ABC + 卖家集中度", None),
        ("scripts/03_analysis_basket.py", "Apriori 关联规则 + Cramér's V", None),
        ("scripts/03_analysis_forecast.py", "SARIMA 网格搜索 + 回测 + 外推", None),
        ("scripts/03_analysis_funnel.py", "履约漏斗 + 延迟归因 + 反事实", None),
    ],
    "figures": [
        ("代码/run_all_figs.py", "24 张图（每图一份独立脚本）", None),
    ],
    "dashboard": [
        ("scripts/05_dashboard.py", "自包含交互大屏 HTML", None),
    ],
    "paper": [
        ("scripts/06_paper.py", "按学院模板生成论文 docx", None),
        ("scripts/07_build_equations.py", "把线性公式转成 Word 原生公式（需本机 Word）", "warn"),
    ],
}

ORDER = ["data", "clean", "analysis", "figures", "dashboard", "paper"]


def run_one(rel: str, desc: str, tolerate: str | None) -> bool:
    path = os.path.join(BASE, rel)
    if not os.path.exists(path):
        msg = f"缺少脚本 {rel}"
        if tolerate == "warn":
            print(f"  [skip] {msg}")
            return True
        print(f"  [FAIL] {msg}")
        return False
    t0 = time.time()
    print(f"  → {desc}  ({rel})")
    r = subprocess.run([PY, path], cwd=os.path.dirname(path) or BASE)
    dt = time.time() - t0
    if r.returncode != 0:
        if tolerate == "warn":
            print(f"  [warn] {rel} 返回码 {r.returncode}（可选阶段，继续）")
            return True
        print(f"  [FAIL] {rel} 返回码 {r.returncode}，耗时 {dt:.1f}s")
        return False
    print(f"  [ok] {dt:.1f}s")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-data", action="store_true", help="跳过下载阶段")
    ap.add_argument("--only", choices=ORDER, help="只跑某一阶段")
    args = ap.parse_args()

    stages = [args.only] if args.only else ORDER
    if args.skip_data and "data" in stages:
        stages.remove("data")

    t_all = time.time()
    for st in stages:
        print(f"\n===== 阶段：{st} =====")
        for rel, desc, tol in STAGES[st]:
            if not run_one(rel, desc, tol):
                print("\n中止：请先修复上述错误。")
                return 1
    print(f"\n全部完成，总耗时 {time.time() - t_all:.1f}s")
    print("产物：outputs/figures、outputs/tables、outputs/dashboard、docs/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
