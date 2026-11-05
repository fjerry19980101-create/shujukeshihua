# Olist 电商用户价值分层与履约流失预警

> 《商业数据分析》期末大作业 · 大数据专业
> 一条从「合规取数 → 清洗治理 → 商业建模 → 可视化复现 → 交互大屏 → 商业建议」的完整链路。

---

## 1. 项目一句话结论

Olist 2018 年 1—8 月名义 GMV 同比 **+137%**，但扣除通胀与汇率后仅 **+112%**；复购客户只占 **3.11%**，M+1 留存即跌破 **1%**；延迟订单评分从 **4.30** 掉到 **2.57**，而延迟增量的 **93%** 发生在承运之后、不在卖家手里。进一步反事实模拟显示：**把承诺时效从 13 天放宽到 15 天，延迟率可从 10.4% 降到 6.0%**——不花一分钱运力成本。

---

## 2. 数据来源与合规

| 项 | 内容 |
|---|---|
| 主数据源 | Kaggle · Brazilian E-Commerce Public Dataset by Olist |
| 主页 | https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce |
| 获取方式 | **Kaggle 官方 Dataset API**：`https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce`（与官方 CLI `kaggle datasets download` 同一后端） |
| 授权 | CC BY-NC-SA 4.0 |
| 获取日期 | 2026-10-22 |
| 规模 | 9 张表、1,550,922 行、44.7 MB |
| 辅助数据源 | 巴西中央银行 SGS 开放数据（IPCA / Selic / USD-BRL），`https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados`，免登录、免密钥 |
| 辅助源用途 | 把名义 GMV 拆成「实际价」与「美元」两个口径，剔除通胀与汇率幻觉 |

**合规性声明**：全流程未使用 Scrapy、Selenium、`requests`+网页解析、模拟登录等任何爬虫手段；不涉及任何网页抓取。数据不含姓名、证件号等个人身份信息，客户标识为脱敏哈希。详见 [`docs/数据来源合规声明.md`](docs/数据来源合规声明.md)。

> 关于天池（tianchi.aliyun.com）：平台数据集下载接口需登录态，匿名请求返回 302。本项目最终以 BCB 官方开放接口作为辅助源（属课程附件 A 白名单第 3 类「政府/国际组织开放平台」），合规性更强；天池保留为备选源，未实际使用。

---

## 3. 目录结构

```
shujukeshihua/
├── data/
│   ├── raw/                 9 张原始 CSV（原样落盘）+ _manifest.json（URL/时间/SHA256/行数）
│   ├── raw_aux/             BCB 宏观月度序列 + 抓取清单
│   └── clean/               清洗后 CSV + olist.db(SQLite) + _clean_manifest.json
├── scripts/
│   ├── 01_load.py           数据获取（Kaggle 官方 API）
│   ├── 01b_aux.py           辅助源获取（BCB 开放接口）
│   ├── 02_clean.py          清洗治理 → 星型模型 + SQLite
│   ├── 03_analysis_*.py     7 个模型脚本（总览/RFM/同期群/BCG/关联/预测/漏斗）
│   ├── 05_dashboard.py      交互大屏（自包含 HTML）
│   ├── 06_paper.py          按学院模板生成论文 docx（--full 生成完整版）
│   ├── 07_build_equations.py 8 条公式转 Word 原生 OMML
│   ├── _paper_content.py    送审版正文源
│   └── _paper_content_full.py 未删减完整版正文源
├── 代码/                    ★ 每张图一份独立脚本（fig01–fig24）
│   ├── _style.py            统一版式（画布/配色/字体/标题-副标题-注脚）
│   └── fig*.py              可单独运行，各自产出 outputs/figures 下的一张图
├── outputs/
│   ├── figures/             24 张 150 dpi 图表
│   ├── tables/              各模型结果表（论文中所有数字的唯一来源）
│   └── dashboard/           olist_dashboard.html（1.1 MB，离线可开）+ 截图
├── docs/                    论文送审版 + 完整版（docx/pdf）、合规声明、图表索引
├── assets/echarts.min.js    ECharts 5.5（内联进大屏，保证离线可用）
├── requirements.txt
├── run_all.py               一键复现入口
└── README.md
```

---

## 4. 复现步骤

### 4.1 环境

