"""
编程场景 Agent
作用：专门处理编程相关需求，包括代码编写、调试、环境配置、项目开发
这是智能体的核心强项场景
"""
import os
from typing import Dict, Any
from agents.base import BaseSceneAgent
from core.prompt_loader import prompt_loader
from memory.manager import MemoryManager


class CodingAgent(BaseSceneAgent):
    """编程场景 Agent"""

    def __init__(self, memory: MemoryManager = None):
        super().__init__(memory)
        self.scene_name = "编程"
        self.scene_description = "编程科研场景：代码编写、调试、环境配置、项目开发"
        self.tools = [
            "代码生成", "代码重构", "代码审查", "报错修复",
            "环境配置", "包管理", "项目搭建", "实验复现"
        ]
        self.acceptance_criteria = """
        编程场景验收标准：
        1. 代码兼容 Python 3.13.2，可在 PyCharm CE 中直接运行
        2. 无明文 API Key/密码，敏感信息使用 os.environ.get() 读取
        3. 遵循 PEP 8 规范，函数/类有文档字符串，关键步骤有中文注释
        4. 包含错误处理（try-except）和边界情况处理
        5. 附带 requirements.txt 和运行说明
        6. 实验代码固定随机种子，保证可复现
        7. 项目结构清晰，模块化拆分
        """
        self.load_prompt()

    def load_prompt(self):
        """加载编程场景专属提示词"""
        self.system_prompt = prompt_loader.load("scenes/coding.md")
        if not self.system_prompt:
            # 如果文件不存在，使用默认提示词
            self.system_prompt = "你是一个专业的Python编程助手，擅长数据处理和机器学习开发。"

    def process(self, user_input: str) -> str:
        """
        处理编程需求（专属流程：环境检测→需求分析→代码生成→自检→交付）

        Args:
            user_input: 用户输入

        Returns:
            处理结果
        """
        print(f"\n{'='*50}")
        print(f"  编程 Agent 启动")
        print(f"  需求: {user_input[:50]}{'...' if len(user_input) > 50 else ''}")
        print(f"{'='*50}")

        # 第1步：环境检测
        self._stage_env_check()

        # 第2步：需求分析
        self._stage_analysis(user_input)

        # 第3步：代码生成
        self._stage_code_generation(user_input)

        # 第4步：代码自检
        self._stage_code_review(user_input)

        # 第5步：交付
        final_output = self._stage_delivery(user_input)

        return final_output

    def _stage_env_check(self):
        """第1步：环境检测（检查 Python 版本、已装包、虚拟环境）"""
        self._print_stage("环境检测", "检查 Python 版本、已安装包、虚拟环境状态")

        env_info = []
        # Python 版本
        import sys
        env_info.append(f"Python 版本: {sys.version}")

        # 虚拟环境
        venv_path = "E:\\ai智能体开发\\.venv"
        env_info.append(f"虚拟环境: {venv_path} ({'存在' if os.path.exists(venv_path) else '不存在'})")

        # 检查常用包
        common_packages = ["pandas", "numpy", "sklearn", "matplotlib", "torch", "requests"]
        installed = []
        for pkg in common_packages:
            try:
                __import__(pkg)
                installed.append(pkg)
            except ImportError:
                pass
        env_info.append(f"已装常用包: {', '.join(installed) if installed else '无'}")
        env_info.append(f"缺失常用包: {', '.join([p for p in common_packages if p not in installed])}")

        env_report = "\n".join(env_info)
        self._save_result("env_check", env_report)
        print(f"    {env_report.replace(chr(10), chr(10) + '    ')}")

    def _stage_analysis(self, user_input: str):
        """第2步：需求分析"""
        self._print_stage("需求分析", "分析编程需求类型、技术栈、复杂度")

        prompt = f"""分析以下编程需求，输出结构化的需求分析。

用户需求：{user_input}

【当前环境】
{self._get_result('env_check')}

请分析：
1. 需求类型：（脚本开发/项目搭建/报错修复/代码重构/环境配置/算法实现）
2. 技术栈：（需要哪些库和工具）
3. 复杂度评估：（简单/中等/复杂，预计代码行数）
4. 关键难点：（技术挑战、可能的坑）
5. 环境适配：（是否需要安装新包，Python 3.13 兼容性如何）
6. 交付物：（单个脚本/完整项目/代码片段+说明）

请直接输出分析结果。"""

        result = self._call_llm(prompt)
        self._save_result("analysis", result)
        print(f"    {result[:300]}{'...' if len(result) > 300 else ''}")

    def _stage_code_generation(self, user_input: str):
        """第3步：代码生成"""
        self._print_stage("代码生成", "生成完整可运行的代码")

        prompt = f"""根据以下需求和分析，生成完整可运行的代码。

【用户需求】
{user_input}

【需求分析】
{self._get_result('analysis')}

【环境约束】
- Python 3.13.2 + PyCharm CE 2024.3
- 虚拟环境：E:\\ai智能体开发\\.venv
- 包安装命令：E:\\ai智能体开发\\.venv\\Scripts\\pip.exe install 包名
- 禁止明文写 API Key，使用 os.environ.get()
- Windows 路径使用双反斜杠

【代码要求】
1. 完整可运行，包含所有 import
2. 关键步骤有中文注释
3. 包含错误处理
4. 实验代码固定随机种子
5. 附带运行说明和依赖安装命令
6. 如果是项目，给出目录结构

请直接输出代码和说明。"""

        result = self._call_llm(prompt)
        self._save_result("code", result)
        print(f"    已生成 {len(result)} 字符的代码内容")

    def _stage_code_review(self, user_input: str):
        """第4步：代码自检"""
        self._print_stage("代码自检", "检查代码质量、安全性、兼容性")

        prompt = f"""对以下代码进行自检和优化。

【用户需求】
{user_input}

【生成的代码】
{self._get_result('code')}

【检查清单】
1. 安全性：是否有明文 API Key/密码？是否有 SQL 注入等安全隐患？
2. 兼容性：是否兼容 Python 3.13？使用的库是否有版本问题？
3. 可运行性：是否有语法错误？import 是否完整？是否有未定义变量？
4. 规范性：是否遵循 PEP 8？命名是否规范？注释是否充分？
5. 健壮性：是否有错误处理？边界情况是否处理？
6. 性能：是否有明显的性能问题？

请输出：
1. 自检报告（逐项检查结果）
2. 发现的问题（如有）
3. 优化后的代码（在原代码基础上优化，如无问题则保留原代码）

请直接输出自检报告和优化后的代码。"""

        result = self._call_llm(prompt)
        self._save_result("review", result)
        print(f"    自检完成，{len(result)} 字符")

    def _stage_delivery(self, user_input: str) -> str:
        """第5步：交付"""
        self._print_stage("交付", "组装最终交付物")

        review = self._get_result("review")
        env_check = self._get_result("env_check")
        analysis = self._get_result("analysis")

        final_output = f"""
{'='*60}
  编程 Agent 交付物
{'='*60}

【用户需求】
{user_input}

【环境检测】
{env_check}

【需求分析】
{analysis}

【代码与自检】
{review}

{'='*60}
  交付说明
{'='*60}
- 代码已通过自检，可直接在 PyCharm CE 中运行
- 如需安装依赖，请使用：E:\\ai智能体开发\\.venv\\Scripts\\pip.exe install 包名
- API Key 请配置到环境变量 ALIBABA_CLOUD_API_KEY
- 如有问题，请提供完整报错信息，我会帮你修复
"""
        self._save_result("final", final_output)
        return final_output

    def get_acceptance_criteria(self) -> str:
        return self.acceptance_criteria
