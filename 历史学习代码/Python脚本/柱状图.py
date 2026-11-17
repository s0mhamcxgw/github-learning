import matplotlib.pyplot as plt

# 准备数据（2023年Q4各城市销售额）
cities = ['北京', '上海', '广州', '深圳']
sales = [150, 180, 120, 160]

# 绘制柱状图
plt.figure(figsize=(8, 5))
plt.bar(cities, sales,
        color=['#4CAF50', '#2196F3', '#FF9800', '#E91E63'],  # 自定义颜色
        edgecolor='black',  # 柱子边框颜色
        width=0.6)          # 柱子宽度

# 添加数据标签（柱子顶部显示具体数值）
for i, v in enumerate(sales):
    plt.text(i, v + 5, f'{v}万元', ha='center', fontsize=10)  # ha: 水平对齐

# 设置标题和轴标签
plt.rcParams['font.sans-serif']=['SimHei']
plt.title('2023年Q4各城市销售额对比', fontsize=14)
plt.xlabel('城市', fontsize=12)
plt.ylabel('销售额（万元）', fontsize=12)

plt.show()
