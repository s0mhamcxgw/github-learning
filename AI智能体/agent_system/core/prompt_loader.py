"""
提示词加载模块
作用：从文件加载系统提示词，支持多场景提示词切换
"""
import os
from config.settings import settings


class PromptLoader:
    """系统提示词加载器"""

    def __init__(self, prompt_dir: str = None):
        self.prompt_dir = prompt_dir or settings.SYSTEM_PROMPT_DIR

    def load(self, filename: str = "system_prompt.md") -> str:
        """
        加载指定的系统提示词文件

        Args:
            filename: 提示词文件名，默认 system_prompt.md

        Returns:
            提示词文本内容
        """
        filepath = os.path.join(self.prompt_dir, filename)
        if not os.path.exists(filepath):
            print(f"[警告] 提示词文件不存在: {filepath}")
            return ""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"[提示词] 已加载: {filename} ({len(content)} 字符)")
        return content

    def list_prompts(self) -> list:
        """列出所有可用的提示词文件"""
        if not os.path.exists(self.prompt_dir):
            return []
        return [f for f in os.listdir(self.prompt_dir) if f.endswith(".md")]


# 全局提示词加载器
prompt_loader = PromptLoader()
