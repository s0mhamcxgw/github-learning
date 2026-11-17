
"""
元组的性质和列表区别是不能修改内容
元组=（元素，元素）
元组的访问和列表的访问一样
"""
T1=((1,2,3,4,5),(123,5135145))
num=T1[1][1]
print(num)

"""
字符串本身就是一个数据容器，本身不可修改
常见操作
字符串[下标]取出指定位置
字符串.index(字符串)指定的下标
字符串.replace(字符串1，字符串2)代替
字符串.split(字符串)字符串的分割，得到一个新的列表
字符串.strip()移除首尾的内容
字符串.strip(字符串)指定字符串前后的移除
"""
index=0
my_str="石老师"
while index<len(my_str):
    print(my_str[index])
    index+=1

for x in my_str:
    print(x)
#
my_str="itheima itcast boxuegu"
count=my_str.count("it")
print(f"字符串{my_str}有{count}个it")
my_new_str=my_str.replace(" ","|")
print(f"字符串{my_str}内容替换以后，结果{my_new_str}")
my_str_new_1=my_new_str.split("|")
print(f"得到分割以后的结果{my_str_new_1}")

"""
序列就是内容有序支持下标的一类数据容器
切片操作序列[起始：结束：步长]
可以为负数倒叙执行
"""
my_str="万过薪月，原序程马黑来，nohtyp学"
my_str_1=my_str[::-1]
print(f"{my_str_1}")
my_str_2=my_str_1[9:14:1]
print(f"{my_str_2}")
result= my_str.split("，")[1].replace("来"," ")[::-1]
print(f"{result}")

"""
集合是无序的不可重复的
可以进行修改等
集合.add(元素)集合内添加元素
集合1.difference(集合2)
集合1.difference_update(集合2)

"""
my_list=["黑","hei","黑","白"]
my_=set()
for i in my_list:
    my_.add(i)

print(f"原始的列表{my_list},得到的集合{my_}")

"""
字典可以提供基于key的价值
定义 {key:value,}
字典不可以重复，不支持下标索引
字典的常见操作，更新，新增,删除,清空，获取全部的key
字典[key]=value
字典.pop(key)
字典.clear()
字典.keys()
"""
#字典的遍历
my_dict={
        "王力宏":{
            "部门":"科技部",
            "工资":"3000",
            "级别":"1",
        "周杰轮":{
            "部门":"市场部",
            "工资":"5000",
            "级别":"2",
        "林俊杰":{
            "部门":"科技部",
            "工资":"7000",
            "级别":"3",
        "张学友":{
            "部门":"市场部",
            "工资":"4000",
            "级别":"1",
        "刘德华":{
            "部门":"科技部",
            "工资":"6000",
            "级别":"2",

        }

        }
        }
        }
        }


}
print(f"输出的结果{my_dict}")
for name in my_dict:
    if my_dict[name]["级别"]==1:
        employ=my_dict[name]#获取员工的信息
        employ["级别"]=2
        employ["工资"]+=1000
    my_dict[name]=employ

print(f"最后升值加薪的结果是：{my_dict}")
"""
列表用于一批数据，可修改，可重复
元组不可以修改，可以重复
集合去重，
字典就是键值对，不重复
之间互相住转换
sorted(序列,[reverse=Ture])排序操作
"""


