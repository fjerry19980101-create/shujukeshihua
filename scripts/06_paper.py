# -*- coding: utf-8 -*-
"""
06_paper.py —— 按学院模板排版生成期末大论文
========================================
输入：5、《商业数据分析》 - 期末大作业模板.docx（只读，不修改原件）
输出：docs/Olist电商用户价值分层与履约流失预警.docx

排版要点（严格对照模板批注）：
  论文题目 三号黑体居中；作者与单位 五号宋体居中；
  "摘要""关键词"标签 四号黑体、段前空两格；摘要与关键词正文 小四宋体、1.5 倍行距；
  正文 小四宋体、1.5 倍行距、首行缩进 2 字符；一级标题 三号黑体、二级标题 四号黑体；
  图题、表题 五号宋体居中；表格用三线表。
"""
from __future__ import annotations

import copy
import os
import shutil

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from _paper_content import build

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(BASE, "5、《商业数据分析》 - 期末大作业模板.docx")
DOCS = os.path.join(BASE, "docs")
FIG = os.path.join(BASE, "outputs", "figures")
DASH = os.path.join(BASE, "outputs", "dashboard")
os.makedirs(DOCS, exist_ok=True)
OUT = os.path.join(DOCS, "Olist电商用户价值分层与履约流失预警.docx")

# 封面信息（可在此处改）
COVER = {
    "题目": "Olist 电商用户价值分层与履约流失预警",
    "学院": "数据科学学院",
    "专业班级": "大数据 2 班",
    "学号": "2024XXXXXXX",
    "姓名": "范XX",
    "完成日期": "2026 年 10 月 22 日",
}
AUTHOR = "范XX"
AFFIL = "（嘉兴大学 数据科学学院）"


# ---------------------------------------------------------------- 工具
def set_run_font(run, cn_font="宋体", en_font="Times New Roman", size=12,
                 bold=False, color=None):
    run.font.name = en_font
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    rf.set(qn("w:ascii"), en_font)
    rf.set(qn("w:hAnsi"), en_font)
    rf.set(qn("w:eastAsia"), cn_font)


def zh(s: str) -> str:
    """把正文中的 ASCII 双引号按出现顺序转成中文引号，排版更符合中文论文规范。"""
    out, open_q = [], True
    for ch in str(s):
        if ch == '"':
            out.append("“" if open_q else "”")
            open_q = not open_q
        else:
            out.append(ch)
    return "".join(out)


def clear_runs(p):
    for r in list(p.runs):
        r._element.getparent().remove(r._element)


def add_par(doc, text="", size=12, bold=False, align=None, indent=True,
            space_before=0, space_after=0, line=1.5, cn_font="宋体",
            en_font="Times New Roman", style=None):
    p = doc.add_paragraph(style=style) if style else doc.add_paragraph()
    pf = p.paragraph_format
    if align is not None:
        p.alignment = align
    pf.line_spacing = line
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.first_line_indent = Pt(size * 2) if indent else Pt(0)
    if text:
        run = p.add_run(text)
        set_run_font(run, cn_font, en_font, size, bold)
    return p


def three_line(table, size=8.5):
    """把表格改成学术三线表：上下粗线、表头下细线、无竖线。"""
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for tag, sz in [("top", 12), ("bottom", 12), ("left", 0), ("right", 0),
                    ("insideH", 4), ("insideV", 0)]:
        el = OxmlElement(f"w:{tag}")
        el.set(qn("w:val"), "single" if sz else "none")
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:color"), "000000")
        borders.append(el)
    tblPr.append(borders)
    for row in table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.line_spacing = 1.0
                for run in p.runs:
                    set_run_font(run, "宋体", "Times New Roman", size)


