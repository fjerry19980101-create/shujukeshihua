# -*- coding: utf-8 -*-
"""
_style.py —— 图表统一版式（对标《Excel数据可视化》教材模板）
=========================================================
教材 30 套模板的共性版式被固化成这里的常量与函数：
  画布 1088×794（16:11.7）、深蓝底 #1A1E43、白色粗体大标题、
  次行灰色副标题（一句话结论）、右下角*注脚*、无边框无刻度线、
  深灰虚线网格、类别标签浅灰、数值标签白色、主色为蓝到浅蓝的竖向渐变。

任何一张图都只通过 new_canvas() + chrome() + save() 三件套生成，
从而保证 24 张图"像同一个人做的"——这正是评分项"配色协调统一"的要求。
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle

# ---------------- 画布 ----------------
W, H, DPI = 1088, 794, 100
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TBL = os.path.join(BASE, "outputs", "tables")
FIG = os.path.join(BASE, "outputs", "figures")
os.makedirs(FIG, exist_ok=True)

# ---------------- 配色 ----------------
BG = "#1A1E43"
GRID = "#404361"
WHITE = "#FFFFFF"
SOFT = "#F2F2F2"
CAT = "#BBBCC5"
NOTE = "#D9D9D9"
ACCENT = "#F2B705"      # 强调黄（均值线、关键标注）
ORANGE = "#ED7D31"
RED = "#D64550"
TEAL = "#3CC7C0"
PURPLE = "#8E7CF0"
BAR_TOP = (0, 176, 240)   # 柱顶亮蓝
BAR_BOT = (0, 112, 192)   # 柱底深蓝
SEQ = ["#2E86DE", "#3CC7C0", "#F2B705", "#ED7D31", "#8E7CF0", "#D64550",
       "#7FB3D5", "#A3E4D7"]

# ---------------- 字体 ----------------
FONT_REG = "C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FP = fm.FontProperties(fname=FONT_REG)
FPB = fm.FontProperties(fname=FONT_BOLD)
plt.rcParams["font.family"] = FP.get_name()
plt.rcParams["axes.unicode_minus"] = False

# 版式坐标（与教材模板逐像素对齐后换算成 figure 比例）
PLOT = (0.145, 0.155, 0.755, 0.525)     # left, bottom, width, height
X_TITLE, Y_TITLE = 0.082, 0.872
X_SUB, Y_SUB = 0.079, 0.784
X_NOTE, Y_NOTE = 0.061, 0.047


def new_canvas(plot: tuple = PLOT, dark: bool = True):
    """新建画布并返回 (fig, ax)。ax 已去掉边框与刻度，只保留数据区。"""
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI,
                     facecolor=BG if dark else "#FFFFFF")
    ax = fig.add_axes(list(plot))
    ax.set_facecolor(BG if dark else "#FFFFFF")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID if dark else "#BFBFBF")
    ax.spines["bottom"].set_linewidth(1.2)
    ax.tick_params(axis="both", colors=CAT if dark else "#595959",
                   labelsize=13, length=0, pad=8)
    ax.grid(axis="y", color=GRID if dark else "#E3E3E3",
            linestyle=(0, (8, 3)), linewidth=0.9, alpha=0.9)
    ax.set_axisbelow(True)
    return fig, ax


def _fit_text(fig, x, y, text, size, min_size, max_w, fp, color):
    """写文字并按可用宽度自动缩字号，保证任何长度的标题/副标题都不会被截断。
    以 100dpi 下的像素宽度度量（画布宽 1088px），与版式坐标同一坐标系。"""
    t = fig.text(x, y, text, fontsize=size, color=color, ha="left", va="baseline",
                 fontproperties=fp)
    try:
        renderer = fig.canvas.get_renderer()
        while size > min_size and t.get_window_extent(renderer).width > max_w:
            size -= 0.5
            t.set_fontsize(size)
    except Exception:
        pass
    return t


def chrome(fig, title: str, subtitle: str = "", note: str = "", dark: bool = True,
           title_size: float = 30, sub_size: float = 18.5, note_size: float = 12.5):
    """写标题/副标题/脚注。标题用左对齐粗体，副标题承载"一句话结论"。
    三者都会按可用宽度自动缩字号（标题最低 22pt、副标题最低 13pt、脚注最低 10pt），
    避免中文长句在 1088px 画布上溢出——这是 24 张图版式统一的关键。"""
    c_title = WHITE if dark else "#1F1F1F"
    c_sub = WHITE if dark else "#404040"
    c_note = NOTE if dark else "#7F7F7F"
    _fit_text(fig, X_TITLE, Y_TITLE, title, title_size, 22, W * 0.87, FPB, c_title)
    if subtitle:
        _fit_text(fig, X_SUB, Y_SUB, subtitle, sub_size, 13, W * 0.885, FP, c_sub)
    if note:
        _fit_text(fig, X_NOTE, Y_NOTE, note, note_size, 10, W * 0.90, FP, c_note)


def gradient_vbar(ax, xc: float, height: float, width: float = 0.55,
                  bottom: float = 0.0, n: int = 120,
                  c_top=BAR_TOP, c_bot=BAR_BOT, zorder: int = 2) -> None:
    """竖向渐变柱：逐段插值，亮度从上到下衰减（教材模板的柱体观感）。"""
    if height <= 0:
        return
    ys = np.linspace(0, 1, n + 1)
    for i in range(n):
        t = ys[i]                       # 0 在底部，1 在顶部
        col = tuple((c_bot[k] + (c_top[k] - c_bot[k]) * t) / 255 for k in range(3))
        ax.add_patch(Rectangle((xc - width / 2, bottom + height * ys[i]),
                               width, height * (ys[i + 1] - ys[i]),
                               facecolor=col, edgecolor="none", zorder=zorder))


def gradient_hbar(ax, yc: float, length: float, height: float = 0.55,
                  left: float = 0.0, n: int = 120,
                  c_left=BAR_BOT, c_right=BAR_TOP, zorder: int = 2) -> None:
    """横向渐变条：左深右亮，用于条形排名图。"""
    xs = np.linspace(0, 1, n + 1)
    for i in range(n):
        t = xs[i]
        col = tuple((c_left[k] + (c_right[k] - c_left[k]) * t) / 255 for k in range(3))
        ax.add_patch(Rectangle((left + length * xs[i], yc - height / 2),
                               length * (xs[i + 1] - xs[i]), height,
                               facecolor=col, edgecolor="none", zorder=zorder))


def gradient_vbar_rounded(ax, xc: float, height: float, width: float = 0.55,
                          n: int = 200, c_top=BAR_TOP, c_bot=BAR_BOT,
                          zorder: int = 2, rounding: float = 0.12) -> None:
    """顶部圆角渐变柱：用一张竖向渐变图 + 圆角矩形裁剪路径实现，
    避免逐段矩形在圆角处露出锯齿（教材《3 渐变圆角柱形图》的做法）。"""
    if height <= 0:
        return
    from matplotlib.patches import FancyBboxPatch
    patch = FancyBboxPatch((xc - width / 2, 0), width, height,
                           boxstyle=f"round,pad=0,rounding_size={rounding}",
                           linewidth=0, facecolor="none", edgecolor="none",
                           mutation_aspect=1.0, zorder=zorder)
    ax.add_patch(patch)
    grad = np.linspace(0, 1, n).reshape(-1, 1)
    rgb = np.zeros((n, 1, 3))
    for k in range(3):
        rgb[:, 0, k] = (c_bot[k] + (c_top[k] - c_bot[k]) * grad[:, 0]) / 255
    im = ax.imshow(rgb, extent=[xc - width / 2, xc + width / 2, 0, height],
                   aspect="auto", origin="lower", zorder=zorder,
                   interpolation="bilinear")
    im.set_clip_path(patch)


def save(fig, name: str, dpi: int = 150) -> str:
    """统一导出：150 dpi，满足课程"分辨率 ≥150dpi"要求。"""
    path = os.path.join(FIG, name)
    fig.savefig(path, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[fig] {name}")
    return path


def load(name: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(TBL, name))


def kpi() -> dict:
    import json
    with open(os.path.join(TBL, "kpi_overview.json"), encoding="utf-8") as f:
        return json.load(f)


def money(v: float) -> str:
    """金额缩写：1.2万 / 1.2亿（中文习惯，便于标题内嵌数字）。"""
    if abs(v) >= 1e8:
        return f"{v/1e8:.1f}亿"
    if abs(v) >= 1e4:
        return f"{v/1e4:.1f}万"
    return f"{v:,.0f}"


# ---------------- 品类中文名（Olist 原始为葡语/英语，报告中统一中文呈现） ----------------
CATEGORY_CN = {
    "health_beauty": "健康美妆", "watches_gifts": "手表礼品", "bed_bath_table": "床品家纺",
    "sports_leisure": "运动休闲", "computers_accessories": "电脑配件",
    "furniture_decor": "家具装饰", "housewares": "家居厨具", "cool_stuff": "潮流好物",
    "auto": "汽车用品", "garden_tools": "园艺工具", "toys": "玩具", "baby": "母婴用品",
    "perfumery": "香水", "telephony": "手机通讯", "office_furniture": "办公家具",
    "luggage_accessories": "箱包配件", "fashion_bags_accessories": "时尚包袋",
    "home_appliances": "家用电器", "home_appliances_2": "家电II", "air_conditioning": "空调",
    "audio": "音频设备", "consoles_games": "游戏主机", "electronics": "消费电子",
    "computers": "电脑整机", "fixed_telephony": "固定电话", "tablets_printing_image": "平板影像",
    "small_appliances": "小家电", "small_appliances_home_oven_and_coffee": "小家电(烤箱咖啡)",
    "furniture_living_room": "客厅家具", "furniture_bedroom": "卧室家具",
    "kitchen_dining_laundry_garden_furniture": "厨房餐厨家具",
    "home_construction": "家装建材", "construction_tools_construction": "建筑工具",
    "costruction_tools_garden": "园艺工具(建材)", "construction_tools_lights": "建筑照明",
    "construction_tools_safety": "建筑安全", "signaling_and_security": "安防监控",
    "fashion_shoes": "时尚鞋履", "fashion_male_clothing": "男装", "fashion_female_clothing": "女装",
    "fashion_underwear_beach": "内衣泳装", "fashion_sport": "运动时尚",
    "fashion_accessories": "时尚配饰", "bags": "箱包", "diapers_and_hygiene": "尿裤卫生",
    "drinks": "饮料", "food": "食品", "food_drink": "食品饮料", "la_cuisine": "厨具",
    "home_confort": "家居舒适", "home_comfort_2": "家居舒适II", "music": "音乐",
    "art": "艺术品", "arts_and_craftmanship": "手工艺", "christmas_supplies": "圣诞用品",
    "party_supplies": "派对用品", "pet_shop": "宠物用品",
    "agro_industry_and_commerce": "农业商贸", "industry_commerce_and_business": "工业商贸",
    "books_general_interest": "综合图书", "books_technical": "技术图书",
    "books_imported": "进口图书", "cds_dvds_musicals": "音像制品", "dvds_blu_ray": "DVD蓝光",
    "cine_photo": "影像器材", "musical_instruments": "乐器", "security_and_services": "安保服务",
    "fashion_childrens_clothes": "童装", "unknown": "未分类",
}


def cn(name: str) -> str:
    """品类英文名 -> 中文名；同时兼容下划线与空格两种写法。"""
    n = str(name)
    if n in CATEGORY_CN:
        return CATEGORY_CN[n]
    return CATEGORY_CN.get(n.replace(" ", "_"), n)


def note_src(extra: str = "") -> str:
    base = "*注：数据来源于 Kaggle Olist 巴西电商公开数据集（2017.01–2018.08）"
    return base + ("；" + extra if extra else "")
