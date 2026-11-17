class student:
    name=None
    age=None
    ard=None
def __init__(self,name,age,ard):
    self.name=name
    self.age=age
    self.ard=ard
def __str__(self):
    return f"姓名:{self.name},年龄:{self.age},地址:{self.ard}"
num_student=10
students=[]
for i in range(num_student):
    name = input(f"请输入第{i + 1}个学生的姓名：")
    age = input(f"请输入第{i + 1}个学生的年纪：")
    ard = input(f"请输入第{i + 1}个学生的地址：")
    students=student(name,age,ard)
    students.append(student)
for student in students:
    print(student)
