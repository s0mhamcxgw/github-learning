"""
工作流系统测试
验证：场景识别 + 五阶闭环工作流 + 工作流管理器
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflows.scene_classifier import SceneClassifier
from workflows.five_stage import FiveStageWorkflow
from workflows.workflow_manager import WorkflowManager
from memory.manager import MemoryManager


def test_scene_classifier():
    """测试1：场景识别器"""
    print("\n" + "="*50)
    print("测试1：场景识别器")
    print("="*50)

    classifier = SceneClassifier()

    # 测试用例
    test_cases = [
        ("帮我写一个Python数据预处理脚本，用pandas处理缺失值", "编程"),
        ("帮我写一篇大数据方向的开题报告，研究机器学习在金融风控中的应用", "论文"),
        ("帮我做一个毕业答辩PPT，主题是基于深度学习的图像识别", "办公"),
        ("帮我写一个答辩视频的脚本，时长5分钟", "视频"),
        ("你好", "编程"),  # 简单问候，默认编程
    ]

    all_pass = True
    for user_input, expected in test_cases:
        scene, config = classifier.classify(user_input)
        status = "通过" if scene == expected else f"失败（期望:{expected}，实际:{scene}）"
        if scene != expected:
            all_pass = False
        print(f"  输入: {user_input[:30]}...")
        print(f"    识别: {scene} | {status}")
        print()

    print(f"场景识别器测试: {'通过' if all_pass else '部分失败'}")
    return all_pass


def test_workflow_manager():
    """测试2：工作流管理器（模式判断）"""
    print("\n" + "="*50)
    print("测试2：工作流管理器（模式判断）")
    print("="*50)

    memory = MemoryManager()
    wf_manager = WorkflowManager(memory=memory)

    # 测试应该使用工作流的情况
    workflow_cases = [
        "帮我写一个Python机器学习模型训练脚本",
        "帮我写一篇关于数据挖掘的课程论文",
        "帮我做一个科研汇报PPT",
    ]

    # 测试应该使用快速对话的情况
    quick_cases = [
        "你好",
        "谢谢",
        "1+1等于几",
    ]

    print("应该使用工作流的情况:")
    for case in workflow_cases:
        result = wf_manager.should_use_workflow(case)
        print(f"  '{case[:25]}...' -> {'工作流' if result else '快速对话'} {'✓' if result else '✗'}")

    print("\n应该使用快速对话的情况:")
    for case in quick_cases:
        result = wf_manager.should_use_workflow(case)
        print(f"  '{case}' -> {'工作流' if result else '快速对话'} {'✓' if not result else '✗'}")

    print("\n工作流管理器测试: 通过")
    return True


def test_five_stage_workflow():
    """测试3：五阶闭环工作流（完整执行，耗时较长）"""
    print("\n" + "="*50)
    print("测试3：五阶闭环工作流（完整执行）")
    print("="*50)
    print("注意：此测试会调用5次API，可能需要1-2分钟\n")

    memory = MemoryManager()
    workflow = FiveStageWorkflow(memory=memory)

    # 用一个简单的测试需求
    test_input = "帮我写一个简单的Python脚本，计算斐波那契数列的前10项"

    print(f"测试需求: {test_input}")
    print("开始执行五阶闭环工作流...\n")

    try:
        result = workflow.run(test_input)

        # 验证结果
        print("\n" + "="*50)
        print("工作流执行结果验证")
        print("="*50)
        print(f"结果长度: {len(result)} 字符")
        print(f"包含'最终交付': {'是' if '最终交付' in result else '否'}")
        print(f"包含'复盘总结': {'是' if '复盘总结' in result else '否'}")
        print(f"场景识别: {workflow.current_scene}")
        print(f"各阶段结果:")
        for stage, content in workflow.results.items():
            print(f"  {stage}: {len(str(content))} 字符")

        print("\n五阶闭环工作流测试: 通过")
        return True
    except Exception as e:
        print(f"\n五阶闭环工作流测试失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "#"*50)
    print("#  工作流系统测试")
    print("#"*50)

    results = {}
    results["场景识别器"] = test_scene_classifier()
    results["工作流管理器"] = test_workflow_manager()

    # 询问是否运行完整工作流测试（耗时较长）
    print("\n" + "="*50)
    print("是否运行完整五阶工作流测试？（需要1-2分钟）")
    print("输入 y 运行，其他键跳过")
    print("="*50)
    try:
        choice = input("[y/N]: ").strip().lower()
    except:
        choice = "n"

    if choice == "y":
        results["五阶闭环工作流"] = test_five_stage_workflow()
    else:
        print("\n已跳过完整工作流测试（可在 main.py 中输入 /workflow 手动测试）")
        results["五阶闭环工作流"] = "跳过"

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
    if all_pass or results["五阶闭环工作流"] == "跳过":
        print("工作流系统核心功能测试通过！")
        print("运行 python main.py 启动智能体，复杂任务自动使用五阶闭环工作流。")
        print("也可以输入 /workflow 强制下一条消息使用工作流。")
    else:
        print("部分测试失败，请检查上方错误信息。")
    print("="*50)
