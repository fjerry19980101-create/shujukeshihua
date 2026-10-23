# -*- coding: utf-8 -*-
r"""
07_build_equations.py —— 把线性公式转成 Word 原生公式对象（OMML）
===============================================================
python-docx 只能写普通文本，写不出可编辑的 Word 公式。
本脚本用 Word COM 的 OMaths.BuildUp() 完成转换：
  ① 06_paper.py 把公式写成“线性 Math 文本 + 末尾标记 ⟦EQ⟧”；
  ② 这里打开 docx，逐段找到带标记的段落，删掉标记，
     把“公式文本”那一段 Range 交给 OMaths.Add()，再 BuildUp()；
  ③ Word 会把它变成可双击编辑的原生公式对象（OMML）。
Word 的线性数学语法与 LaTeX 接近但不完全相同，故 06_paper.py 里
给出的就是线性写法（^ 上标、_ 下标、/ 分数、\sum 求和）。
r"""
from __future__ import annotations

import os
import sys

import glob
import shutil
import tempfile

import win32com.client as win32

# Word 与 WPS 都注册了 Word.Application；gen_py 缓存可能绑定到 WPS（无 OMath），
# 每次运行前清掉缓存并用 DispatchEx 拿到真正的 Word。
for _d in glob.glob(os.path.join(tempfile.gettempdir(), "gen_py*")):
    shutil.rmtree(_d, ignore_errors=True)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCX = os.path.join(BASE, "docs", "Olist电商用户价值分层与履约流失预警.docx")
MARK = "⟦EQ⟧"


def main() -> int:
    if not os.path.exists(DOCX):
        print("找不到 docx：", DOCX)
        return 1

    # 直接按 CLSID 取 Word 应用对象：ProgID "Word.Application" 在本机被 WPS 抢占，
    # 用 CLSID 才能确保拿到微软 Word（只有它支持 OMaths.BuildUp）。
    # 注意：必须先清 gen_py 缓存，再用 EnsureDispatch(CLSID) 绑定到微软 Word 的类型库；
    # 若用 Dispatch，pywin32 可能沿用 WPS 的类型库，拿到的 Range 没有 BuildUp 方法。
    word = win32.gencache.EnsureDispatch("{000209FF-0000-0000-C000-000000000046}")
    word.Visible = False
    word.DisplayAlerts = False
    doc = word.Documents.Open(DOCX)

    done, failed = 0, 0
    try:
        # 若文档里已存在公式对象（重复运行时），先统一 BuildUp 一遍
        if doc.OMaths.Count:
            for k in range(1, doc.OMaths.Count + 1):
                try:
                    doc.OMaths(k).BuildUp()
                except Exception:
                    pass
        # 从后往前处理：先删标记会改变段落长度，倒序可避免影响未处理段落
        total = doc.Paragraphs.Count
        targets = []
        for i in range(1, total + 1):
            p = doc.Paragraphs(i)
            t = p.Range.Text
            if MARK in t:
                targets.append(i)

        for i in reversed(targets):
            p = doc.Paragraphs(i)
            t = p.Range.Text
            pos = t.rfind(MARK)
            if pos < 0:
                continue
            # ① 删掉标记
            doc.Range(p.Range.Start + pos, p.Range.Start + pos + len(MARK)).Delete()
            # ② 重新取段落文本，定位公式终点（编号“（4-x）”之前）
            t = p.Range.Text
            cut = t.find("（")
            if cut < 0:
                cut = max(len(t) - 1, 0)
            try:
                rng = doc.Range(p.Range.Start, p.Range.Start + cut)
                doc.OMaths.Add(rng)          # 先转成公式对象（线性状态）
                done += 1
            except Exception as e:      # 单条失败不影响整体
                failed += 1
                print(f"  [warn] 第 {i} 段公式转换失败：{e}")

        # 统一 BuildUp：遍历整个 OMaths 集合，已构建的重复调用无副作用
        built = 0
        for k in range(1, doc.OMaths.Count + 1):
            try:
                doc.OMaths(k).BuildUp()
                built += 1
            except Exception as e:
                print(f"  [warn] 第 {k} 个公式 BuildUp 失败：{e}")
        print(f"[eq] BuildUp {built} 条")
        doc.Save()
        print(f"[eq] 转换成功 {done} 条，失败 {failed} 条（共发现 {len(targets)} 条）")
    finally:
        doc.Close(True)
        word.Quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
