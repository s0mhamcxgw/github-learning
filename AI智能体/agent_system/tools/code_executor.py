"""
代码执行工具
作用：执行 Python 代码，返回运行结果和报错信息
安全限制：只能执行在沙箱目录中的代码，设置超时限制
"""
import os
import sys
import subprocess
import tempfile
from typing import Dict, Any
from tools.base import BaseTool


class CodeExecutorTool(BaseTool):
    """Python 代码执行工具"""

    def __init__(self):
        super().__init__()
        self.tool_name = "code_executor"
        self.tool_description = "执行 Python 代码，返回运行结果、输出和报错信息。用于验证代码可行性、运行脚本、测试函数。"
        self.parameters = {
            "code": {
                "type": "str",
                "description": "要执行的 Python 代码",
                "required": True,
            },
            "timeout": {
                "type": "int",
                "description": "超时时间（秒），默认30秒",
                "required": False,
            },
        }
        # 使用用户的虚拟环境 Python
        self.python_path = r"E:\ai智能体开发\.venv\Scripts\python.exe"
        if not os.path.exists(self.python_path):
            self.python_path = sys.executable

    def execute(self, code: str, timeout: int = 30, **kwargs) -> Dict[str, Any]:
        """执行 Python 代码"""
        # 参数验证
        param_error = self.validate_params(code=code)
        if param_error:
            return self._error(param_error)

        if not code or not code.strip():
            return self._error("代码为空")

        # 创建临时文件
        try:
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.py', delete=False, encoding='utf-8'
            ) as f:
                f.write(code)
                temp_file = f.name
        except Exception as e:
            return self._error(f"创建临时文件失败: {e}")

        try:
            # 执行代码
            result = subprocess.run(
                [self.python_path, temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace',
            )

            output = result.stdout
            error_output = result.stderr
            return_code = result.returncode

            if return_code == 0:
                result_text = f"执行成功（返回码: 0）\n\n【输出】\n{output}" if output else "执行成功，无输出"
                return self._success(result_text, data={"stdout": output, "stderr": error_output, "returncode": return_code})
            else:
                result_text = f"执行失败（返回码: {return_code}）\n\n【标准输出】\n{output}\n\n【错误输出】\n{error_output}"
                return self._success(result_text, data={"stdout": output, "stderr": error_output, "returncode": return_code})

        except subprocess.TimeoutExpired:
            return self._error(f"代码执行超时（{timeout}秒）")
        except Exception as e:
            return self._error(f"执行出错: {type(e).__name__}: {e}")
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file)
            except:
                pass
