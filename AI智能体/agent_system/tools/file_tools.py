"""
文件读写工具
作用：读取本地文件内容、写入内容到文件
"""
import os
from typing import Dict, Any
from tools.base import BaseTool


class FileReadTool(BaseTool):
    """文件读取工具"""

    def __init__(self):
        super().__init__()
        self.tool_name = "file_read"
        self.tool_description = "读取本地文本文件内容，支持 .py、.txt、.md、.json、.csv 等文本文件。"
        self.parameters = {
            "file_path": {
                "type": "str",
                "description": "要读取的文件绝对路径",
                "required": True,
            },
            "encoding": {
                "type": "str",
                "description": "文件编码，默认 utf-8",
                "required": False,
            },
        }

    def execute(self, file_path: str, encoding: str = "utf-8", **kwargs) -> Dict[str, Any]:
        """读取文件"""
        param_error = self.validate_params(file_path=file_path)
        if param_error:
            return self._error(param_error)

        if not os.path.exists(file_path):
            return self._error(f"文件不存在: {file_path}")

        if not os.path.isfile(file_path):
            return self._error(f"路径不是文件: {file_path}")

        try:
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()

            file_size = os.path.getsize(file_path)
            result_text = f"文件读取成功: {file_path}\n文件大小: {file_size} 字节\n内容长度: {len(content)} 字符\n\n【文件内容】\n{content}"
            return self._success(result_text, data={"content": content, "size": file_size})
        except Exception as e:
            return self._error(f"读取文件失败: {type(e).__name__}: {e}")


class FileWriteTool(BaseTool):
    """文件写入工具"""

    def __init__(self):
        super().__init__()
        self.tool_name = "file_write"
        self.tool_description = "将内容写入到本地文件，支持创建新文件或覆盖已有文件。"
        self.parameters = {
            "file_path": {
                "type": "str",
                "description": "要写入的文件绝对路径",
                "required": True,
            },
            "content": {
                "type": "str",
                "description": "要写入的文件内容",
                "required": True,
            },
            "encoding": {
                "type": "str",
                "description": "文件编码，默认 utf-8",
                "required": False,
            },
            "append": {
                "type": "bool",
                "description": "是否追加模式，默认覆盖",
                "required": False,
            },
        }

    def execute(self, file_path: str, content: str, encoding: str = "utf-8",
                append: bool = False, **kwargs) -> Dict[str, Any]:
        """写入文件"""
        param_error = self.validate_params(file_path=file_path, content=content)
        if param_error:
            return self._error(param_error)

        try:
            # 确保目录存在
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

            mode = 'a' if append else 'w'
            with open(file_path, mode, encoding=encoding) as f:
                f.write(content)

            file_size = os.path.getsize(file_path)
            mode_text = "追加" if append else "写入"
            result_text = f"文件{mode_text}成功: {file_path}\n文件大小: {file_size} 字节\n内容长度: {len(content)} 字符"
            return self._success(result_text, data={"size": file_size, "path": file_path})
        except Exception as e:
            return self._error(f"写入文件失败: {type(e).__name__}: {e}")
