# -*- coding: utf-8 -*-
"""
run_all_figs.py —— 顺序执行 24 张图的独立脚本
==========================================
每张图都是一个可单独 `python figXX_xxx.py` 运行的脚本；
这里只负责按编号顺序批量调用，任何一张失败都会中断并报出文件名。
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def main() -> int:
    files = sorted(f for f in glob.glob(os.path.join(HERE, "fig*.py")))
    if not files:
        print("未找到 fig*.py")
        return 1
    ok = 0
    for f in files:
        name = os.path.basename(f)
        r = subprocess.run([PY, f], cwd=HERE)
        if r.returncode != 0:
            print(f"[FAIL] {name}")
            return 1
        ok += 1
    print(f"\n共 {ok} 张图完成 → outputs/figures/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
