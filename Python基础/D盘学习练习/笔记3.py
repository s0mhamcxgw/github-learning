import random
num=random.randint(1,200)
#随机生成数
count=0
flag=False#无限次循环用一个标记，用布尔型本身
while flag:
    guess_num=int(input("请输入你猜想的数字："))
    count+=1
    if guess_num==num:
        print("恭喜猜对了！")
        flag=True
    else:
        if guess_num>num:
            print("猜想的数字大了")
        else:
            print("猜想的数字小了")
print(f"你一共猜想了{count}")

"""
while的循环嵌套
要用空格缩进来控制循环
注意内外层次的循环条件
"""
i=1
while i<=100:
    print(f"今天是第{i}天，准备表白。。。")
    j=1
    while j<=10:
        print(f"今天送石昆昆{j}朵玫瑰")
        j+=1
        print("喜欢石昆昆")
    i+=1
print(f"今天是第{i-1}天，表白成功")

#不换行功能edn=''输出九九乘法表
#制表符，\t进行字符对其
i=1
while i<=9:
    j=1
    while j<=i:
        print(f"{j}*{i}={j*i}\t",end='')
        j+=1
    i+=1
    print()#控制输出一个换行


