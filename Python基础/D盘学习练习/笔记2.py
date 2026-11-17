"""
嵌套使用空格缩进来控制
判断层次关系
"""
if 30>int(input("请输入你的年纪："))>=18:
    print("你的年纪达标，恭喜！")
    if int(input("请输入你的入职年时间："))>2:
        print("恭喜满足条件！")
    elif int(input("请输入你的级别："))>3:
            print("恭喜满足条件！")
    else:
        print("不满足条件！")
else:
    print("年纪不达标！")

print("-------------------")
"""
案列需求，随机产生一个数字，通过判断关系来猜出数字
每次猜不中，会提示大小
"""
import random
num = random.randint(1,10)
guess_num=int(input("请输入你猜的数字："))
if guess_num == num:
    print("恭喜猜对！")
else:
    if guess_num>num:
        print("输入的数字大了")
    else:
        print("输入的数字小了")
    guess_num = int(input("再次请输入你猜的数字："))
    if guess_num == num:
        print("第二次恭喜猜对！")
    else:
        if guess_num > num:
            print("输入的数字大了")
        else:
            print("输入的数字小了")
        guess_num = int(input("再次请输入你猜的数字："))
        if guess_num == num:
            print("第三次恭喜猜对！")
        else:
            print("机会用完了")

print("-----------------")
'''
循环语句 满足条件进行操作，进行循环，条件不满足，跳出循环。
while 条件：条件是布尔类型
注意设置终止条件
案列练习求1到100的和
'''
i = 1
sum=0
while i<=100:
    sum = sum + i
    print(f"1到{i}的和为{sum}")
    i+=1
