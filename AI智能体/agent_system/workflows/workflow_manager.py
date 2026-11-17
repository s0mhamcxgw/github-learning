"""
工作流管理器
作用：统一管理和调度各种工作流，根据用户输入选择合适的工作流执行
"""
from typing import Optional
from workflows.five_stage import FiveStageWorkflow
from workflows.scene_classifier import SceneClassifier
from memory.manager import MemoryManager


class WorkflowManager:
    """工作流管理器"""

    def __init__(self, memory: MemoryManager = None):
        self.memory = memory
        self.scene_classifier = SceneClassifier()
        self.current_workflow = None
        self.workflow_history = []  # 工作流执行历史

    def execute(self, user_input: str, workflow_type: str = "five_stage") -> str:
        """
        执行工作流

        Args:
            user_input: 用户输入
            workflow_type: 工作流类型，默认五阶闭环

        Returns:
            工作流执行结果
        """
        if workflow_type == "five_stage":
            self.current_workflow = FiveStageWorkflow(memory=self.memory)
        else:
            print(f"[工作流] 未知工作流类型: {workflow_type}，使用默认五阶闭环")
            self.current_workflow = FiveStageWorkflow(memory=self.memory)

        # 执行工作流
        result = self.current_workflow.run(user_input)

        # 记录历史
        self.workflow_history.append({
            "input": user_input[:100],
            "workflow": workflow_type,
            "scene": self.current_workflow.current_scene,
            "stages_completed": 5
        })

        return result

    def quick_chat(self, user_input: str) -> str:
        """
        快速对话（不经过完整工作流，简单问答）
        用于简单问题，避免工作流开销

        Args:
            user_input: 用户输入

        Returns:
            回复文本
        """
        from core.llm_client import llm
        messages = [{"role": "user", "content": user_input}]
        return llm.chat_non_stream(messages)

    def should_use_workflow(self, user_input: str) -> bool:
        """
        判断是否应该使用完整工作流
        简单问题（问候、简单事实性问题）用快速对话
        复杂任务（写代码、写论文、做PPT等）用完整工作流

        Args:
            user_input: 用户输入

        Returns:
            是否使用工作流
        """
        # 简单问题的关键词
        simple_keywords = ["你好", "hi", "hello", "谢谢", "再见", "在吗", "干嘛",
                          "几点", "今天", "天气", "你是谁", "介绍一下自己"]

        input_lower = user_input.lower().strip()

        # 太短的输入可能是问候
        if len(input_lower) < 5:
            return False

        # 匹配简单关键词
        for kw in simple_keywords:
            if kw in input_lower and len(input_lower) < 20:
                return False

        # 复杂任务关键词（需要工作流）
        complex_keywords = ["写", "制作", "生成", "设计", "搭建", "开发", "分析",
                           "论文", "代码", "程序", "脚本", "PPT", "报告", "总结",
                           "帮我", "如何", "怎么", "方案", "框架"]

        for kw in complex_keywords:
            if kw in input_lower:
                return True

        # 默认：长度超过30字的用工作流
        return len(input_lower) > 30

    def get_workflow_stats(self) -> dict:
        """获取工作流执行统计"""
        return {
            "历史执行次数": len(self.workflow_history),
            "最近执行": self.workflow_history[-1] if self.workflow_history else None
        }
