"""
工作流基类
作用：定义所有工作流的通用接口和基础功能
所有具体工作流（五阶闭环、单场景工作流等）都继承自此类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.llm_client import llm
from memory.manager import MemoryManager


class BaseWorkflow(ABC):
    """工作流基类"""

    def __init__(self, memory: MemoryManager = None):
        self.llm = llm
        self.memory = memory
        self.workflow_name = "基础工作流"
        self.stages = []  # 子类定义具体阶段
        self.results: Dict[str, Any] = {}  # 各阶段输出结果

    @abstractmethod
    def run(self, user_input: str) -> str:
        """
        执行工作流

        Args:
            user_input: 用户输入

        Returns:
            最终输出文本
        """
        pass

    def _call_llm(self, prompt: str, system_prompt: str = None) -> str:
        """
        调用 LLM（非流式，用于工作流内部各阶段）

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）

        Returns:
            LLM 回复文本
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self.llm.chat_non_stream(messages)

    def _save_result(self, stage: str, result: Any):
        """保存某阶段的结果"""
        self.results[stage] = result

    def _get_result(self, stage: str) -> Any:
        """获取某阶段的结果"""
        return self.results.get(stage, "")

    def _print_stage(self, stage_num: int, stage_name: str, description: str):
        """打印阶段开始信息"""
        print(f"\n{'─'*50}")
        print(f"  第{stage_num}步：{stage_name}")
        print(f"  {description}")
        print(f"{'─'*50}")

    def _print_stage_result(self, content: str, max_len: int = 500):
        """打印阶段结果（截断显示）"""
        if len(content) > max_len:
            print(content[:max_len] + f"\n...（共 {len(content)} 字符，已截断显示）")
        else:
            print(content)
