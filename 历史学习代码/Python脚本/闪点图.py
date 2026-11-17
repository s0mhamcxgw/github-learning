import matplotlib.pyplot as plt
import numpy as np

# 生成模拟数据（身高cm，体重kg）
np.random.seed(42)  # 固定随机数，结果可复现
height = np.random.normal(170, 5, 100)  # 均值170，标准差5，100个样本
weight = 0.7 * height + np.random.normal(0, 3, 100)  # 身高与体重正相关，带随机误差

# 绘制散点图
plt.figure(figsize=(8, 6))
plt.scatter(height, weight,
            color='red',    # 点颜色
            alpha=0.6,      # 透明度（0.6避免重叠看不清）
            s=30,           # 点大小
            edgecolor='black')  # 点边框颜色

# 添加拟合直线（显示相关性）
m, b = np.polyfit(height, weight, 1)  # 1次多项式拟合（直线）
plt.plot(height, m*height + b, color='blue', linewidth=2, label='拟合直线')

# 设置标题和标签
plt.title('身高与体重相关性分析', fontsize=14)
plt.xlabel('身高（cm）', fontsize=12)
plt.ylabel('体重（kg）', fontsize=12)
plt.legend()

plt.show()
