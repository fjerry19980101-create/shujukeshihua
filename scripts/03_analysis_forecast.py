# -*- coding: utf-8 -*-
"""
03_analysis_forecast.py —— SARIMA 周 GMV 预测（含 95% 置信区间与回测）
====================================================================
为什么用"周"而不是"月"
  Olist 只有 20 个完整月份，月度序列做季节性差分后样本不足（<15 个有效点），
  参数估计不可靠；周序列有 85 个点，且电商的周内节律（周末下单高峰）本身是有效信号。

为什么 s=13
  年度季节性需要 s=52，85 个点无法支撑 52 阶季节项（至少需要 2-3 个完整周期即 104 点以上）。
  这里改用 13 周（约一个季度）作为季节周期——巴西电商的季度性促销
  （3 月返校季、5 月母亲节、11 月黑五）正是以季度为节奏，业务上可解释。

参数选择
  (p,d,q)×(P,D,Q,s) 在 p,q∈{0,1,2}、P,Q∈{0,1} 上网格搜索，取 AIC 最小且收敛的模型；
  d=1（一阶差分去趋势）、D=1（季节差分去季度性）由序列平稳性检验（ADF/KPSS）决定。

回测
  留出最后 8 周做样本外检验，报告 MAPE / RMSE / MASE；再用全量数据重训并外推 12 周。
"""
from __future__ import annotations

import itertools
import json
import warnings

import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller, kpss

from _common import load_orders, save_json, save_table

warnings.filterwarnings("ignore")

S = 13            # 季节周期（周）
HOLDOUT = 8       # 留出 8 周回测
HORIZON = 12      # 外推 12 周


def mape(y: np.ndarray, yhat: np.ndarray) -> float:
    m = y != 0
    return float(np.mean(np.abs((y[m] - yhat[m]) / y[m])) * 100)


def mase(y: np.ndarray, yhat: np.ndarray) -> float:
    """MASE：以"朴素预测"（上一期值）为基准的相对误差，<1 表示优于朴素法。"""
    naive = np.abs(np.diff(y)).mean()
    return float(np.abs(y - yhat).mean() / naive) if naive else np.nan


def build_series() -> pd.Series:
    fo = load_orders(with_window=True)
    s = fo.groupby("purchase_week").gmv.sum().sort_index()
    # 掐掉首尾不完整周（首周仅 1 月 1-5 日的 4 天，末周仅到 8 月 31 日）
    s = s.iloc[1:-1] if len(s) > 10 else s
    s.index = pd.DatetimeIndex(s.index, freq="W-MON")
    return s


