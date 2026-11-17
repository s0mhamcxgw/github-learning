"""
工具基类
作用：定义所有工具的通用接口和基础功能
每个具体工具（代码执行、文件读写、包管理等）都继承此类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseTool(ABC):
    """工具基类"""

    def __init__(self):
        self.tool_name = "基础工具"
        self.tool_description = "基础工具描述"
        self.parameters = {}  # 参数定义：{"param_name": {"type": "str", "description": "...", "required": True}}
        self.enabled = True

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行工具

        Returns:
            执行结果字典，必须包含：
            - success: bool，是否成功
            - result: str，执行结果文本
            - error: str，错误信息（如有）
            - data: Any，附加数据（如有）
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """获取工具信息（用于 LLM 选择工具）"""
        return {
            "name": self.tool_name,
            "description": self.tool_description,
            "parameters": self.parameters,
            "enabled": self.enabled,
        }

    def validate_params(self, **kwargs) -> Optional[str]:
        """
        验证参数是否齐全

        Returns:
            错误信息（如有），None 表示验证通过
        """
        for param_name, param_def in self.parameters.items():
            if param_def.get("required", False) and param_name not in kwargs:
                return f"缺少必填参数: {param_name} ({param_def.get('description', '')})"
        return None

    def _success(self, result: str, data: Any = None) -> Dict[str, Any]:
        """构造成功结果"""
        return {
            "success": True,
            "result": result,
            "error": None,
            "data": data,
        }

    def _error(self, error: str) -> Dict[str, Any]:
        """构造失败结果"""
        return {
            "success": False,
            "result": "",
            "error": error,
            "data": None,
        }
