# -*- coding: utf-8 -*-
"""
LangChain 调用大语言模型（LLM）示例
====================================

在 PyCharm 中直接右键运行本文件即可。

依赖安装（在 PyCharm 终端执行）：
    pip install -r requirements.txt

运行前需要设置环境变量 DASHSCOPE_API_KEY（阿里云百炼 API Key）：
    方式一：PyCharm -> Run -> Edit Configurations -> Environment variables
            填入 DASHSCOPE_API_KEY=sk-xxxx
    方式二：在本文件同目录创建 .env 文件（参考 .env.example），
            代码会自动加载（需要 python-dotenv）

如果要用 OpenAI 官方模型，见文末 switch_to_openai() 的说明。
"""

import os

# 可选：从 .env 文件加载环境变量（需安装 python-dotenv）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# DashScope（阿里云百炼）的 OpenAI 兼容地址
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def build_llm() -> ChatOpenAI:
    """创建并返回一个 LLM 客户端实例。"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "未检测到环境变量 DASHSCOPE_API_KEY。\n"
            "请在 PyCharm 运行配置中设置该环境变量，"
            "或在项目根目录创建 .env 文件（参考 .env.example）。"
        )
    return ChatOpenAI(
        model="qwen-plus",          # 可换成 qwen-turbo / qwen-max 等
        api_key=api_key,
        base_url=DASHSCOPE_BASE_URL,
        temperature=0.7,            # 采样温度，0~2，越高越发散
    )


def demo_basic_chat() -> None:
    """示例 1：最基础的一问一答。"""
    llm = build_llm()
    messages = [
        SystemMessage(content="你是一个简洁专业的AI助手。"),
        HumanMessage(content="用一句话介绍 LangChain。"),
    ]
    response = llm.invoke(messages)
    print("【基础对话】")
    print(response.content)


def demo_chain() -> None:
    """示例 2：提示词模板 + 模型 + 输出解析器组成链（LCEL 写法）。"""
    llm = build_llm()
    prompt = ChatPromptTemplate.from_template(
        "请把下面这句话翻译成{language}，只输出译文：\n{text}"
    )
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"language": "英文", "text": "今天天气真好，适合写代码。"})
    print("\n【链式调用（翻译）】")
    print(result)


def demo_streaming() -> None:
    """示例 3：流式输出，逐字打印回复。"""
    llm = build_llm()
    print("\n【流式输出】")
    for chunk in llm.stream("用三句话说明大语言模型的工作原理。"):
        print(chunk.content, end="", flush=True)
    print()


def demo_multi_turn() -> None:
    """示例 4：多轮对话，手动维护消息历史。"""
    llm = build_llm()
    history = [SystemMessage(content="你是一个耐心的编程导师。")]

    for question in ["什么是向量数据库？", "它和传统数据库有什么区别？"]:
        history.append(HumanMessage(content=question))
        response = llm.invoke(history)
        history.append(response)
        print(f"\n【多轮对话】用户：{question}")
        print(f"【多轮对话】模型：{response.content}")


def switch_to_openai() -> None:
    """
    如果要改用 OpenAI 官方模型，只需调整 build_llm()：
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
            # 不传 base_url 即默认使用 OpenAI 官方地址
        )
    其他调用方式完全不变。
    """


if __name__ == "__main__":
    demo_basic_chat()
    demo_chain()
    demo_streaming()
    demo_multi_turn()
