"""
系统工具：包管理、命令执行、目录列表
"""
import os
import subprocess
from typing import Dict, Any, List
from tools.base import BaseTool


class PackageInstallTool(BaseTool):
    """Python 包安装工具"""

    def __init__(self):
        super().__init__()
        self.tool_name = "package_install"
        self.tool_description = "在虚拟环境中安装 Python 第三方库，使用 pip 安装。"
        self.parameters = {
            "package_name": {
                "type": "str",
                "description": "要安装的包名（如 pandas、numpy、scikit-learn）",
                "required": True,
            },
            "version": {
                "type": "str",
                "description": "指定版本号（如 2.0.0），不填则安装最新版",
                "required": False,
            },
        }
        self.pip_path = r"E:\ai智能体开发\.venv\Scripts\pip.exe"
        if not os.path.exists(self.pip_path):
            self.pip_path = "pip"

    def execute(self, package_name: str, version: str = None, **kwargs) -> Dict[str, Any]:
        """安装 Python 包"""
        param_error = self.validate_params(package_name=package_name)
        if param_error:
            return self._error(param_error)

        # 构造安装命令
        if version:
            install_target = f"{package_name}=={version}"
        else:
            install_target = package_name

        try:
            result = subprocess.run(
                [self.pip_path, "install", install_target],
                capture_output=True,
                text=True,
                timeout=120,
                encoding='utf-8',
                errors='replace',
            )

            output = result.stdout + result.stderr
            if result.returncode == 0:
                result_text = f"包安装成功: {install_target}\n\n【安装输出】\n{output[-500:]}" if len(output) > 500 else f"包安装成功: {install_target}\n\n【安装输出】\n{output}"
                return self._success(result_text, data={"output": output, "package": install_target})
            else:
                return self._error(f"包安装失败: {install_target}\n\n【错误输出】\n{output[-500:]}")

        except subprocess.TimeoutExpired:
            return self._error(f"包安装超时（120秒）: {install_target}")
        except Exception as e:
            return self._error(f"安装出错: {type(e).__name__}: {e}")


class CommandTool(BaseTool):
    """系统命令执行工具"""

    def __init__(self):
        super().__init__()
        self.tool_name = "command_executor"
        self.tool_description = "执行 Windows 系统命令（如 dir、cd、echo 等），返回命令输出。"
        self.parameters = {
            "command": {
                "type": "str",
                "description": "要执行的系统命令",
                "required": True,
            },
            "timeout": {
                "type": "int",
                "description": "超时时间（秒），默认30秒",
                "required": False,
            },
        }
        # 安全限制：禁止执行的命令
        self.blocked_commands = ["rmdir /s", "del /f", "format", "diskpart", "reg delete", "shutdown"]

    def execute(self, command: str, timeout: int = 30, **kwargs) -> Dict[str, Any]:
        """执行系统命令"""
        param_error = self.validate_params(command=command)
        if param_error:
            return self._error(param_error)

        # 安全检查
        command_lower = command.lower()
        for blocked in self.blocked_commands:
            if blocked in command_lower:
                return self._error(f"安全限制：禁止执行危险命令: {blocked}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace',
            )

            output = result.stdout
            error_output = result.stderr
            return_code = result.returncode

            full_output = output
            if error_output:
                full_output += f"\n【错误输出】\n{error_output}"

            if return_code == 0:
                result_text = f"命令执行成功（返回码: 0）\n命令: {command}\n\n【输出】\n{full_output}" if full_output else f"命令执行成功，无输出\n命令: {command}"
                return self._success(result_text, data={"output": full_output, "returncode": return_code})
            else:
                result_text = f"命令执行失败（返回码: {return_code}）\n命令: {command}\n\n【输出】\n{full_output}"
                return self._success(result_text, data={"output": full_output, "returncode": return_code})

        except subprocess.TimeoutExpired:
            return self._error(f"命令执行超时（{timeout}秒）: {command}")
        except Exception as e:
            return self._error(f"命令执行出错: {type(e).__name__}: {e}")


class DirectoryListTool(BaseTool):
    """目录列表工具"""

    def __init__(self):
        super().__init__()
        self.tool_name = "directory_list"
        self.tool_description = "列出指定目录下的文件和子目录，用于查看项目结构。"
        self.parameters = {
            "directory": {
                "type": "str",
                "description": "要列出的目录路径",
                "required": True,
            },
            "recursive": {
                "type": "bool",
                "description": "是否递归列出子目录，默认 False",
                "required": False,
            },
        }

    def execute(self, directory: str, recursive: bool = False, **kwargs) -> Dict[str, Any]:
        """列出目录内容"""
        param_error = self.validate_params(directory=directory)
        if param_error:
            return self._error(param_error)

        if not os.path.exists(directory):
            return self._error(f"目录不存在: {directory}")

        if not os.path.isdir(directory):
            return self._error(f"路径不是目录: {directory}")

        try:
            items = []
            if recursive:
                for root, dirs, files in os.walk(directory):
                    level = root.replace(directory, '').count(os.sep)
                    indent = '  ' * level
                    items.append(f"{indent}{os.path.basename(root)}/")
                    subindent = '  ' * (level + 1)
                    for file in files:
                        items.append(f"{subindent}{file}")
            else:
                for item in sorted(os.listdir(directory)):
                    item_path = os.path.join(directory, item)
                    if os.path.isdir(item_path):
                        items.append(f"[目录] {item}/")
                    else:
                        size = os.path.getsize(item_path)
                        items.append(f"[文件] {item} ({size} 字节)")

            result_text = f"目录内容: {directory}\n共 {len(items)} 项\n\n" + "\n".join(items)
            return self._success(result_text, data={"items": items, "count": len(items)})

        except Exception as e:
            return self._error(f"列出目录失败: {type(e).__name__}: {e}")
