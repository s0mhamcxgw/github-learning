"""
continue用于中断本次循环，直接进入下一次循环
适用于while和for循环
for x in 处理数据:
    语句一
    continue
    语句二
跳出循环不会执行语句二
进入下一次循环
"""

money=10000
#for循环对员工发送工资
for x in range(1,20):
    import random
    num = random.randint(1, 10)
    if num <5:
        print(f"{x}不发工资，下一位")
        continue#continue跳过发放
    if money >=1000:#判断余下的前是否足够
        money-=1000
        print(f"向{x}发送工资1000元,账户余额还剩余{money}元")
    else:
        print(f"余额不足{money}，下个月发放工资")
        break
"""
函数是说已有的模块。特定的功能，只需要调用
减少代码的重复率
函数的定义
def 函数名（传入参数）：
    函数体
    return返回值
    其中传入参数和返回值不做硬性的要求
    函数的调用
    函数名（参数）
"""

#定义一个函数完成两个数的相加
def add(a,b):
    result=a+b
    return result
#函数的返回值可以用一个变量去接收
r=add(5,9)
print(r)