def add_table(doc, caption, header, rows, widths):
    caption = zh(caption)
    cap = add_par(doc, caption, size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER,
                  indent=False, space_before=6, space_after=3, line=1.0)
    t = doc.add_table(rows=1, cols=len(header))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    # 固定布局 + 100% 页宽，避免 Word 按内容自动收缩导致列过窄、文字碎行
    t.autofit = False
    tblPr = t._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    tblW = OxmlElement("w:tblW")
    tblW.set(qn("w:type"), "pct")
    tblW.set(qn("w:w"), "5000")
    tblPr.append(tblW)
    hdr = t.rows[0].cells
    for i, h in enumerate(header):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(str(h))
        set_run_font(r, "宋体", "Times New Roman", 8.5, bold=True)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(str(v))
            set_run_font(r, "宋体", "Times New Roman", 8.5)
    scale = 15.4 / sum(widths)          # 统一缩放到页面正文宽度
    for i, w in enumerate(widths):
        t.columns[i].width = Cm(w * scale)
        for row in t.rows:
            row.cells[i].width = Cm(w * scale)
    # 表头跨页重复、行内不断页
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trPr.append(th)
    for row in t.rows:
        rp = row._tr.get_or_add_trPr()
        cs = OxmlElement("w:cantSplit")
        rp.append(cs)
    three_line(t)
    add_par(doc, "", size=6, indent=False, line=1.0)


def add_figure(doc, fname, caption, width=14.2):
    path = os.path.join(FIG, fname)
    if not os.path.exists(path):
        path = os.path.join(DASH, fname)
    if not os.path.exists(path):
        print(f"[warn] 缺图：{fname}")
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(path, width=Cm(width))
    add_par(doc, caption, size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER,
            indent=False, space_after=8, line=1.0)


def fill_cover_par(p, label, value):
    """保留段落的原有字体属性，替换文字内容。"""
    if p.runs:
        src = p.runs[0]
        cn = src.font.name or "宋体"
        size = src.font.size.pt if src.font.size else 12
        bold = bool(src.bold)
        underline = src.underline
    else:
        cn, size, bold, underline = "宋体", 12, False, None
    clear_runs(p)
    r = p.add_run(f"{label}{value}")
    set_run_font(r, "宋体", "Times New Roman", size, bold)
    if underline:
        r.underline = True


