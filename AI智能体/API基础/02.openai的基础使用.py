from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion

from pyexpat.errors import messages

client = OpenAI(
    # 如果没有配置环境变量，请用阿里云百炼API Key替换：api_key="sk-xxx"
    api_key='REDACTED_CREDENTIAL',
    base_url="https://ws-q3ed5buioquiomzd.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
)

#调用模型
resopnse=client.chat.completions.create(
    model='qwen3.7-plus',
    messages=[
        {'role':'system','content':'你是一个编程专家,用简单不说废话回答'},
        {'role':'assistant','content':'好的,我是编程专家,不说废话,你要问什么?'},
        {'role':'user','content':''},
    ]

)
print(resopnse.choices[0].message.content)
#for chunk in resopnse:
 #   print(
  #      chunk.choices[0].delta.content,
   #     end=' ',
    #    flush=True
    #)