def main() -> None:
    y_all = build_series()
    print(f"[forecast] 周序列 {len(y_all)} 期：{y_all.index[0].date()} ~ {y_all.index[-1].date()}")

    # ---------------- 平稳性检验 ----------------
    adf_p = float(adfuller(y_all, autolag="AIC")[1])
    try:
        kpss_p = float(kpss(y_all, nlags="auto")[1])
    except Exception:
        kpss_p = np.nan
    d = 1 if (adf_p > 0.05) else 0
    print(f"[forecast] ADF p={adf_p:.4f}（>0.05 非平稳）-> d={d}")

    train, test = y_all.iloc[:-HOLDOUT], y_all.iloc[-HOLDOUT:]

    # ---------------- 网格搜索（AIC） ----------------
    rows = []
    best = None
    for p, q, P, Q in itertools.product([0, 1, 2], [0, 1, 2], [0, 1], [0, 1]):
        if p == 0 and q == 0 and P == 0 and Q == 0:
            continue
        order = (p, d, q)
        sorder = (P, 1, Q, S)
        try:
            m = SARIMAX(train, order=order, seasonal_order=sorder,
                        enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
            rows.append({"order": str(order), "seasonal_order": str(sorder),
                         "aic": round(float(m.aic), 2), "bic": round(float(m.bic), 2),
                         "converged": bool(m.mle_retvals.get("converged", True))})
            if best is None or m.aic < best[0]:
                best = (m.aic, order, sorder, m)
        except Exception:
            continue
    sel = pd.DataFrame(rows).sort_values("aic").reset_index(drop=True)
    save_table(sel.head(20), "forecast_model_selection.csv")
    _, order, sorder, model_bt = best
    print(f"[forecast] 选定 SARIMA{order}x{sorder}  AIC={best[0]:.1f}")

    # ---------------- 回测 ----------------
    fc = model_bt.get_forecast(steps=HOLDOUT)
    pred = fc.predicted_mean.values
    ci = fc.conf_int(alpha=0.05).values
    y_true = test.values
    metrics = {
        "order": str(order), "seasonal_order": str(sorder),
        "aic": round(float(model_bt.aic), 2),
        "train_weeks": int(len(train)), "test_weeks": int(HOLDOUT),
        "mape_pct": round(mape(y_true, pred), 3),
        "rmse": round(float(np.sqrt(np.mean((y_true - pred) ** 2))), 2),
        "mase": round(mase(y_true, pred), 4),
        "coverage_pct": round(float(np.mean((y_true >= ci[:, 0]) & (y_true <= ci[:, 1])) * 100), 2),
        "adf_p": round(adf_p, 4), "kpss_p": round(kpss_p, 4), "d": d, "period": S,
    }

    # 残差白噪声检验（Ljung-Box）
    lb = acorr_ljungbox(model_bt.resid, lags=[8], return_df=True)
    metrics["ljungbox_p_lag8"] = round(float(lb["lb_pvalue"].iloc[0]), 4)

    bt = pd.DataFrame({
        "week": test.index, "actual": y_true, "pred": pred.round(0),
        "lower95": ci[:, 0].round(0), "upper95": ci[:, 1].round(0),
    })
    save_table(bt, "forecast_backtest.csv")
    save_json(metrics, "forecast_metrics.json")
    print(f"[forecast] 回测 MAPE={metrics['mape_pct']}%  RMSE={metrics['rmse']:,}  "
          f"MASE={metrics['mase']}  95%CI 覆盖率={metrics['coverage_pct']}%  "
          f"LjungBox p={metrics['ljungbox_p_lag6'] if 'ljungbox_p_lag6' in metrics else metrics['ljungbox_p_lag8']}")

    # ---------------- 基准模型对照：Holt-Winters（对数 + 阻尼趋势） ----------------
    # 用同一训练集/测试集，避免"只报一个模型好看的数字"。HW 在对数空间建模，
    # 天然假设波动是乘性的，与电商 GMV 的增长形态更匹配。
    hw_rows = []
    try:
        hw = ExponentialSmoothing(np.log(train), trend="add", damped_trend=True,
                                  seasonal="add", seasonal_periods=S,
                                  initialization_method="estimated").fit()
        hw_pred = np.exp(hw.forecast(HOLDOUT).values)
        hw_resid = np.exp(hw.fittedvalues.values) - train.values
        hw_sigma = float(np.std(hw_resid, ddof=1))
        hw_ci = np.column_stack([hw_pred - 1.96 * hw_sigma, hw_pred + 1.96 * hw_sigma])
        hw_rows.append({
            "model": "Holt-Winters(log, 阻尼)",
            "mape_pct": round(mape(y_true, hw_pred), 3),
            "rmse": round(float(np.sqrt(np.mean((y_true - hw_pred) ** 2))), 2),
            "mase": round(mase(y_true, hw_pred), 4),
            "coverage_pct": round(float(np.mean((y_true >= hw_ci[:, 0]) &
                                                (y_true <= hw_ci[:, 1])) * 100), 2),
        })
    except Exception as e:
        print("[forecast] Holt-Winters 拟合失败：", e)

    cmp_rows = [{
        "model": f"SARIMA{order}x{sorder}",
        "mape_pct": metrics["mape_pct"], "rmse": metrics["rmse"],
        "mase": metrics["mase"], "coverage_pct": metrics["coverage_pct"],
    }] + hw_rows
    save_table(pd.DataFrame(cmp_rows), "forecast_model_comparison.csv")

    # ---------------- 全量重训 + 外推 ----------------
    final = SARIMAX(y_all, order=order, seasonal_order=sorder,
                    enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
    f = final.get_forecast(steps=HORIZON)
    mean = f.predicted_mean
    ci2 = f.conf_int(alpha=0.05)

    hist = pd.DataFrame({"week": y_all.index, "actual": y_all.values,
                         "fitted": final.fittedvalues.values.round(0)})
    hist["pred"] = np.nan
    hist["lower95"] = np.nan
    hist["upper95"] = np.nan
    fut = pd.DataFrame({
        "week": mean.index, "actual": np.nan, "fitted": np.nan,
        "pred": mean.values.round(0),
        "lower95": ci2.iloc[:, 0].values.round(0),
        "upper95": ci2.iloc[:, 1].values.round(0),
    })
    out = pd.concat([hist, fut], ignore_index=True)
    save_table(out, "forecast_weekly.csv")

    # 未来 12 周合计 GMV 区间（论文与商业建议引用）
    total_pt = float(mean.sum())
    total_lo = float(ci2.iloc[:, 0].sum())
    total_hi = float(ci2.iloc[:, 1].sum())
    save_json({
        "horizon_weeks": HORIZON,
        "forecast_start": str(mean.index[0].date()),
        "forecast_end": str(mean.index[-1].date()),
        "total_gmv_point": round(total_pt, 0),
        "total_gmv_lower95": round(total_lo, 0),
        "total_gmv_upper95": round(total_hi, 0),
        "weekly_mean_point": round(float(mean.mean()), 0),
        "aggregate_band_note": ("合计区间由逐周 95% 区间累加得到，属保守包络："
                                "周间预测误差正相关（水平不确定性主导），"
                                "因此真实合计区间通常略窄于此包络，但量级相当"),
    }, "forecast_summary.json")

    print(f"[forecast] 外推 {HORIZON} 周（{mean.index[0].date()}~{mean.index[-1].date()}）："
          f"合计 {total_pt:,.0f} BRL，95%CI [{total_lo:,.0f}, {total_hi:,.0f}]")


if __name__ == "__main__":
    main()
