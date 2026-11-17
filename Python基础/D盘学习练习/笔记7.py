"""
数据容器可以容纳任意类型的数据
列表list    变量名称=[元素1，元素2]
支持嵌套
"""
#列表的索引查找
list_1=["itheima","python","itcast"]
index = list_1.index("python")
print(f"列表的索引是{index}")
#列表元素的修改，语法：列表【下标】=值
list_1[1]="hello"
print(list_1)
#指定条件下插入新的元素语法列表.insert(下标，元素)
list_1.insert(0,"dada")
print(list_1)
#指定元素追加到列表的尾部列表。append(元素)
list_1.append("haha")
print(list_1)
#追加数据的容器列表.extend(其他数据容器)，依次追加到数据的尾部
list_2=[[1123,1231,4621],[1235,4521,5125]]
list_1.extend(list_2)
print(list_1)
#删除元素，del列表[下标]，第二种列表.pop(下标)
list_3=list_1.pop(0)
print(f"输出的内容{list_1}，取出的值{list_3}")
#指定元素的内容删除，语法列表.remove(元素),删除第一个指定项
list_1=["111","111","222"]
list_1.remove("111")
print(f"移除的结果是：{list_1}")
#清空列表的内容语法列表.clear()
list_1.clear()
print(list_1)
#统计列表中的元素个数，语法列表.count（元素）,有返回值
list_1=["itheima","python","itcast"]
count=list_1.count("python")
print(f"次数是{count}次")
#统计列表的元素的数量len(列表)，有返回值
list_1=["itheima","python","itcast"]
count=len(list_1)
print(f"列表的元素有{count}个")

list_student=[21,25,21,23,22,20]
print(list_student)
#追加一个数字到列表的尾部
list_student.append(31)

#追加一个新的列表
list_student_1=[23,33,30]
list_student.extend(list_student_1)
#取出一个元素
#实现对列表中对偶数的取出建一个新的列表
index=0#获取下标索引
list=[1,2,3,4,5,6,7,8,9,10]
#建立一个新的空列表
list_1=[]
while index<len(list):
    if list[index]%2==0:
        list_1.append(list[index])
        index+=1
print(f"偶数的新列表为：{list_1}")



