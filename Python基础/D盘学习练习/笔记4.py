"""
for循环是一种轮巡机制，逐个执行。
遍历循环
for 零食变量 in 被处理的数据:
无法定义循环条件

"""
i = 0
name="itheima is a brand of itcas"
for x in name:
    if x=="a":
        i+=1
print(f"一共有{i}个")

count=0
for x in range(1,1000):
    if x%2==0:
        count+=1
print(f"一共有{count}个偶数")

for x in range(1,101):
    print(f"像小妹表白的第{x}天")
    for y in range(2,10):
        print(f"今天送{y}朵玫瑰")

print("表白成功！")

for x in range(1,10):
    y=1
    while y<=x:
        print(f"{y}*{x}={x*y}\t",end='')
        y+=1
    print()