```bash
python -m venv --system-site-packages .venv      # 若本机已有科学栈可继承
.venv\Scripts\activate                            # Windows
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

环境基线：Python 3.11+ / pandas 2.2 / matplotlib 3.9 / seaborn 0.13 / statsmodels 0.14 / scikit-learn 1.5 / mlxtend 0.23 / pyecharts 2.0 / python-docx 1.2。中文字体需系统自带 `SimHei`、`Microsoft YaHei`（Windows 默认具备）。

### 4.2 一键复现

```bash
python run_all.py            # 全链路：取数 → 清洗 → 建模 → 出图 → 大屏 → 论文
python run_all.py --skip-data # 已有 data/raw 时跳过下载
```

分步执行（推荐首次）：

```bash
python scripts/01_load.py         # 下载并落盘 9 张表（约 45 MB）
python scripts/01b_aux.py         # 拉取 BCB 宏观序列
python scripts/02_clean.py        # 清洗 → data/clean + SQLite + 治理台账
python scripts/03_analysis_overview.py
python scripts/03_analysis_rfm.py
python scripts/03_analysis_cohort.py
python scripts/03_analysis_bcg.py
python scripts/03_analysis_basket.py
python scripts/03_analysis_forecast.py   # 35 组 SARIMA 网格搜索，约 30 秒
python scripts/03_analysis_funnel.py
python 代码/run_all_figs.py       # 24 张图，约 40 秒
python scripts/05_dashboard.py    # 生成自包含大屏 HTML
python scripts/06_paper.py        # 生成论文 docx（送审版）
python scripts/07_build_equations.py   # 8 条公式转 Word 原生 OMML（需本机 Microsoft Word）
python scripts/06_paper.py --full      # 可选：生成未删减的完整版
```

### 4.3 两个论文版本

同一套版式、同一批图表，正文源不同，互不覆盖：

| 版本 | 文件 | 正文 | 摘要 | 关键词 | 表 | 用途 |
|---|---|---|---|---|---|---|
| **送审版**（默认） | `docs/Olist电商用户价值分层与履约流失预警.docx` | 6,615 汉字 | 291 字符 | 5 个 | 8 张（含字段说明、Python/Excel 对比） | 按作业要求逐条对齐，用于提交 |
| **完整版**（`--full`） | `docs/Olist…_完整版.docx` | 9,222 汉字 | 460 字符 | 6 个 | 6 张 | 保留全部论证细节（阈值敏感性、口径推导、模型取舍的完整推理），用于答辩底稿或扩写 |

两版的差异只在文字取舍：送审版把每个模型的长段论证压成结论句，并把省下的篇幅让给 25 张图的逐图解读；完整版保留原始论证，但不满足"摘要 200–300 字""关键词 3–5 个"等硬性条款。正文源分别是 `scripts/_paper_content.py` 与 `scripts/_paper_content_full.py`。

### 4.4 提交稿与模板文件

按课程提交要求，最终提交稿以模板文件名保存：

| 文件 | 说明 |
|---|---|
| `5、《商业数据分析》 - 期末大作业模板.docx` | **最终提交稿**。已填真实封面信息（大数据 241 班 / 2024459985105 / 范珏维），正文为送审版，并在 Word 中手工调整过排版（去除中英文间空格、改用多级自动编号、摘要在送审版基础上重写） |
| `docs/5、《商业数据分析》 - 期末大作业.pdf` | 上述提交稿的 PDF（28 页） |

注意两点：

1. 根目录的模板文件已被提交稿覆盖，因此 `06_paper.py` **优先读取 `docs/模板备份_期末大作业模板.docx`**（98 KB 空白模板）作为版式母版，只有备份缺失时才回落到根目录文件。这样既保留提交稿，又不影响 `run_all.py` 一键复现。
2. 提交稿与 `docs/` 下的脚本版内容并不完全一致：手工排版时表 3-1（数据治理台账）、表 5-1（Python/Excel 对比）与两段方法说明（模板复现、大屏实现）未保留，图题中的图表类型标注也被删除。若要一份结构与评分要点完全对齐的文档，请用脚本生成的 `docs/Olist电商用户价值分层与履约流失预警.docx`。

### 4.5 随机性说明

- 全项目统一 `random_state = 42`（K-Means 初始化、轮廓系数抽样）。
- **不做抽样**：主表 99,441 行远超课程的 500 行下限，全量使用，抽样偏差为零。
- 唯一的抽样发生在聚类评估：轮廓系数为 O(n²) 距离计算，9.6 万样本不可行，故在 1 万条分层随机子样本上估计（`kmeans_silhouette.csv` 的 `eval_n` 字段有记录）。

---

## 5. 模型清单

| 模型 | 脚本 | 关键参数与依据 | 结果表 |
|---|---|---|---|
| 环比/同比 + 三口径拆解 | `03_analysis_overview.py` | 以 IPCA 定基指数平减、BCB 月均汇率折算 | `monthly_kpi.csv` |
| RFM 八分类 | `03_analysis_rfm.py` | R/M 用中位数（抗偏态）；**F 用 2 单阈值**（F 中位数=1，按中位数会使八分类退化为四分类） | `rfm_segments.csv`、`rfm_threshold_sensitivity.csv` |
| K-Means 分群 | 同上 | log 变换 + 标准化；轮廓系数最优 k=2，**业务取 k=4**（显式取舍） | `kmeans_profile.csv` |
| 同期群留存 | `03_analysis_cohort.py` | 首购月分组；只保留 2017-01–2018-02 的群（≥6 个完整观察月） | `cohort_retention_matrix.csv` |
| 波士顿矩阵 | `03_analysis_bcg.py` | 纵轴用**相对增速**（品类增速 − 平台增速），避免高速扩张期全部落在「高增长」 | `bcg_matrix.csv` |
| 帕累托/ABC | 同上 | 累计 ≤80% 为 A、80–95% 为 B | `pareto_categories.csv` |
| Apriori | `03_analysis_basket.py` | `min_support=0.0005`（由「至少 50 单才可执行」反推） | `basket_rules.csv`、`basket_diagnosis.csv` |
| SARIMA | `03_analysis_forecast.py` | (2,1,2)×(0,1,1,13)；35 组网格 + AIC；留出 8 周回测 | `forecast_weekly.csv`、`forecast_metrics.json` |
| Holt-Winters 对照 | 同上 | 对数 + 阻尼趋势，同一训练/测试集 | `forecast_model_comparison.csv` |
| 履约漏斗 + 延迟归因 | `03_analysis_funnel.py` | 三段时长分解（备货/干线）；logistic 剂量-反应 + 反事实模拟 | `funnel_stages.csv`、`buffer_scenario.csv` |

---

## 6. 图表索引

24 张静态图 + 1 张交互大屏，两张一类：

| 类别 | 编号 | 内容 |
|---|---|---|
| 模板复现（12 种） | 图 5-1 ~ 5-12 | 渐变柱形、带均值柱形、渐变圆角柱形、标注柱形、层叠柱形、蝴蝶图、对比柱形、数值百分比、甘特图、平滑折线、单值圆环、玉玦图 |
| 业务模型（12 张） | 图 5-13 ~ 5-24 | 帕累托、波士顿矩阵、同期群热力图、RFM 气泡、SARIMA 预测、履约漏斗、环比同比、关联规则诊断、剂量反应、反事实曲线、州级四象限、K-Means 评估 |
| 交互大屏 | 图 5-25 | 8 组件、三层联动（州筛选 / 点击条形下钻 / 点击品类下钻） |

完整文件清单与字段说明见 [`docs/图表索引.md`](docs/图表索引.md)。

---

## 7. 大屏

`outputs/dashboard/olist_dashboard.html` —— 单文件 1.1 MB，**ECharts 内联，双击即可离线打开**，无需服务器、无需联网。

- **8 个组件**：6 张 KPI 卡、月度成交与增速、州级 GMV 排名、品类结构树图、履约漏斗、RFM 双环、延迟率与评分双轴、州×品类明细表。
- **联动**：顶部「州」下拉 → KPI/趋势/品类/漏斗/明细全部重算。
- **下钻**：点击州条形 = 切换州；点击品类色块 = 明细表过滤到该品类。
- 明细表支持表头排序，延迟率 >10% 的行自动标记「需关注」。

---

## 8. 主要发现

1. **增长被高估**：名义同比 +137%，实际价 +129.6%，美元口径 +112.4%——汇率吃掉约 25 个百分点。
2. **钱在两个「快要走」的客群**：重要深耕（24.1% 客户 / 38.0% GMV）+ 重要挽留（23.2% / 37.2%）；真正的「重要价值客户」仅 1.5%。
3. **留存不是漏，是不来**：M+1 留存 0.49%，复购间隔中位数 64 天。
4. **品类结构缺压舱石**：明星 4 个（29.9%）、现金牛仅 3 个；A 类 17 个品类贡献 80% GMV。
5. **购物篮不存在**：多品类订单仅 0.8%，Apriori 唯一规则 lift=0.114（<1 即互斥）。
6. **延迟恶化是因为「承诺太快」**：实际时效 10.7→7.0 天（更快），承诺 39→13.4 天（更紧），缓冲 28.3→6.1 天，延迟率 3.07%→10.39%。
7. **责任在干线**：延迟订单比准时订单多耗 18.2 天，其中干线段占 93%。
8. **3 天是红线**：延迟 1–3 天差评率 19%，4–7 天跳到 60%。

---

## 9. 局限

- 缺少营销投放、流量来源、库存等内部数据，无法做严格因果推断（如 DID / 断点回归）。
- 2018-09 之后数据截断，同期群最长观察期 12 个月。
- 大屏为静态数据快照，未接实时库。
- 天池数据源因下载需登录态未采用，辅助源改用 BCB 官方接口。

---

## 10. 学术诚信

所有代码、图表、结论均由本人完成；AI 辅助使用情况已在论文 7.3 节按要求披露（工具、环节、关键提示词示例）。图表全部由 Python 生成，未使用 Power BI / Tableau / FineBI，未以 Excel 截图替代 Python 输出。
