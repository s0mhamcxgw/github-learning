"""
工具管理器
作用：注册、管理和调度所有工具
"""
from typing import Dict, List, Optional, Any
from tools.base import BaseTool
from tools.code_executor import CodeExecutorTool
from tools.file_tools import FileReadTool, FileWriteTool
from tools.system_tools import PackageInstallTool, CommandTool, DirectoryListTool
from tools.doc_tools import DocxWriterTool, XlsxWriterTool, PptxWriterTool, FileInfoTool
from tools.paper_tools import PdfExtractTool, PaperWriterTool


class ToolManager:
    """工具管理器"""

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """注册默认工具"""
        default_tools = [
            CodeExecutorTool(),
            FileReadTool(),
            FileWriteTool(),
            PackageInstallTool(),
            CommandTool(),
            DirectoryListTool(),
            DocxWriterTool(),
            XlsxWriterTool(),
            PptxWriterTool(),
            FileInfoTool(),
            PdfExtractTool(),
            PaperWriterTool(),
        ]
        for tool in default_tools:
            self.register_tool(tool)

    def register_tool(self, tool: BaseTool):
        """注册工具"""
        self.tools[tool.tool_name] = tool
        print(f"[工具管理器] 已注册工具: {tool.tool_name}")

    def unregister_tool(self, tool_name: str):
        """注销工具"""
        if tool_name in self.tools:
            del self.tools[tool_name]
            print(f"[工具管理器] 已注销工具: {tool_name}")

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self.tools.get(tool_name)

    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        执行指定工具

        Args:
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            执行结果
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "success": False,
                "result": "",
                "error": f"工具不存在: {tool_name}",
                "data": None,
            }

        if not tool.enabled:
            return {
                "success": False,
                "result": "",
                "error": f"工具已禁用: {tool_name}",
                "data": None,
            }

        print(f"[工具管理器] 执行工具: {tool_name}")
        return tool.execute(**kwargs)

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取所有可用工具的信息（用于 LLM 选择）"""
        return [
            tool.get_info()
            for tool in self.tools.values()
            if tool.enabled
        ]

    def get_tools_description(self) -> str:
        """获取工具描述文本（用于注入到 LLM 提示词中）"""
        tools = self.get_available_tools()
        lines = ["可用工具列表："]
        for i, tool in enumerate(tools, 1):
            lines.append(f"\n{i}. {tool['name']}")
            lines.append(f"   描述: {tool['description']}")
            lines.append(f"   参数:")
            for param_name, param_def in tool['parameters'].items():
                required = "必填" if param_def.get('required') else "可选"
                lines.append(f"     - {param_name} ({param_def['type']}, {required}): {param_def['description']}")
        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        """获取工具统计"""
        return {
            "已注册工具数": len(self.tools),
            "可用工具数": len([t for t in self.tools.values() if t.enabled]),
            "工具列表": list(self.tools.keys()),
        }
