money=50000000
name=None
name=input(f"请输入你的姓名：")
def query(show):
    if show:
        print("-----余额--------")
    else:
        print(f"您的余额为{money}")
def saving(num):
    global money
    money+=num
    print(f"{name}，您好，能成功存款{num}")
    query(False)

def get_money(num):
    global money
    money-=num
    if money<num:
        print("您的余额不足，不好意思")
    else:
        print(f"{name}，您好，能成功取款{num}")
        query(False)

def mean():
    print(f"-------主菜单---------")
    print(f"{name},您好，欢迎来的黑马银行！")
    print(f"查询余额输入\t【1】")
    print(f"存款输入\t\t【2】")
    print(f"取款输入\t\t【3】")
    print(f"退出输入\t\t【4】")
    return input(f"请输入你的选项")
#设置无限循环
while True:
    kinbor_number=mean()
    if kinbor_number=="1":
        query(True)
        continue
    elif kinbor_number=="2":
        num=int(input(f"请输入你存的钱:"))
        saving(num)
        continue
    elif kinbor_number=="3":
        num=int(input(f"请输入你取的钱:"))
        get_money(num)
        continue
    else:
        print(f"退出程序！")
        break
