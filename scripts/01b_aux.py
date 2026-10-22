# -*- coding: utf-8 -*-
"""
01b_aux.py —— 辅助数据源：巴西央行（BCB）开放数据 API
=====================================================
为什么需要它
------------
Olist 的 GMV 是"名义雷亚尔"。2017-2018 巴西经历高利率下行 + 通胀 + 雷亚尔贬值，
只看名义 GMV 会把"通胀/汇率"误读成"增长"。引入 IPCA（通胀）、Selic（基准利率）、
USD/BRL（汇率）三条月度序列后，可把 GMV 拆成"实际增长"与"价格效应"，这是本项目的
批判性分析支点。

数据源合规
----------
机构 : Banco Central do Brasil（巴西中央银行）
接口 : https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados?formato=json
性质 : 官方开放数据 API（SGS 时序库），无需登录、无需密钥，属课程附件 A 白名单
       第 3 类"政府/国际组织开放平台的公开数据文件下载"
许可 : BCB 开放数据，可自由使用与再分发，须注明来源
序列 : 433  = IPCA 月度环比（%）
       4189 = Selic 月度累计（%）
       3695 = USD/BRL 月均汇率（雷亚尔/美元）

产物
----
data/raw_aux/bcb/*.json            原始响应（原样留存，可追溯）
data/raw_aux/bcb_macro_monthly.csv 月度宏观宽表
"""
from __future__ import annotations

import datetime as dt
import json
import os
import urllib.request

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUX = os.path.join(BASE, "data", "raw_aux")
os.makedirs(os.path.join(AUX, "bcb"), exist_ok=True)

SERIES = {
    433: ("ipca_pct", "IPCA 月度环比（%）"),
    4189: ("selic_pct", "Selic 月度累计（%）"),
    3695: ("usdbrl", "USD/BRL 月均汇率"),
}
START, END = "01/09/2016", "31/12/2018"   # 覆盖订单全量区间，避免首年口径缺失
URL = ("https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"
       "?formato=json&dataInicial={s}&dataFinal={e}")


def fetch(code: int) -> list[dict]:
    url = URL.format(code=code, s=START, e=END)
    req = urllib.request.Request(url, headers={"User-Agent": "olist-coursework/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8")
    with open(os.path.join(AUX, "bcb", f"sgs_{code}.json"), "w", encoding="utf-8") as f:
        f.write(raw)
    return json.loads(raw)


def main() -> None:
    frames = []
    for code, (name, desc) in SERIES.items():
        data = fetch(code)
        s = pd.DataFrame(data)
        s["month"] = pd.to_datetime(s["data"], format="%d/%m/%Y").dt.to_period("M").astype(str)
        s[name] = pd.to_numeric(s["valor"], errors="coerce")
        frames.append(s[["month", name]])
        print(f"[aux] SGS {code:<5} {desc:<22} {len(s)} 期")

    macro = frames[0]
    for f in frames[1:]:
        macro = macro.merge(f, on="month", how="outer")
    macro = macro.sort_values("month").reset_index(drop=True)

    # IPCA 环比 -> 定基指数（以 2018-08 为 100，与趋势观察窗末端对齐）
    macro["ipca_index"] = (1 + macro["ipca_pct"] / 100).cumprod()
    base_month = "2018-08"
    base_idx = float(macro.loc[macro.month == base_month, "ipca_index"].iloc[0])
    macro["ipca_index_201808"] = macro["ipca_index"] / base_idx * 100
    macro["deflator"] = macro["ipca_index_201808"] / 100          # 名义 -> 2018-08 不变价

    macro.to_csv(os.path.join(AUX, "bcb_macro_monthly.csv"), index=False, encoding="utf-8-sig")

    man = {
        "source": "Banco Central do Brasil - SGS",
        "api": "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados",
        "license": "BCB 开放数据（可自由使用，须注明来源）",
        "fetched_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "series": {str(k): v[1] for k, v in SERIES.items()},
        "rows": int(len(macro)),
    }
    with open(os.path.join(AUX, "_aux_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=2)

    print(f"[aux] 宏观表 {len(macro)} 期 -> {os.path.join(AUX, 'bcb_macro_monthly.csv')}")
    print(macro.tail(6).to_string(index=False))


if __name__ == "__main__":
    main()
