"""P14：无额外参数的 __init__，课堂示例重录版。

来源：https://www.bilibili.com/video/BV1U2WmzfEqp/?p=14
按本节约10:00、15:00、16:00、20:05的可读画面核对逻辑，整理缩进与注释。
这是从视频重录的示例，不是下载到的官方配套源码。
"""


class Car:
    def __init__(self):
        print('我是 无参 init 魔法方法')
        self.color = '黑色'
        self.number = 3

    def show(self):
        print(f'颜色: {self.color}, 轮胎数: {self.number}')


# 创建第一个对象：自动执行 __init__，随后修改这一个对象的属性。
c1 = Car()
c1.color = '红色'
c1.number = 6
print(c1.color, c1.number)
c1.show()

print('-' * 34)

# 再创建一个对象：它独立进行初始化，仍使用黑色、3个轮胎的默认值。
c2 = Car()
c2.show()
