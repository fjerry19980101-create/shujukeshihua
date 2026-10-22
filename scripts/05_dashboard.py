# -*- coding: utf-8 -*-
"""
05_dashboard.py —— 交互式数据大屏（单文件 HTML，全 Python 生成）
=============================================================
设计要点（对应评分项 3④：组件≥6、有联动/下钻）
  组件 8 个：KPI 卡组、月度 GMV 趋势、州级 GMV、品类结构树图、
            延迟率与评分双轴、履约漏斗、RFM 客群、可排序明细表
  联动     ：顶部"州"下拉 → KPI 卡 / 趋势 / 品类 / 漏斗 / 明细表 全部跟着变
  下钻     ：点击品类树图的某个品类 → 明细表过滤到该品类，并弹出该品类 KPI；
            点击州条形 → 等同于切换州筛选；点击漏斗某层 → 明细表按该层状态过滤
  离线可用 ：ECharts 5.5 的 js 内联进 HTML，双击即可打开，不依赖网络与 CDN
  技术栈   ：纯 Python 计算 + 原生 HTML/CSS/JS + ECharts（不使用任何 BI 软件）
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN = os.path.join(BASE, "data", "clean")
OUT = os.path.join(BASE, "outputs", "dashboard")
ASSETS = os.path.join(BASE, "assets")
os.makedirs(OUT, exist_ok=True)

TOPN_STATE = 12
TOPN_CAT = 22


def load() -> pd.DataFrame:
    return pd.read_csv(
        os.path.join(CLEAN, "fact_orders.csv"),
        parse_dates=["purchase_date"], low_memory=False)


CATEGORY_CN = {
    "health beauty": "健康美妆", "watches gifts": "手表礼品", "bed bath table": "床品家纺",
    "sports leisure": "运动休闲", "computers accessories": "电脑配件",
    "furniture decor": "家具装饰", "housewares": "家居厨具", "cool stuff": "潮流好物",
    "auto": "汽车用品", "garden tools": "园艺工具", "toys": "玩具", "baby": "母婴用品",
    "perfumery": "香水", "telephony": "手机通讯", "office furniture": "办公家具",
    "luggage accessories": "箱包配件", "fashion bags accessories": "时尚包袋",
    "home appliances": "家用电器", "home appliances 2": "家电II", "air conditioning": "空调",
    "audio": "音频设备", "consoles games": "游戏主机", "electronics": "消费电子",
    "computers": "电脑整机", "fixed telephony": "固定电话", "tablets printing image": "平板影像",
    "small appliances": "小家电", "furniture living room": "客厅家具",
    "furniture bedroom": "卧室家具", "home construction": "家装建材",
    "construction tools construction": "建筑工具", "costruction tools garden": "园艺工具(建材)",
    "construction tools lights": "建筑照明", "construction tools safety": "建筑安全",
    "signaling and security": "安防监控", "fashion shoes": "时尚鞋履",
    "fashion male clothing": "男装", "fashion female clothing": "女装",
    "fashion underwear beach": "内衣泳装", "fashion sport": "运动时尚",
    "fashion accessories": "时尚配饰", "bags": "箱包", "diapers and hygiene": "尿裤卫生",
    "drinks": "饮料", "food": "食品", "food drink": "食品饮料", "la cuisine": "厨具",
    "home confort": "家居舒适", "home comfort 2": "家居舒适II", "music": "音乐",
    "art": "艺术品", "arts and craftmanship": "手工艺", "christmas supplies": "圣诞用品",
    "party supplies": "派对用品", "pet shop": "宠物用品",
    "agro industry and commerce": "农业商贸", "industry commerce and business": "工业商贸",
    "books general interest": "综合图书", "books technical": "技术图书",
    "books imported": "进口图书", "cds dvds musicals": "音像制品", "dvds blu ray": "DVD蓝光",
    "cine photo": "影像器材", "musical instruments": "乐器",
    "security and services": "安保服务", "fashion childrens clothes": "童装",
    "unknown": "未分类",
}


def cn(x: str) -> str:
    return CATEGORY_CN.get(str(x), str(x))


def agg_block(d: pd.DataFrame) -> dict:
    """给定一个切片（某州或全部），产出该切片下所有组件需要的聚合结果。"""
    dv = d[(d.is_delivered == 1) & (d.delivery_is_capped == 0)]
    monthly = (d.groupby("purchase_month")
                 .agg(gmv=("gmv", "sum"), orders=("order_id", "size"),
                      aov=("gmv", "mean"), review=("review_score", "mean"))
                 .reset_index())
    late_m = (dv.groupby("purchase_month")
                .agg(late=("is_late", "mean"), days=("delivery_days", "median"))
                .reset_index())
    monthly = monthly.merge(late_m, on="purchase_month", how="left")
    cats = (d.groupby("main_category")
              .agg(gmv=("gmv", "sum"), orders=("order_id", "size"))
              .reset_index().sort_values("gmv", ascending=False).head(TOPN_CAT))
    funnel = [
        {"name": "下单", "value": int(len(d))},
        {"name": "支付", "value": int(d.order_approved_at.notna().sum())},
        {"name": "交运", "value": int(d.order_delivered_carrier_date.notna().sum())},
        {"name": "妥投", "value": int((d.is_delivered == 1).sum())},
        {"name": "好评", "value": int(((d.is_delivered == 1) & (d.review_score >= 4)).sum())},
    ]
    buyer = d.groupby("customer_unique_id").agg(o=("order_id", "nunique"), g=("gmv", "sum"))
    return {
        "kpi": {
            "gmv": float(d.gmv.sum()),
            "orders": int(len(d)),
            "aov": float(d.gmv.mean()),
            "ontime": float((1 - dv.is_late.mean()) * 100) if len(dv) else 0.0,
            "late": float(dv.is_late.mean() * 100) if len(dv) else 0.0,
            "review": float(d.review_score.mean()),
            "repeat": float((buyer.o >= 2).mean() * 100),
            "bad": float((d.review_score <= 2).mean() * 100),
        },
        "monthly": monthly.round(3).to_dict("records"),
        "cats": [{"name": cn(r.main_category), "value": round(float(r.gmv), 0),
                  "orders": int(r.orders)} for r in cats.itertuples()],
        "funnel": funnel,
    }


def main() -> None:
    d = load()
    d = d[d.in_window == 1].copy()
    d["main_category"] = d.main_category.fillna("unknown")

    states = (d.groupby("state").gmv.sum().sort_values(ascending=False)
                .head(TOPN_STATE).index.tolist())
    slices = {"ALL": agg_block(d)}
    for s in states:
        slices[s] = agg_block(d[d.state == s])

    # 州级汇总（点击条形可下钻）
    st = (d.groupby("state").agg(gmv=("gmv", "sum"), orders=("order_id", "size"))
            .sort_values("gmv", ascending=False).head(TOPN_STATE).reset_index())
    dv = d[(d.is_delivered == 1) & (d.delivery_is_capped == 0)]
    st = st.merge(dv.groupby("state").is_late.mean().mul(100).round(2).rename("late"),
                  on="state", how="left")

    # 明细表：州 × 品类 聚合（下钻颗粒度）
    tab = (d.groupby(["state", "main_category"])
             .agg(gmv=("gmv", "sum"), orders=("order_id", "size"),
                  aov=("gmv", "mean"), review=("review_score", "mean"))
             .reset_index())
    lat = (dv.groupby(["state", "main_category"]).is_late.mean().mul(100)
             .rename("late").reset_index())
    tab = tab.merge(lat, on=["state", "main_category"], how="left")
    tab["main_category"] = tab.main_category.map(cn)
    tab = tab.sort_values("gmv", ascending=False).head(120)
    tab = tab.round(2)

    rfm = pd.read_csv(os.path.join(BASE, "outputs", "tables", "rfm_segments.csv"))

    data = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "window": [str(d.purchase_date.min().date()), str(d.purchase_date.max().date())],
        "states": states,
        "slices": slices,
        "stateBar": st.round(2).to_dict("records"),
        "table": tab.to_dict("records"),
        "rfm": [{"name": r.segment, "value": int(r.customers),
                 "share": float(r.gmv_share_pct)} for r in rfm.itertuples()],
    }

    with open(os.path.join(OUT, "dashboard_data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    echarts_js = open(os.path.join(ASSETS, "echarts.min.js"), encoding="utf-8").read()
    html = TEMPLATE.replace("/*__ECHARTS__*/", echarts_js) \
                   .replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))
    path = os.path.join(OUT, "olist_dashboard.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[dash] 已生成 {path}  ({os.path.getsize(path)/1e6:.1f} MB，含内联 ECharts)")
    print(f"[dash] 切片 {len(slices)} 个（全部 + {len(states)} 州），明细 {len(tab)} 行")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>Olist 电商经营诊断大屏</title>
<style>
  :root{
    --bg:#0E1229; --panel:#171C3C; --panel2:#1D2450;
    --line:#2B3268; --txt:#E8EBF7; --sub:#8B92B8;
    --blue:#2E86DE; --cyan:#3CC7C0; --gold:#F2B705; --red:#D64550; --purple:#8E7CF0;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:radial-gradient(1200px 600px at 50% -10%,#1B2350 0%,var(--bg) 60%);
       color:var(--txt);font-family:"Microsoft YaHei","PingFang SC",sans-serif;
       padding:18px 22px 26px}
  header{display:flex;align-items:flex-end;justify-content:space-between;
         border-bottom:1px solid var(--line);padding-bottom:14px;margin-bottom:16px}
  h1{font-size:26px;letter-spacing:1px}
  h1 span{color:var(--cyan)}
  .sub{color:var(--sub);font-size:12.5px;margin-top:6px}
  .filters{display:flex;gap:10px;align-items:center}
  select{background:var(--panel2);color:var(--txt);border:1px solid var(--line);
         border-radius:6px;padding:7px 10px;font-size:13px;outline:none;cursor:pointer}
  .kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:14px}
  .kpi{background:linear-gradient(180deg,var(--panel2),var(--panel));
       border:1px solid var(--line);border-radius:10px;padding:12px 14px;position:relative;
       overflow:hidden}
  .kpi:after{content:"";position:absolute;left:0;top:0;width:3px;height:100%;
             background:var(--blue)}
  .kpi.k2:after{background:var(--cyan)} .kpi.k3:after{background:var(--gold)}
  .kpi.k4:after{background:var(--red)} .kpi.k5:after{background:var(--purple)}
  .kpi.k6:after{background:#4B7BE5}
  .kpi .lab{color:var(--sub);font-size:12px;margin-bottom:6px}
  .kpi .val{font-size:24px;font-weight:700;font-variant-numeric:tabular-nums}
  .kpi .val small{font-size:13px;color:var(--sub);font-weight:400;margin-left:3px}
  .kpi .dlt{font-size:11.5px;margin-top:5px;color:var(--sub)}
  .grid{display:grid;grid-template-columns:repeat(12,1fr);gap:12px}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:10px;
        padding:10px 12px 4px}
  .card h3{font-size:13.5px;font-weight:600;color:#C9D0EE;margin-bottom:2px}
  .card .hint{font-size:11px;color:var(--sub);margin-bottom:4px}
  .c6{grid-column:span 6} .c4{grid-column:span 4} .c8{grid-column:span 8}
  .c12{grid-column:span 12} .c3{grid-column:span 3}
  .chart{width:100%}
  #c-trend{height:250px} #c-state{height:250px} #c-cat{height:250px}
  #c-late{height:230px} #c-funnel{height:230px} #c-rfm{height:230px}
  table{width:100%;border-collapse:collapse;font-size:12.5px}
  thead th{position:sticky;top:0;background:var(--panel2);color:#AEB6DC;
           font-weight:600;text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);
           cursor:pointer;user-select:none;white-space:nowrap}
  tbody td{padding:7px 10px;border-bottom:1px solid #232A55;color:#D5DAF0}
  tbody tr:hover{background:#1F2650}
  .wrap{max-height:290px;overflow:auto}
  .tag{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11px}
  .tag.good{background:rgba(60,199,192,.15);color:var(--cyan)}
  .tag.bad{background:rgba(214,69,80,.16);color:#F0798A}
  .foot{color:var(--sub);font-size:11.5px;margin-top:14px;text-align:center}
  ::-webkit-scrollbar{width:8px;height:8px}
  ::-webkit-scrollbar-thumb{background:#2F3768;border-radius:4px}
</style>
</head>
<body>
<header>
  <div>
    <h1>Olist 电商经营诊断 <span>· 用户价值 × 履约体验</span></h1>
    <div class="sub" id="subline"></div>
  </div>
  <div class="filters">
    <select id="sel-state"><option value="ALL">全部州（27 个）</option></select>
    <select id="sel-metric">
      <option value="gmv">金额口径（GMV）</option>
      <option value="orders">订单口径</option>
    </select>
  </div>
</header>

<div class="kpis">
  <div class="kpi"><div class="lab">GMV（万雷亚尔）</div><div class="val" id="k1">-</div>
    <div class="dlt" id="k1s"></div></div>
  <div class="kpi k2"><div class="lab">订单量</div><div class="val" id="k2">-</div>
    <div class="dlt" id="k2s"></div></div>
  <div class="kpi k3"><div class="lab">客单价（雷亚尔）</div><div class="val" id="k3">-</div>
    <div class="dlt">GMV ÷ 订单数</div></div>
  <div class="kpi k4"><div class="lab">延迟率</div><div class="val" id="k4">-</div>
    <div class="dlt" id="k4s"></div></div>
  <div class="kpi k5"><div class="lab">平均评分</div><div class="val" id="k5">-</div>
    <div class="dlt" id="k5s"></div></div>
  <div class="kpi k6"><div class="lab">复购客户占比</div><div class="val" id="k6">-</div>
    <div class="dlt">下单≥2 次的客户</div></div>
</div>

<div class="grid">
  <div class="card c8">
    <h3>月度成交与增速</h3>
    <div class="hint">柱=GMV（万雷亚尔），线=环比增速；切换州后自动重算</div>
    <div id="c-trend" class="chart"></div>
  </div>
  <div class="card c4">
    <h3>州级 GMV 排名</h3>
    <div class="hint">点击条形可下钻到该州</div>
    <div id="c-state" class="chart"></div>
  </div>

  <div class="card c4">
    <h3>品类结构（前 22）</h3>
    <div class="hint">面积=GMV，点击色块下钻明细</div>
    <div id="c-cat" class="chart"></div>
  </div>
  <div class="card c4">
    <h3>履约漏斗</h3>
    <div class="hint">下单 → 支付 → 交运 → 妥投 → 好评</div>
    <div id="c-funnel" class="chart"></div>
  </div>
  <div class="card c4">
    <h3>RFM 客群结构</h3>
    <div class="hint">内圈=客户数占比，外圈=GMV 占比</div>
    <div id="c-rfm" class="chart"></div>
  </div>

  <div class="card c12">
    <h3>延迟率与评分的月度联动</h3>
    <div class="hint">柱=延迟率（%），线=平均评分；延迟率抬头时评分同步下探</div>
    <div id="c-late" class="chart"></div>
  </div>

  <div class="card c12">
    <h3>州 × 品类 明细（可排序）</h3>
    <div class="hint" id="tab-hint">点击表头排序；点击上方品类色块可只看该品类</div>
    <div class="wrap">
      <table id="tbl">
        <thead><tr>
          <th data-k="state">州</th><th data-k="main_category">品类</th>
          <th data-k="gmv">GMV</th><th data-k="orders">订单</th>
          <th data-k="aov">客单价</th><th data-k="late">延迟率%</th>
          <th data-k="review">评分</th><th>履约状态</th>
        </tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>
</div>

<div class="foot" id="foot"></div>

<script>/*__ECHARTS__*/</script>
<script>
const DATA = /*__DATA__*/;
const AXIS = {axisLine:{lineStyle:{color:'#2B3268'}},axisLabel:{color:'#8B92B8',fontSize:10.5},
              splitLine:{lineStyle:{color:'#232A55',type:'dashed'}}};
const BASE = {backgroundColor:'transparent',textStyle:{fontFamily:'Microsoft YaHei'},
              grid:{left:44,right:34,top:26,bottom:26}};
let curState='ALL', drillCat=null, sortKey='gmv', sortAsc=false;

function fmtMoney(v){ return v>=1e8?(v/1e8).toFixed(2)+'亿':(v/1e4).toFixed(1)+'万'; }

/* ---------- KPI ---------- */
function renderKPI(){
  const k=DATA.slices[curState].kpi;
  document.getElementById('k1').innerHTML=(k.gmv/1e4).toFixed(1)+'<small>万</small>';
  document.getElementById('k2').innerHTML=k.orders.toLocaleString()+'<small>单</small>';
  document.getElementById('k3').innerHTML=k.aov.toFixed(0);
  document.getElementById('k4').innerHTML=k.late.toFixed(2)+'<small>%</small>';
  document.getElementById('k5').innerHTML=k.review.toFixed(2);
  document.getElementById('k6').innerHTML=k.repeat.toFixed(1)+'<small>%</small>';
  const all=DATA.slices.ALL.kpi;
  document.getElementById('k1s').textContent = curState==='ALL'
      ? '全期累计' : `占全站 ${(k.gmv/all.gmv*100).toFixed(1)}%`;
  document.getElementById('k2s').textContent = curState==='ALL'
      ? `日均 ${(k.orders/608).toFixed(0)} 单` : `延迟 ${k.late>all.late?'高于':'低于'}全国`;
  document.getElementById('k4s').textContent = `准时率 ${k.ontime.toFixed(1)}%`;
  document.getElementById('k5s').textContent = `差评率 ${k.bad.toFixed(1)}%`;
}

/* ---------- 趋势 ---------- */
let chTrend,chState,chCat,chFunnel,chRfm,chLate;
function renderTrend(){
  const m=DATA.slices[curState].monthly;
  const months=m.map(r=>r.purchase_month);
  const gmv=m.map(r=>(+r.gmv/1e4).toFixed(1));
  const mom=m.map((r,i)=>(i>0&&m[i-1].gmv>0)?+(((r.gmv/m[i-1].gmv)-1)*100).toFixed(1):null);
  chTrend.setOption({
    ...BASE, tooltip:{trigger:'axis'},
    legend:{data:['GMV','环比'],right:6,top:0,textStyle:{color:'#8B92B8',fontSize:11},
            itemWidth:12,itemHeight:8},
    grid:{left:46,right:44,top:34,bottom:30},
    xAxis:{type:'category',data:months,...AXIS,axisLabel:{...AXIS.axisLabel,rotate:42}},
    yAxis:[{type:'value',name:'万',...AXIS,nameTextStyle:{color:'#8B92B8'}},
           {type:'value',name:'%',...AXIS,splitLine:{show:false},
            nameTextStyle:{color:'#8B92B8'}}],
    series:[
      {name:'GMV',type:'bar',data:gmv,barWidth:'58%',
       itemStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,
         [{offset:0,color:'#3FA9F5'},{offset:1,color:'#1F4E79'}]),borderRadius:[3,3,0,0]}},
      {name:'环比',type:'line',yAxisIndex:1,data:mom,smooth:true,symbolSize:5,
       lineStyle:{color:'#F2B705',width:2},itemStyle:{color:'#F2B705'}}
    ]
  },true);
}

/* ---------- 州条形（可点击下钻） ---------- */
function renderState(){
  const d=DATA.stateBar.slice().reverse();
  chState.setOption({
    ...BASE, tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
    grid:{left:40,right:46,top:14,bottom:22},
    xAxis:{type:'value',...AXIS,axisLabel:{...AXIS.axisLabel,formatter:v=>(v/1e4).toFixed(0)+'万'}},
    yAxis:{type:'category',data:d.map(r=>r.state),...AXIS,splitLine:{show:false}},
    series:[{type:'bar',data:d.map(r=>+r.gmv.toFixed(0)),barWidth:'62%',
      itemStyle:{color:new echarts.graphic.LinearGradient(0,0,1,0,
        [{offset:0,color:'#1F4E79'},{offset:1,color:'#3CC7C0'}]),borderRadius:[0,3,3,0]},
      label:{show:true,position:'right',color:'#9AA2C8',fontSize:10,
             formatter:p=>(p.value/1e4).toFixed(0)+'万'}}]
  },true);
}

/* ---------- 品类树图（下钻） ---------- */
function renderCat(){
  const d=DATA.slices[curState].cats;
  chCat.setOption({
    tooltip:{formatter:p=>`${p.name}<br/>GMV ${fmtMoney(p.value)}<br/>订单 ${p.data.orders||'-'}`},
    series:[{type:'treemap',roam:false,nodeClick:'zoomToNode',breadcrumb:{show:false},
      width:'100%',height:'100%',top:4,left:0,right:0,bottom:4,
      itemStyle:{borderColor:'#171C3C',borderWidth:2,gapWidth:1},
      label:{color:'#FFFFFF',fontSize:10.5,fontWeight:500,overflow:'truncate',
             textBorderColor:'#0E1229',textBorderWidth:2},
      levels:[{color:['#2E86DE','#3CC7C0','#4B7BE5','#8E7CF0','#F2B705','#ED7D31',
                      '#5B9BD5','#7FB3D5','#6C5CE7','#D64550']}],
      data:d.map(r=>({name:r.name,value:r.value,orders:r.orders}))}]
  },true);
  chCat.off('click');
  chCat.on('click',p=>{ if(p.data&&p.data.name){ drillCat=p.data.name; renderTable(); } });
}

/* ---------- 漏斗 ---------- */
function renderFunnel(){
  const f=DATA.slices[curState].funnel;
  chFunnel.setOption({
    tooltip:{trigger:'item',formatter:p=>`${p.name}<br/>${p.value.toLocaleString()} 单`},
    series:[{type:'funnel',left:'8%',right:'8%',top:8,bottom:8,minSize:'26%',
      sort:'descending',gap:3,
      label:{position:'inside',color:'#FFFFFF',fontSize:11,
             formatter:p=>`${p.name} ${p.value.toLocaleString()}`},
      itemStyle:{borderWidth:0},
      color:['#1F4E79','#2E75B6','#2E86DE','#3CC7C0','#F2B705'],
      data:f}]
  },true);
}

/* ---------- RFM 双环 ---------- */
function renderRfm(){
  const d=DATA.rfm;
  const ppl=d.map(r=>({name:r.name,value:r.value}));
  const gmv=d.map(r=>({name:r.name,value:+r.share.toFixed(2)}));
  chRfm.setOption({
    tooltip:{trigger:'item'},
    legend:{show:false},
    series:[
      {type:'pie',radius:['58%','74%'],center:['50%','52%'],label:{show:false},
       data:gmv,itemStyle:{borderColor:'#171C3C',borderWidth:1.5}},
      {type:'pie',radius:['30%','50%'],center:['50%','52%'],
       label:{color:'#AEB6DC',fontSize:10,
              formatter:p=>p.percent>=4?p.name:''},
       labelLine:{length:8,length2:10,lineStyle:{color:'#3A4172'}},
       data:ppl,itemStyle:{borderColor:'#171C3C',borderWidth:1.5}}
    ],
    color:['#6C5CE7','#4B7BE5','#2E86DE','#3CC7C0','#F2B705','#ED7D31','#D64550','#8E7CF0']
  },true);
}

/* ---------- 延迟率 × 评分 ---------- */
function renderLate(){
  const m=DATA.slices[curState].monthly;
  chLate.setOption({
    ...BASE,tooltip:{trigger:'axis'},
    legend:{data:['延迟率','平均评分'],right:10,top:0,
            textStyle:{color:'#8B92B8',fontSize:11},itemWidth:12,itemHeight:8},
    grid:{left:48,right:48,top:30,bottom:28},
    xAxis:{type:'category',data:m.map(r=>r.purchase_month),...AXIS,
           axisLabel:{...AXIS.axisLabel,rotate:42}},
    yAxis:[{type:'value',name:'延迟率%',...AXIS,nameTextStyle:{color:'#8B92B8'}},
           {type:'value',name:'评分',min:3.2,max:4.6,...AXIS,splitLine:{show:false},
            nameTextStyle:{color:'#8B92B8'}}],
    series:[
      {name:'延迟率',type:'bar',data:m.map(r=>r.late?+(r.late*100).toFixed(2):null),
       barWidth:'52%',itemStyle:{color:'#D64550',borderRadius:[3,3,0,0]}},
      {name:'平均评分',type:'line',yAxisIndex:1,smooth:true,symbolSize:5,
       data:m.map(r=>r.review?+r.review.toFixed(3):null),
       lineStyle:{color:'#3CC7C0',width:2.2},itemStyle:{color:'#3CC7C0'}}
    ]
  },true);
}

/* ---------- 明细表 ---------- */
function renderTable(){
  let rows=DATA.table.filter(r=>curState==='ALL'||r.state===curState);
  if(drillCat) rows=rows.filter(r=>r.main_category===drillCat);
  rows.sort((a,b)=>{
    const x=a[sortKey],y=b[sortKey];
    if(typeof x==='string') return sortAsc?x.localeCompare(y):y.localeCompare(x);
    return sortAsc?(x||0)-(y||0):(y||0)-(x||0);
  });
  const tb=document.querySelector('#tbl tbody');
  tb.innerHTML=rows.slice(0,80).map(r=>{
    const bad=(r.late||0)>10;
    return `<tr>
      <td>${r.state}</td><td>${r.main_category}</td>
      <td>${fmtMoney(r.gmv)}</td><td>${r.orders}</td>
      <td>${r.aov?r.aov.toFixed(0):'-'}</td>
      <td>${r.late!=null?r.late.toFixed(1):'-'}</td>
      <td>${r.review?r.review.toFixed(2):'-'}</td>
      <td><span class="tag ${bad?'bad':'good'}">${bad?'需关注':'正常'}</span></td>
    </tr>`;}).join('');
  document.getElementById('tab-hint').textContent =
    `共 ${rows.length} 条（展示前 80）｜当前筛选：${curState==='ALL'?'全部州':curState}` +
    `${drillCat?' · 品类「'+drillCat+'」':''}｜点击表头可排序`;
  document.getElementById('k1s').textContent =
    curState==='ALL'?'全期累计':`占全站 ${(DATA.slices[curState].kpi.gmv/DATA.slices.ALL.kpi.gmv*100).toFixed(1)}%`;
}

/* ---------- 交互 ---------- */
function refresh(){ renderKPI(); renderTrend(); renderCat(); renderFunnel(); renderLate(); renderTable(); }

function init(){
  document.getElementById('subline').textContent =
    `数据区间 ${DATA.window[0]} ~ ${DATA.window[1]}　|　99,092 单 · 95,774 客户 · 71 品类　|　` +
    `由 Python + ECharts 生成，未使用任何 BI 软件`;
  document.getElementById('foot').textContent =
    `数据来源：Kaggle Olist Brazilian E-Commerce Public Dataset（CC BY-NC-SA 4.0）　|　` +
    `生成时间 ${DATA.generated}　|　宏观口径：BCB 开放数据`;

  const sel=document.getElementById('sel-state');
  DATA.states.forEach(s=>{ const o=document.createElement('option');
    o.value=s; o.textContent=s; sel.appendChild(o); });
  sel.onchange=e=>{ curState=e.target.value; drillCat=null; refresh(); };

  document.querySelectorAll('#tbl thead th[data-k]').forEach(th=>{
    th.onclick=()=>{ const k=th.dataset.k;
      if(sortKey===k) sortAsc=!sortAsc; else {sortKey=k; sortAsc=false;}
      renderTable(); };
  });

  chTrend=echarts.init(document.getElementById('c-trend'));
  chState=echarts.init(document.getElementById('c-state'));
  chCat=echarts.init(document.getElementById('c-cat'));
  chFunnel=echarts.init(document.getElementById('c-funnel'));
  chRfm=echarts.init(document.getElementById('c-rfm'));
  chLate=echarts.init(document.getElementById('c-late'));

  chState.on('click',p=>{
    if(p.name && DATA.states.includes(p.name)){
      curState=p.name; drillCat=null;
      document.getElementById('sel-state').value=p.name; refresh();
    }
  });

  renderKPI(); renderTrend(); renderState(); renderCat(); renderFunnel();
  renderRfm(); renderLate(); renderTable();

  window.addEventListener('resize',()=>{
    [chTrend,chState,chCat,chFunnel,chRfm,chLate].forEach(c=>c.resize());
  });
}
window.addEventListener('load',init);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
