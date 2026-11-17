# 说明：按扫描页重排、规范排版标点与提示语；不是出版社源代码文件。
# 来源：《数据科学基础》PDF第24页。
# 状态：对照原图校正，实际运行通过。

import math

angle = float(input("请输入角度："))
radian = math.pi / 180 * angle
SinF = math.sin(radian)
print("弧度=", radian)
print("sin函数值=", SinF)