# ---------------------------------------------------------------- 主流程
def main() -> None:
    title, abstract, keywords, blocks = build()

    # 备份原件，然后复制一份作为工作副本
    bak = os.path.join(BASE, "docs", "模板备份_期末大作业模板.docx")
    if not os.path.exists(bak):
        shutil.copy2(TPL, bak)
    doc = Document(TPL)

    # ---- 封面 ----
    for p in doc.paragraphs[:12]:
        t = p.text.strip()
        for k in ("题目", "学院", "专业班级", "学号", "姓名", "完成日期"):
            if t.replace("\u3000", "").startswith(k):
                fill_cover_par(p, f"{k}：".replace("题目", "题　　目").replace("学院", "学　　院")
                               .replace("学号", "学　　号").replace("姓名", "姓　　名"), COVER[k])
                break

    # ---- 定位正文起点：删除"注意：全文红色字体…"及其后全部内容 ----
    # 模板第二页以"数 据 科 学 学 院"开头（其前是封面与评分表的节），
    # 从这里往后全部是占位内容，一律删除后由本脚本重建。
    ps = doc.paragraphs
    cut = None
    for i, p in enumerate(ps):
        if p.text.replace(" ", "").replace("\u3000", "") == "数据科学学院" and i > 5:
            cut = i
            break
    if cut is None:
        raise RuntimeError("未找到模板第二页起始段，无法定位正文起点")
    body = doc.element.body
    for p in ps[cut:]:
        body.remove(p._element)
    # 表格（评分表）保留；其余表格若在正文后一并清理（本模板只有评分表）
    for tbl in doc.tables[1:]:
        body.remove(tbl._tbl)

    # ---- 第二页标题区 ----
    # 删除模板残留的空段，重建标题块
    while doc.paragraphs and not doc.paragraphs[-1].text.strip():
        body.remove(doc.paragraphs[-1]._element)

    p = add_par(doc, title, size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
                indent=False, space_before=6, space_after=6, line=1.5, cn_font="黑体")
    add_par(doc, AUTHOR, size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, line=1.5)
    add_par(doc, AFFIL, size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False,
            space_after=8, line=1.5)

    # ---- 摘要 ----
    ab = doc.add_paragraph()
    ab.paragraph_format.line_spacing = 1.5
    ab.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    ab.paragraph_format.first_line_indent = Pt(28)
    ab.paragraph_format.space_after = Pt(4)
    r1 = ab.add_run("摘要：")
    set_run_font(r1, "黑体", "Times New Roman", 14, bold=True)
    r2 = ab.add_run(abstract)
    set_run_font(r2, "宋体", "Times New Roman", 12)

    kw = doc.add_paragraph()
    kw.paragraph_format.line_spacing = 1.5
    kw.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    kw.paragraph_format.first_line_indent = Pt(28)
    kw.paragraph_format.space_after = Pt(10)
    k1 = kw.add_run("关键词：")
    set_run_font(k1, "黑体", "Times New Roman", 14, bold=True)
    k2 = kw.add_run(keywords)
    set_run_font(k2, "宋体", "Times New Roman", 12)

    # ---- 正文 ----
    for blk in blocks:
        kind = blk[0]
        blk = (blk[0],) + tuple(zh(x) if isinstance(x, str) else x for x in blk[1:3]) + tuple(blk[3:])
        if kind == "h1":
            add_par(doc, blk[1], size=16, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT,
                    indent=False, space_before=14, space_after=8, line=1.5, cn_font="黑体")
        elif kind == "h2":
            add_par(doc, blk[1], size=14, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT,
                    indent=False, space_before=10, space_after=6, line=1.5, cn_font="黑体")
        elif kind == "p":
            add_par(doc, blk[1], size=12, indent=True, space_after=3)
        elif kind == "ref":
            q = add_par(doc, blk[1], size=10.5, indent=False, space_after=2, line=1.3)
            q.paragraph_format.left_indent = Pt(21)
            q.paragraph_format.first_line_indent = Pt(-21)
        elif kind == "code":
            q = add_par(doc, blk[1] if len(blk) > 1 else "", size=9, indent=False,
                        space_after=0, line=1.0, cn_font="宋体", en_font="Consolas")
            q.paragraph_format.left_indent = Pt(18)
        elif kind == "fig":
            add_figure(doc, blk[1], blk[2])
        elif kind == "tbl":
            add_table(doc, blk[1], blk[2], blk[3], blk[4])
        else:
            raise ValueError(kind)

    # ---- 页脚页码 ----
    for section in doc.sections:
        footer = section.footer
        p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if not p.text:
            run = p.add_run()
            for el, attr in [("w:fldChar", {"w:fldCharType": "begin"}),
                             ("w:instrText", None)]:
                e = OxmlElement(el)
                if attr:
                    for k, v in attr.items():
                        e.set(qn(k), v)
                else:
                    e.set(qn("xml:space"), "preserve")
                    e.text = " PAGE "
                run._r.append(e)
            end = OxmlElement("w:fldChar")
            end.set(qn("w:fldCharType"), "end")
            run._r.append(end)
            set_run_font(run, "宋体", "Times New Roman", 9)

    doc.save(OUT)

    # 统计字数
    chars = sum(len(b[1]) for b in blocks if b[0] in ("p", "h1", "h2"))
    nfig = sum(1 for b in blocks if b[0] == "fig")
    ntbl = sum(1 for b in blocks if b[0] == "tbl")
    print(f"[paper] 已生成 {OUT}")
    print(f"[paper] 正文字数约 {chars:,} 字｜图 {nfig} 张｜表 {ntbl} 张")


if __name__ == "__main__":
    main()
