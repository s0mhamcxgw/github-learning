import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# 定义爱心的参数方程
def heart_3d(x, y, z):
    return (x**2 + (9/4)*y**2 + z**2 - 1)**3 - x**2*z**3 - (9/80)*y**2*z**3

# 创建一个3D图形
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 设置坐标轴的范围
ax.set_xlim(-1.5, 1.5)
ax.set_ylim(-1.5, 1.5)
ax.set_zlim(-1.5, 1.5)

# 创建一个网格
x = np.linspace(-1.5, 1.5, 30)
y = np.linspace(-1.5, 1.5, 30)
z = np.linspace(-1.5, 1.5, 30)
X, Y, Z = np.meshgrid(x, y, z)

# 计算心形的值
F = heart_3d(X, Y, Z)

# 创建一个3D曲面图
surf = ax.plot_surface(X, Y, Z, F, cmap='hot')

# 设置坐标轴标签
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

# 创建动画
def update(frame):
    ax.clear()
    ax.plot_surface(X, Y, Z, F, cmap='hot')
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_zlim(-1.5, 1.5)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

ani = animation.FuncAnimation(fig, update, frames=100, interval=50)

# 显示动画
plt.show()