import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =========================
# 0) 路径与画图风格
# =========================
BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "outputs"
FIG_DIR = OUT_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 120
plt.rcParams["savefig.dpi"] = 300

# =========================
# 1) 读取数据
# =========================
global_metrics_path = OUT_DIR / "global_metrics.csv"
segment_mae_path = OUT_DIR / "segment_mae.csv"
period_metrics_path = OUT_DIR / "period_metrics.csv"
pred_next_path = OUT_DIR / "next_step_prediction_all_segments.csv"

for p in [global_metrics_path, segment_mae_path, period_metrics_path, pred_next_path]:
    if not p.exists():
        raise FileNotFoundError(f"缺少结果文件: {p}")

global_metrics = pd.read_csv(global_metrics_path).iloc[0].to_dict()
segment_mae = pd.read_csv(segment_mae_path)
period_metrics = pd.read_csv(period_metrics_path, index_col=0)
pred_next = pd.read_csv(pred_next_path)

# 日志中给出的单路段(路段1)指标
seg0_metrics = {
    "mae": 28.35,
    "rmse": 39.49,
    "mape": 12.42,
    "r2": 0.9180,
}

# =========================
# 图1：整体性能指标
# =========================
fig, ax1 = plt.subplots(figsize=(10, 5))
metric_names = ["MAE", "RMSE", "WAPE", "sMAPE", "MAPE_filtered"]
metric_vals = [float(global_metrics[k]) for k in metric_names]

bars = ax1.bar(metric_names, metric_vals, color=["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2"], alpha=0.9)
ax1.set_ylabel("误差值 / 百分比")
ax1.set_title("图1 CNN-LSTM在PeMS04测试集上的整体性能")
ax1.grid(axis="y", alpha=0.25)

for b, v in zip(bars, metric_vals):
    ax1.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}", ha="center", va="bottom", fontsize=9)

ax2 = ax1.twinx()
ax2.plot([0], [float(global_metrics["R2"])], "o", color="black")
ax2.set_ylim(0, 1.0)
ax2.set_ylabel("R²", color="black")
ax2.text(0.05, float(global_metrics["R2"]), f"R²={float(global_metrics['R2']):.4f}", ha="left", va="bottom", fontsize=9)

plt.tight_layout()
plt.savefig(FIG_DIR / "fig1_global_metrics.png", bbox_inches="tight")
plt.close()

# =========================
# 图2：路段MAE分布（直方图+箱线图）
# =========================
mae_vals = segment_mae["mae"].values
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

axes[0].hist(mae_vals, bins=30, color="#4C78A8", alpha=0.85, edgecolor="white")
axes[0].axvline(mae_vals.mean(), color="red", linestyle="--", label=f"均值={mae_vals.mean():.2f}")
axes[0].axvline(np.median(mae_vals), color="orange", linestyle="--", label=f"中位数={np.median(mae_vals):.2f}")
axes[0].set_xlabel("MAE（辆）")
axes[0].set_ylabel("路段数量")
axes[0].set_title("图2(a) 全路段MAE直方分布")
axes[0].legend()
axes[0].grid(alpha=0.25, axis="y")

axes[1].boxplot(
    mae_vals,
    vert=True,
    patch_artist=True,
    boxprops=dict(facecolor="#72B7B2", alpha=0.7),
    medianprops=dict(color="red"),
)
axes[1].set_ylabel("MAE（辆）")
axes[1].set_title("图2(b) 全路段MAE箱线图")
axes[1].grid(alpha=0.25, axis="y")

plt.tight_layout()
plt.savefig(FIG_DIR / "fig2_segment_mae_distribution.png", bbox_inches="tight")
plt.close()

# =========================
# 图3：分时段性能（MAE柱 + WAPE折线）
# =========================
period_order = [
    "深夜 (0:00-6:00)",
    "早高峰 (7:00-9:00)",
    "上午平峰 (9:00-12:00)",
    "午间 (12:00-14:00)",
    "下午平峰 (14:00-17:00)",
    "晚高峰 (17:00-19:00)",
    "夜间 (19:00-24:00)",
]
period_df = period_metrics.loc[[p for p in period_order if p in period_metrics.index]]

