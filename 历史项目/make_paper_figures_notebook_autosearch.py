import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ================================
# 1) 基础配置
# ================================
plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 120
plt.rcParams["savefig.dpi"] = 300

required_files = [
    "global_metrics.csv",
    "segment_mae.csv",
    "period_metrics.csv",
    "next_step_prediction_all_segments.csv",
]

# 可按需增加搜索根目录
search_roots = [
    Path.cwd(),
    Path("/home/anan/代码数据"),
    Path("/home/anan"),
    Path.home(),
]

# ================================
# 2) 自动搜索包含全部CSV的目录
# ================================
def find_candidate_dirs(roots, target="global_metrics.csv"):
    candidates = []
    for root in roots:
        if root.exists():
            for p in root.rglob(target):
                candidates.append(p.parent)
    return candidates

candidate_dirs = find_candidate_dirs(search_roots)
valid_dirs = []

for d in candidate_dirs:
    if all((d / f).exists() for f in required_files):
        valid_dirs.append(d.resolve())

# 去重
valid_dirs = list(dict.fromkeys(valid_dirs))

if not valid_dirs:
    raise FileNotFoundError(
        "未找到包含4个CSV的目录，请确认已生成：\n"
        "- global_metrics.csv\n"
        "- segment_mae.csv\n"
        "- period_metrics.csv\n"
        "- next_step_prediction_all_segments.csv"
    )

# 默认使用第一个匹配目录（通常就是最新实验目录）
OUT_DIR = valid_dirs[0]
FIG_DIR = OUT_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

print("已找到CSV目录：", OUT_DIR)
print("图表输出目录：", FIG_DIR)

# ================================
# 3) 读取CSV
# ================================
global_metrics = pd.read_csv(OUT_DIR / "global_metrics.csv").iloc[0].to_dict()
segment_mae = pd.read_csv(OUT_DIR / "segment_mae.csv")
period_metrics = pd.read_csv(OUT_DIR / "period_metrics.csv", index_col=0)
pred_next = pd.read_csv(OUT_DIR / "next_step_prediction_all_segments.csv")

# 若你有最新的路段1指标可改这里
seg0_metrics = {
    "mae": 28.35,
    "rmse": 39.49,
    "mape": 12.42,
    "r2": 0.9180
}

# ================================
# 图1：整体性能指标
# ================================
fig, ax1 = plt.subplots(figsize=(10, 5))
metric_names = ["MAE", "RMSE", "WAPE", "sMAPE", "MAPE_filtered"]
metric_vals = [float(global_metrics[k]) for k in metric_names]

bars = ax1.bar(metric_names, metric_vals,
               color=["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2"], alpha=0.9)
ax1.set_ylabel("误差值 / 百分比")
ax1.set_title("图1 CNN-LSTM在PeMS04测试集上的整体性能")
ax1.grid(axis="y", alpha=0.25)

for b, v in zip(bars, metric_vals):
    ax1.text(b.get_x() + b.get_width()/2, v, f"{v:.2f}", ha="center", va="bottom", fontsize=9)

ax2 = ax1.twinx()
ax2.plot([0], [float(global_metrics["R2"])], "o", color="black")
ax2.set_ylim(0, 1.0)
ax2.set_ylabel("R²", color="black")
ax2.text(0.05, float(global_metrics["R2"]),
         f"R²={float(global_metrics['R2']):.4f}", ha="left", va="bottom", fontsize=9)

plt.tight_layout()
fig1_path = FIG_DIR / "fig1_global_metrics.png"
plt.savefig(fig1_path, bbox_inches="tight")
plt.show()
plt.close()

# ================================
# 图2：路段MAE分布（直方图+箱线图）
# ================================
mae_vals = segment_mae["mae"].astype(float).values
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

axes[0].hist(mae_vals, bins=30, color="#4C78A8", alpha=0.85, edgecolor="white")
axes[0].axvline(mae_vals.mean(), color="red", linestyle="--", label=f"均值={mae_vals.mean():.2f}")
axes[0].axvline(np.median(mae_vals), color="orange", linestyle="--", label=f"中位数={np.median(mae_vals):.2f}")
axes[0].set_xlabel("MAE（辆）")
axes[0].set_ylabel("路段数量")
axes[0].set_title("图2(a) 全路段MAE直方分布")
axes[0].legend()
axes[0].grid(alpha=0.25, axis="y")

axes[1].boxplot(mae_vals, vert=True, patch_artist=True,
                boxprops=dict(facecolor="#72B7B2", alpha=0.7),
                medianprops=dict(color="red"))
axes[1].set_ylabel("MAE（辆）")
axes[1].set_title("图2(b) 全路段MAE箱线图")
axes[1].grid(alpha=0.25, axis="y")

plt.tight_layout()
fig2_path = FIG_DIR / "fig2_segment_mae_distribution.png"
plt.savefig(fig2_path, bbox_inches="tight")
plt.show()
plt.close()

# ================================
# 图3：分时段性能（MAE柱 + WAPE线）
# ================================
period_order = [
    "深夜 (0:00-6:00)",
    "早高峰 (7:00-9:00)",
    "上午平峰 (9:00-12:00)",
    "午间 (12:00-14:00)",
    "下午平峰 (14:00-17:00)",
    "晚高峰 (17:00-19:00)",
    "夜间 (19:00-24:00)"
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
fig3_path = FIG_DIR / "fig3_period_performance.png"
plt.savefig(fig3_path, bbox_inches="tight")
plt.show()
plt.close()

# ================================
# 图4：下一时间步预测（分布 + Top/Bottom15）
# ================================
pred = pred_next["predicted_flow"].astype(float).values
top15 = pred_next.sort_values("predicted_flow", ascending=False).head(15)
bottom15 = pred_next.sort_values("predicted_flow", ascending=True).head(15)

fig = plt.figure(figsize=(13, 9))

ax1 = plt.subplot(2, 1, 1)
ax1.hist(pred, bins=30, color="#54A24B", alpha=0.8, edgecolor="white")
ax1.set_title("图4(a) 下一时间步全路段预测流量分布")
ax1.set_xlabel("预测流量（辆）")
ax1.set_ylabel("路段数量")
ax1.grid(alpha=0.25, axis="y")

ax2 = plt.subplot(2, 2, 3)
ax2.barh(top15["segment_id"].astype(int).astype(str),
         top15["predicted_flow"].astype(float),
         color="#F58518")
ax2.invert_yaxis()
ax2.set_title("图4(b) 流量最高Top15路段")
ax2.set_xlabel("预测流量（辆）")

ax3 = plt.subplot(2, 2, 4)
ax3.barh(bottom15["segment_id"].astype(int).astype(str),
         bottom15["predicted_flow"].astype(float),
         color="#E45756")
ax3.invert_yaxis()
ax3.set_title("图4(c) 流量最低Bottom15路段")
ax3.set_xlabel("预测流量（辆）")

plt.tight_layout()
fig4_path = FIG_DIR / "fig4_next_step_prediction.png"
plt.savefig(fig4_path, bbox_inches="tight")
plt.show()
plt.close()

# ================================
# 表1：核心指标汇总
# ================================
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
table_path = FIG_DIR / "table1_core_metrics.csv"
summary_df.to_csv(table_path, index=False, encoding="utf-8-sig")

print("\n图表与表格已生成：")
print(f"- {fig1_path}")
print(f"- {fig2_path}")
print(f"- {fig3_path}")
print(f"- {fig4_path}")
print(f"- {table_path}")
