import matplotlib.pyplot as plt
import numpy as np

# 准备数据（2023年各月销售额，单位：万元）
months = np.arange(1, 13)  # [1,2,...,12]
sales = [50, 60, 55, 70, 80, 90, 85, 100, 110, 120, 130, 180]

# 绘制折线图
plt.figure(figsize=(10, 5))  # 设置画布大小（宽10，高5）
plt.plot(months, sales,
         color='blue',       # 线条颜色
         marker='o',         # 数据点标记（圆形）
         linestyle='-',      # 线条样式（实线）
         linewidth=2,        # 线条粗细
         label='月销售额')    # 图例标签

# 添加图表标题和轴标签
plt.rcParams['font.sans-serif']=['SimHei']
plt.title('2023年各月销售额趋势图', fontsize=14, fontweight='bold')
plt.xlabel('月份', fontsize=12)
plt.ylabel('销售额（万元）', fontsize=12)

# 添加网格和图例
plt.grid(True, linestyle='--', alpha=0.5)  # 虚线网格，透明度0.5
plt.legend()  # 显示图例

# 显示图表（IDE中会弹出窗口，Jupyter中直接显示）
plt.show()
