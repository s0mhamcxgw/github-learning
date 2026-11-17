"""
智能体系统连通性测试
验证：配置加载 → 提示词加载 → API 调用 是否正常
"""
import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from core.prompt_loader import prompt_loader
from core.llm_client import llm


def test_config():
    """测试1：配置加载"""
    print("\n" + "="*50)
    print("测试1：配置加载")
    print("="*50)
    ok = settings.validate()
    print(f"API Key 已配置: {'是' if settings.API_KEY else '否'}")
    print(f"Base URL: {settings.BASE_URL}")
    print(f"默认模型: {settings.DEFAULT_MODEL}")
    return ok


def test_prompt():
    """测试2：系统提示词加载"""
    print("\n" + "="*50)
    print("测试2：系统提示词加载")
    print("="*50)
    prompts = prompt_loader.list_prompts()
    print(f"可用提示词文件: {prompts}")
    content = prompt_loader.load("system_prompt.md")
    print(f"提示词长度: {len(content)} 字符")
    print(f"提示词前100字: {content[:100]}...")
    return len(content) > 0


def test_api():
    """测试3：API 调用"""
    print("\n" + "="*50)
    print("测试3：API 调用（非流式，简单问题）")
    print("="*50)
    messages = [
        {"role": "system", "content": "你是一个测试助手，用简短的话回答。"},
        {"role": "user", "content": "说一句'智能体测试成功'，然后用一句话介绍你自己。"}
    ]
    response = llm.chat_non_stream(messages)
    print(f"API 回复:\n{response}")
    return "成功" in response or len(response) > 10


def test_stream():
    """测试4：流式输出"""
    print("\n" + "="*50)
    print("测试4：流式输出（带思考模式）")
    print("="*50)
    messages = [
        {"role": "user", "content": "1+1等于几？请简单思考后回答。"}
    ]
    print("流式输出:")
    full = ""
    for chunk in llm.chat(messages, stream=True):
        print(chunk, end="", flush=True)
        full += chunk
    print()
    return len(full) > 0


if __name__ == "__main__":
    print("\n" + "#"*50)
    print("#  贵财大数据专硕全能智能体 - 连通性测试")
    print("#"*50)

    results = {}
    results["配置加载"] = test_config()
    results["提示词加载"] = test_prompt()
    results["API调用"] = test_api()
    results["流式输出"] = test_stream()

    print("\n" + "="*50)
    print("测试结果汇总")
    print("="*50)
    all_pass = True
    for name, ok in results.items():
        status = "通过" if ok else "失败"
        print(f"  {name}: {status}")
        if not ok:
            all_pass = False

    print("="*50)
    if all_pass:
        print("全部测试通过！智能体系统可以正常运行。")
        print("运行 python main.py 启动交互式对话。")
    else:
        print("部分测试失败，请检查上方错误信息。")
    print("="*50)
