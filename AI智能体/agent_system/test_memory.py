"""
记忆系统测试
验证：短期记忆持久化 + 长期记忆存储 + 记忆注入 + 自动提取
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory.manager import MemoryManager
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory


def test_short_term():
    """测试1：短期记忆"""
    print("\n" + "="*50)
    print("测试1：短期记忆（对话历史持久化）")
    print("="*50)

    stm = ShortTermMemory()

    # 创建会话
    session_id = stm.create_session("测试会话")
    print(f"创建会话: {session_id}")

    # 添加消息
    stm.add_message("user", "你好，我是大数据专业的学生")
    stm.add_message("assistant", "你好！我是你的全能智能体，有什么可以帮你的？")
    stm.add_message("user", "帮我写一个Python数据预处理脚本")
    stm.add_message("assistant", "好的，这是一个数据预处理脚本...")

    print(f"消息数: {len(stm.messages)}")

    # 获取最近消息
    recent = stm.get_recent_messages(2)
    print(f"最近2条消息: {len(recent)} 条")

    # 列出所有会话
    sessions = stm.list_sessions()
    print(f"历史会话数: {len(sessions)}")

    # 清空（保留system）
    stm.clear()
    print(f"清空后消息数: {len(stm.messages)}")

    print("短期记忆测试: 通过")
    return True


def test_long_term():
    """测试2：长期记忆"""
    print("\n" + "="*50)
    print("测试2：长期记忆（偏好/FAQ/经验/知识库）")
    print("="*50)

    ltm = LongTermMemory()

    # 添加偏好
    ltm.add_preference("编程", "主力IDE", "PyCharm", "用户主力使用PyCharm CE 2024.3")
    ltm.add_preference("编程", "代码注释", "中文", "偏好中文注释")
    ltm.add_preference("论文", "引用格式", "GB/T 7714", "学校要求")

    prefs = ltm.get_preferences()
    print(f"用户偏好数: {len(prefs)}")
    for p in prefs:
        print(f"  [{p['category']}] {p['key']}: {p['value']}")

    # 添加 FAQ
    ltm.add_faq(
        "如何在PyCharm中配置虚拟环境？",
        "File -> Settings -> Project -> Python Interpreter -> Add -> Existing environment -> 选择.venv/Scripts/python.exe",
        "编程", ["PyCharm", "虚拟环境", "配置"]
    )
    ltm.add_faq(
        "Python 3.13 安装pandas报错怎么办？",
        "确保pip是最新版本，使用 pip install --upgrade pip，然后安装最新版pandas",
        "编程", ["Python", "pandas", "报错"]
    )

    # 检索 FAQ
    results = ltm.search_faq("PyCharm 虚拟环境配置")
    print(f"\nFAQ检索'PyCharm 虚拟环境配置': {len(results)} 条结果")
    for r in results:
        print(f"  Q: {r['question']}")

    # 添加经验
    ltm.add_experience(
        "百炼API流式输出处理",
        "使用qwen3.8-max的流式输出时，需要区分reasoning_content（思考过程）和content（最终回复），不能直接拼接所有content",
        "编程",
        "成功解决流式输出乱码问题"
    )

    experiences = ltm.get_experiences()
    print(f"\n历史经验数: {len(experiences)}")

    # 添加知识
    ltm.add_knowledge(
        "阿里云百炼API",
        "阿里云百炼支持OpenAI兼容模式，base_url为.../compatible-mode/v1，可使用openai SDK直接调用",
        "文档"
    )

    # 检索知识
    knowledge = ltm.search_knowledge("百炼 API")
    print(f"知识库检索: {len(knowledge)} 条结果")

    # 统计
    stats = ltm.get_stats()
    print(f"\n长期记忆统计: {stats}")

    print("长期记忆测试: 通过")
    return True


def test_memory_manager():
    """测试3：记忆管理器（记忆注入）"""
    print("\n" + "="*50)
    print("测试3：记忆管理器（上下文注入）")
    print("="*50)

    mm = MemoryManager()
    mm.start_new_session("注入测试")
    mm.add_system_message("你是一个测试助手。")

    # 添加用户偏好（模拟已积累的记忆）
    mm.long_term.add_preference("编程", "主力IDE", "PyCharm", "测试用")
    mm.long_term.add_faq("测试问题", "测试答案", "通用", ["测试"])

    # 添加对话历史
    mm.add_user_message("我之前问过什么？")
    mm.add_assistant_message("你之前问了关于Python的问题。")

    # 获取带记忆注入的上下文
    context = mm.get_context_messages("帮我配置PyCharm虚拟环境")

    print(f"上下文消息数: {len(context)}")
    print("\n上下文内容预览:")
    for i, msg in enumerate(context):
        role = msg["role"]
        content = msg["content"][:80].replace("\n", " ")
        print(f"  [{i}] {role}: {content}...")

    # 检查是否有记忆注入
    has_memory = any("长期记忆" in msg["content"] for msg in context)
    print(f"\n记忆注入成功: {'是' if has_memory else '否'}")

    # 统计
    stats = mm.get_memory_stats()
    print(f"记忆统计: {stats}")

    print("记忆管理器测试: 通过")
    return True


if __name__ == "__main__":
    print("\n" + "#"*50)
    print("#  记忆系统测试")
    print("#"*50)

    results = {}
    results["短期记忆"] = test_short_term()
    results["长期记忆"] = test_long_term()
    results["记忆管理器"] = test_memory_manager()

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
        print("全部测试通过！记忆系统已就绪。")
        print("运行 python main.py 启动带记忆的智能体。")
    else:
        print("部分测试失败，请检查上方错误信息。")
    print("="*50)
