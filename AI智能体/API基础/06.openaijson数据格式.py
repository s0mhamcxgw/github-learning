#json与字典差不多,key和value,里面可以嵌套字典,数组,字符串,列表
'''{
    "key":value,
    "key":value
}
#还有json数组的格式
[{},{},{}]'''
#格式转换,这是python转成json
import json
d={
    "name":"周杰伦",
    "age":12,
    "gender":"男"
}
json.dumps(d,ensure_ascii=False)
print(d)


