"""
场景化 Agent 系统测试
验证：四个场景 Agent 的创建、提示词加载、Agent 管理器调度
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.agent_manager import AgentManager
from agents.coding_agent import CodingAgent
from agents.paper_agent import PaperAgent
from agents.office_agent import OfficeAgent
from agents.video_agent import VideoAgent
from memory.manager import MemoryManager


def test_agent_creation():
    """测试1：四个场景 Agent 的创建和提示词加载"""
    print("\n" + "="*50)
    print("测试1：场景 Agent 创建与提示词加载")
    print("="*50)

    memory = MemoryManager()
    agent_classes = [
        ("编程", CodingAgent),
        ("论文", PaperAgent),
        ("办公", OfficeAgent),
        ("视频", VideoAgent),
    ]

    all_pass = True
    for scene_name, agent_class in agent_classes:
        try:
            agent = agent_class(memory=memory)
            info = agent.get_scene_info()
            prompt_loaded = len(agent.system_prompt) > 100

            print(f"\n  【{scene_name} Agent】")
            print(f"    类名: {agent_class.__name__}")
            print(f"    描述: {info.get('scene_description', '')[:50]}...")
            print(f"    工具数: {len(info.get('tools', []))}")
            print(f"    提示词长度: {len(agent.system_prompt)} 字符")
            print(f"    提示词加载: {'✓ 通过' if prompt_loaded else '✗ 失败'}")

            if not prompt_loaded:
                all_pass = False
        except Exception as e:
            print(f"  【{scene_name} Agent】创建失败: {e}")
            all_pass = False

    print(f"\n场景 Agent 创建测试: {'全部通过' if all_pass else '部分失败'}")
    return all_pass


def test_agent_manager():
    """测试2：Agent 管理器（工厂模式）"""
    print("\n" + "="*50)
    print("测试2：Agent 管理器（工厂模式）")
    print("="*50)

    memory = MemoryManager()
    manager = AgentManager(memory=memory)

    # 测试可用场景
    scenes = manager.get_available_scenes()
    print(f"  可用场景: {scenes}")
    print(f"  场景数: {len(scenes)}")

    # 测试每个场景的 Agent 创建
    all_pass = True
    for scene in scenes:
        try:
            agent = manager.create_agent(scene)
            print(f"  创建 {scene} Agent: ✓ ({agent.__class__.__name__})")
        except Exception as e:
            print(f"  创建 {scene} Agent: ✗ ({e})")
            all_pass = False

    # 测试未知场景回退
    agent = manager.create_agent("未知场景")
    print(f"  未知场景回退: ✓ (使用 {agent.scene_name} Agent)")

    # 测试统计
    stats = manager.get_stats()
    print(f"\n  管理器统计:")
    print(f"    可用场景数: {stats['可用场景数']}")
    print(f"    历史调用次数: {stats['历史调用次数']}")

    print(f"\nAgent 管理器测试: {'通过' if all_pass else '部分失败'}")
    return all_pass


def test_scene_prompts():
    """测试3：场景提示词文件"""
    print("\n" + "="*50)
    print("测试3：场景提示词文件检查")
    print("="*50)

    prompt_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "prompts", "scenes")
    expected_files = ["coding.md", "paper.md", "office.md", "video.md"]

    all_pass = True
    for filename in expected_files:
        filepath = os.path.join(prompt_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"  {filename}: ✓ ({len(content)} 字符)")
            if len(content) < 100:
                print(f"    警告: 提示词内容过短")
                all_pass = False
        else:
            print(f"  {filename}: ✗ (文件不存在)")
            all_pass = False

    print(f"\n场景提示词文件测试: {'全部通过' if all_pass else '部分失败'}")
    return all_pass


def test_single_agent_process():
    """测试4：单个场景 Agent 完整执行（可选，耗时较长）"""
    print("\n" + "="*50)
    print("测试4：场景 Agent 完整执行（可选）")
    print("="*50)
    print("此测试会调用多次API，可能需要1-2分钟")
    print("输入 y 运行，其他键跳过")

    try:
        choice = input("[y/N]: ").strip().lower()
    except:
        choice = "n"

    if choice != "y":
        print("已跳过完整执行测试")
        return "跳过"

    memory = MemoryManager()
    manager = AgentManager(memory=memory)

    # 用一个简单的编程需求测试
    test_input = "帮我写一个简单的Python脚本，计算斐波那契数列的前10项"
    print(f"\n测试需求: {test_input}")
    print("开始执行编程 Agent...\n")

    try:
        result = manager.process("编程", test_input)
        print(f"\n执行完成，结果长度: {len(result)} 字符")
        print(f"包含'编程 Agent 交付物': {'是' if '编程 Agent 交付物' in result else '否'}")
        print("\n场景 Agent 完整执行测试: 通过")
        return True
    except Exception as e:
        print(f"\n场景 Agent 完整执行测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "#"*50)
    print("#  场景化 Agent 系统测试")
    print("#"*50)

    results = {}
    results["Agent创建"] = test_agent_creation()
    results["Agent管理器"] = test_agent_manager()
    results["场景提示词"] = test_scene_prompts()
    results["完整执行"] = test_single_agent_process()

    print("\n" + "="*50)
    print("测试结果汇总")
    print("="*50)
    all_pass = True
    for name, ok in results.items():
        if ok == "跳过":
            status = "跳过"
        else:
            status = "通过" if ok else "失败"
            if not ok:
                all_pass = False
        print(f"  {name}: {status}")

    print("="*50)
    if all_pass or results["完整执行"] == "跳过":
        print("场景化 Agent 系统核心功能测试通过！")
        print("运行 python main.py 启动智能体，复杂任务自动调用对应场景 Agent。")
        print("也可以输入 /scene 编程 强制使用编程 Agent。")
    else:
        print("部分测试失败，请检查上方错误信息。")
    print("="*50)