fig, ax1 = plt.subplots(figsize=(12, 5.5))
x = np.arange(len(period_df))
mae = period_df["mae"].astype(float).values
wape = period_df["wape"].astype(float).values

ax1.bar(x, mae, color="#A0CBE8", alpha=0.9, label="MAE")
ax1.set_xticks(x)
ax1.set_xticklabels(period_df.index, rotation=25, ha="right")
ax1.set_ylabel("MAE（辆）", color="blue")
ax1.set_title("图3 不同时段预测性能对比（MAE + WAPE）")
ax1.grid(alpha=0.25, axis="y")

ax2 = ax1.twinx()
ax2.plot(x, wape, color="red", marker="o", linewidth=2, label="WAPE")
ax2.set_ylabel("WAPE（%）", color="red")

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

plt.tight_layout()
plt.savefig(FIG_DIR / "fig3_period_performance.png", bbox_inches="tight")
plt.close()

# =========================
# 图4：下一时间步预测（分布 + Top/Bottom15）
# =========================
pred = pred_next["predicted_flow"].astype(float).values
pred_sorted_desc = pred_next.sort_values("predicted_flow", ascending=False).head(15)
pred_sorted_asc = pred_next.sort_values("predicted_flow", ascending=True).head(15)

fig = plt.figure(figsize=(13, 9))

ax1 = plt.subplot(2, 1, 1)
ax1.hist(pred, bins=30, color="#54A24B", alpha=0.8, edgecolor="white")
ax1.set_title("图4(a) 下一时间步全路段预测流量分布")
ax1.set_xlabel("预测流量（辆）")
ax1.set_ylabel("路段数量")
ax1.grid(alpha=0.25, axis="y")

ax2 = plt.subplot(2, 2, 3)
ax2.barh(pred_sorted_desc["segment_id"].astype(int).astype(str), pred_sorted_desc["predicted_flow"], color="#F58518")
ax2.invert_yaxis()
ax2.set_title("图4(b) 流量最高Top15路段")
ax2.set_xlabel("预测流量（辆）")

ax3 = plt.subplot(2, 2, 4)
ax3.barh(pred_sorted_asc["segment_id"].astype(int).astype(str), pred_sorted_asc["predicted_flow"], color="#E45756")
ax3.invert_yaxis()
ax3.set_title("图4(c) 流量最低Bottom15路段")
ax3.set_xlabel("预测流量（辆）")

plt.tight_layout()
plt.savefig(FIG_DIR / "fig4_next_step_prediction.png", bbox_inches="tight")
plt.close()

# =========================
# 表1：核心结果汇总
# =========================
summary_rows = [
    ["单路段(路段1)", "MAE", seg0_metrics["mae"]],
    ["单路段(路段1)", "RMSE", seg0_metrics["rmse"]],
    ["单路段(路段1)", "MAPE(过滤)%", seg0_metrics["mape"]],
    ["单路段(路段1)", "R²", seg0_metrics["r2"]],
    ["全局(全路段展平)", "MAE", float(global_metrics["MAE"])],
    ["全局(全路段展平)", "RMSE", float(global_metrics["RMSE"])],
    ["全局(全路段展平)", "R²", float(global_metrics["R2"])],
    ["全局(全路段展平)", "WAPE(%)", float(global_metrics["WAPE"])],
    ["全局(全路段展平)", "sMAPE(%)", float(global_metrics["sMAPE"])],
    ["全局(全路段展平)", "MAPE(过滤)%", float(global_metrics["MAPE_filtered"])],
]
summary_df = pd.DataFrame(summary_rows, columns=["评估范围", "指标", "数值"])
summary_df.to_csv(FIG_DIR / "table1_core_metrics.csv", index=False, encoding="utf-8-sig")

print(f"已完成：图表与表格输出到 {FIG_DIR}")
