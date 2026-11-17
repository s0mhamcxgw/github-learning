"""
Agent 管理器（工厂模式）
作用：根据场景名称创建对应的场景 Agent，统一管理所有 Agent
支持：编程 Agent、论文 Agent、办公 Agent、视频 Agent
"""
from typing import Dict, Type, Optional, List
from agents.base import BaseSceneAgent
from agents.coding_agent import CodingAgent
from agents.paper_agent import PaperAgent
from agents.office_agent import OfficeAgent
from agents.video_agent import VideoAgent
from memory.manager import MemoryManager


class AgentManager:
    """Agent 管理器（工厂模式）"""

    # 场景到 Agent 类的映射
    AGENT_MAP: Dict[str, Type[BaseSceneAgent]] = {
        "编程": CodingAgent,
        "论文": PaperAgent,
        "办公": OfficeAgent,
        "视频": VideoAgent,
    }

    def __init__(self, memory: MemoryManager = None):
        self.memory = memory
        self.current_agent: Optional[BaseSceneAgent] = None
        self.agent_history: List[Dict] = []  # Agent 使用历史

    def create_agent(self, scene: str) -> BaseSceneAgent:
        """
        根据场景创建对应的 Agent

        Args:
            scene: 场景名称（编程/论文/办公/视频）

        Returns:
            场景 Agent 实例
        """
        agent_class = self.AGENT_MAP.get(scene)
        if not agent_class:
            print(f"[Agent管理器] 未知场景: {scene}，使用默认编程 Agent")
            agent_class = CodingAgent

        agent = agent_class(memory=self.memory)
        self.current_agent = agent

        # 记录历史
        self.agent_history.append({
            "scene": scene,
            "agent_name": agent.__class__.__name__,
            "tools": agent.tools,
        })

        print(f"[Agent管理器] 已创建 {agent.scene_name} Agent ({agent.__class__.__name__})")
        return agent

    def process(self, scene: str, user_input: str) -> str:
        """
        创建 Agent 并处理用户需求

        Args:
            scene: 场景名称
            user_input: 用户输入

        Returns:
            处理结果
        """
        agent = self.create_agent(scene)
        return agent.process(user_input)

    def get_available_scenes(self) -> List[str]:
        """获取所有可用场景"""
        return list(self.AGENT_MAP.keys())

    def get_agent_info(self, scene: str = None) -> Dict:
        """
        获取 Agent 信息

        Args:
            scene: 场景名称，如为 None 则返回所有场景信息

        Returns:
            Agent 信息字典
        """
        if scene:
            agent_class = self.AGENT_MAP.get(scene)
            if agent_class:
                # 创建临时实例获取信息（不调用 process）
                agent = agent_class(memory=self.memory)
                return agent.get_scene_info()
            return {}

        # 返回所有场景信息
        all_info = {}
        for scene_name, agent_class in self.AGENT_MAP.items():
            agent = agent_class(memory=self.memory)
            all_info[scene_name] = agent.get_scene_info()
        return all_info

    def get_current_agent(self) -> Optional[BaseSceneAgent]:
        """获取当前使用的 Agent"""
        return self.current_agent

    def get_stats(self) -> Dict:
        """获取 Agent 使用统计"""
        return {
            "可用场景数": len(self.AGENT_MAP),
            "可用场景": list(self.AGENT_MAP.keys()),
            "历史调用次数": len(self.agent_history),
            "最近使用": self.agent_history[-1] if self.agent_history else None,
        }
