# 说明：按扫描页重排、规范排版标点与提示语；不是出版社源代码文件。
# 来源：《数据科学基础》PDF第25页。
# 状态：对照原图校正，实际运行通过（实数根输入）。
# 原书练习范围为 a 不等于 0；未扩展为一般方程求解器。

import math

a = float(input("请输入系数 a："))
b = float(input("请输入系数 b："))
c = float(input("请输入系数 c："))
delta = b * b - 4 * a * c
if delta >= 0:
    root1 = (-b + math.sqrt(delta)) / (2 * a)
    root2 = (-b - math.sqrt(delta)) / (2 * a)
    print("root1=", root1, "\nroot2=", root2)
else:
    print("无实数根")
