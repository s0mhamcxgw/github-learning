"""
场景 Agent 基类
作用：定义所有场景 Agent 的通用接口和基础功能
每个场景 Agent（编程/论文/办公/视频）都继承此类，实现场景特有的能力
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from core.llm_client import llm
from core.prompt_loader import prompt_loader
from memory.manager import MemoryManager


class BaseSceneAgent(ABC):
    """场景 Agent 基类"""

    def __init__(self, memory: MemoryManager = None):
        self.llm = llm
        self.memory = memory
        self.scene_name = "基础场景"
        self.scene_description = "基础场景描述"
        self.system_prompt = ""  # 子类加载专属提示词
        self.tools = []  # 子类定义可用工具
        self.acceptance_criteria = ""  # 子类定义验收标准
        self.results: Dict[str, Any] = {}

    @abstractmethod
    def load_prompt(self):
        """加载场景专属系统提示词"""
        pass

    @abstractmethod
    def process(self, user_input: str) -> str:
        """
        处理用户需求（场景特有的处理流程）

        Args:
            user_input: 用户输入

        Returns:
            处理结果
        """
        pass

    @abstractmethod
    def get_acceptance_criteria(self) -> str:
        """获取场景验收标准"""
        pass

    def _call_llm(self, prompt: str, system_prompt: str = None) -> str:
        """调用 LLM（带场景系统提示词）"""
        messages = []
        # 优先使用传入的系统提示词，否则使用场景默认的
        sys_prompt = system_prompt or self.system_prompt
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})
        messages.append({"role": "user", "content": prompt})
        return self.llm.chat_non_stream(messages)

    def _call_llm_stream(self, prompt: str, system_prompt: str = None):
        """调用 LLM（流式输出）"""
        messages = []
        sys_prompt = system_prompt or self.system_prompt
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})
        messages.append({"role": "user", "content": prompt})
        return self.llm.chat(messages, stream=True)

    def _save_result(self, key: str, value: Any):
        """保存处理结果"""
        self.results[key] = value

    def _get_result(self, key: str) -> Any:
        """获取处理结果"""
        return self.results.get(key, "")

    def get_scene_info(self) -> Dict:
        """获取场景信息"""
        return {
            "scene_name": self.scene_name,
            "scene_description": self.scene_description,
            "tools": self.tools,
        }

    def _print_stage(self, stage_name: str, description: str):
        """打印处理阶段"""
        print(f"\n  [{self.scene_name} Agent] {stage_name}")
        print(f"    {description}")
