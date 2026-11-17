"""
自主任务执行引擎（TaskAgent）V6.0
作用：真正实现"一句话完成工作"——像专业 AI 助手一样：
  1. 规划：把一句话需求拆解成可执行的任务计划
  2. 执行：自动循环调用工具（写文件/跑代码/生成文档/装包），直到完成
  3. 验证：自动检查产出文件是否真实生成
  4. 交付：汇总执行过程 + 产出文件清单 + 使用说明

与旧工作流的区别：
  - 五阶工作流：纯文字流水线，只"说"不"做"
  - 场景Agent：基于提示词的虚拟分身，只"说"不"做"
  - TaskAgent：真实执行工具，产出可交付文件（Word/Excel/PPT/代码/文档）
"""
import os
import json
import re
from typing import Dict, Any, List, Generator, Optional
from tools.tool_manager import ToolManager
from core.llm_client import llm
from memory.manager import MemoryManager
from config.settings import settings

# 可交付文件的扩展名（用于自动识别产出物）
_DELIVERABLE_EXTS = {'.docx', '.xlsx', '.xls', '.pptx', '.pdf', '.py', '.md', '.txt', '.csv', '.json', '.html'}


class TaskAgent:
    """自主任务执行引擎"""

    def __init__(self, memory: MemoryManager = None):
        self.memory = memory
        self.tool_manager = ToolManager()
        self.max_iterations = 20          # 最大工具调用轮数
        self.output_dir = os.path.join(settings.BASE_DIR, "outputs")
        os.makedirs(self.output_dir, exist_ok=True)
        self.files_produced: List[str] = []
        self.steps_log: List[str] = []

    # ========== 主入口 ==========

    def process(self, user_input: str, plan: str = "") -> Generator:
        """
        执行一个完整任务（生成器，逐步产出进度事件）

        Args:
            user_input: 用户的一句话需求
            plan: 可选的预设计划（由场景Agent/工作流传入），为空则自动规划

        Yields:
            {"type": "plan", "content": 任务计划}
            {"type": "step", "content": 正在执行的步骤说明}
            {"type": "tool_call", "content": 工具调用信息}
            {"type": "tool_result", "content": 工具结果}
            {"type": "done", "content": 最终交付总结, "files": [...], "steps": [...]}
        """
        self.files_produced = []
        self.steps_log = []
        conversation: List[Dict[str, str]] = []

        # ---- 第1步：规划 ----
        plan_text = plan if plan else self._make_plan(user_input)
        self.steps_log.append("规划：" + plan_text[:200])
        yield {"type": "plan", "content": plan_text}

        # ---- 第2步：执行循环（ReAct） ----
        system_prompt = self._build_system_prompt(plan_text)
        conversation.append({"role": "user", "content": f"用户需求：{user_input}\n\n任务计划：{plan_text}\n\n请按计划执行。"})

        for iteration in range(1, self.max_iterations + 1):
            messages = [{"role": "system", "content": system_prompt}] + conversation[-10:]
            response = llm.chat_non_stream(messages)
            response = response.strip()

            decision = self._parse_decision(response)

            if decision and decision.get("tool"):
                # 调用工具
                tool_name = decision["tool"]
                tool_params = decision.get("params", {})
                self.steps_log.append(f"调用工具 {tool_name}: {json.dumps(tool_params, ensure_ascii=False)[:150]}")

                yield {"type": "tool_call", "content": f"**调用工具** `{tool_name}`\n参数：{json.dumps(tool_params, ensure_ascii=False)}"}

                tool_result = self.tool_manager.execute_tool(tool_name, **tool_params)
                result_text = self._format_tool_result(tool_result)
                # 截断工具结果防止上下文爆炸
                result_text_short = result_text[:3000]
                if len(result_text) > 3000:
                    result_text_short += f"\n...（结果过长，已截断，共 {len(result_text)} 字符）"

                self.steps_log.append(f"工具 {tool_name} 结果: {result_text[:120]}")
                yield {"type": "tool_result", "content": f"**工具结果**（{tool_name}）：\n```\n{result_text_short}\n```"}

                # 记录产出文件
                self._collect_produced_files(tool_name, tool_params, tool_result)

                conversation.append({"role": "assistant", "content": response})
                conversation.append({
                    "role": "user",
                    "content": f"工具 {tool_name} 执行结果：\n{result_text_short}\n\n根据结果继续执行，如果任务全部完成，输出完成指令。"
                })
            elif decision and decision.get("done"):
                # 任务完成
                self.steps_log.append("任务完成")
                final_text = decision["done"]
                break
            else:
                # 无法解析为工具调用——视为最终回答
                self.steps_log.append("AI 直接给出最终回答")
                final_text = response
                break
        else:
            final_text = "已达到最大执行轮数，任务可能未完全完成。"

        # ---- 第3步：验证产出文件 ----
        verified = self._verify_files()

        # ---- 第4步：交付总结 ----
        deliver = self._make_delivery(final_text, verified)
        yield {"type": "done", "content": deliver, "files": self.files_produced, "steps": list(self.steps_log)}

    # ========== 规划 ==========

    def _make_plan(self, user_input: str) -> str:
        """LLM 生成任务计划"""
        prompt = f"""你是任务规划专家。请把用户的一句话需求拆解成清晰可执行的步骤计划。

用户需求：{user_input}

输出要求（直接输出计划文本，不要 JSON，不要解释）：
1. 【目标】用一句话说明要交付什么
2. 【步骤】分步骤列出执行方案（3-8步），每步说明做什么
3. 【产出物】说明最终要生成什么文件（如 Word 论文、Excel 表格、Python 代码等）
4. 【注意】说明可能遇到的问题和注意事项

计划要具体、可执行，让执行者知道每一步该做什么。"""

        try:
            plan = llm.chat_non_stream([{"role": "user", "content": prompt}])
            return plan.strip()[:2000]
        except Exception as e:
            return f"【目标】{user_input}\n【步骤】1. 分析需求 2. 生成内容 3. 保存文件\n【产出物】根据需求确定"

    # ========== 系统提示词 ==========

    def _build_system_prompt(self, plan_text: str) -> str:
        """构建执行循环的系统提示词"""
        tools_desc = self.tool_manager.get_tools_description()
        return f"""你是一个具备自主执行能力的智能体，可以调用工具真正完成任务（写文件、跑代码、生成 Word/Excel/PPT）。

【任务计划】
{plan_text}

【输出目录】
所有生成的文件请保存到：{self.output_dir}（绝对路径），文件名用中文或英文均可。

【可用工具】
{tools_desc}

【执行规则】
1. 按计划逐步执行，每轮只做一件事。
2. 需要调用工具时，只输出一行 JSON（不要 markdown 代码块，不要其他文字）：
{{"tool": "工具名称", "params": {{"参数名": "参数值"}}}}
3. 收到工具结果后继续下一步。
4. 写论文/报告 → 用 docx_writer；做数据表 → 用 xlsx_writer；做PPT → 用 pptx_writer；写代码 → 先 file_write 保存 .py，再用 code_executor 运行验证。
5. 所有文件路径必须是绝对路径，且放在输出目录 {self.output_dir} 下。
6. 全部步骤完成后，输出一行 JSON（同样不要其他文字）：
{{"done": "最终交付总结：说明完成了什么、产出了哪些文件（列出完整绝对路径）、如何使用"}}
7. 如果某工具调用失败，分析错误并换一种方式重试（如先安装依赖、先建目录）。
8. 简单任务（如只需要回答不需要动手）可以直接输出 {{"done": "..."}}。

【论文写作规则（用户要求写论文/模仿论文时）】
- 写本科毕业论文 Word：用 paper_writer 工具（mode=create 一次 + mode=append 分章追加，多次调用写出长论文）。
- paper_writer 会自动生成学校页眉、封面、声明页；cover_info 参数传入论文题目/学号/姓名/班级/专业/学院/导师/日期。
- 需要模仿参考论文时：先用 pdf_extract 工具读取参考 PDF，掌握其章节结构、写作风格、格式要求后再动笔。
- 论文结构与格式遵循 config/prompts/paper_format.md（贵州财经大学本科毕业论文格式规范）。
"""

    # ========== 决策解析 ==========

    def _parse_decision(self, response: str) -> Optional[Dict[str, Any]]:
        """解析 LLM 决策：工具调用 或 完成"""
        response = response.strip()

        # 直接 JSON
        try:
            data = json.loads(response)
            if "tool" in data or "done" in data:
                return data
        except json.JSONDecodeError:
            pass

        # 提取 ```json ... ``` 或 ``` ... ``` 中的 JSON
        for fence in ["```json", "```"]:
            if fence in response:
                try:
                    json_str = response.split(fence)[1].split("```")[0].strip()
                    data = json.loads(json_str)
                    if "tool" in data or "done" in data:
                        return data
                except (IndexError, json.JSONDecodeError):
                    pass

        # 宽松提取：找第一个 { 到最后一个 }
        try:
            start, end = response.find("{"), response.rfind("}")
            if start >= 0 and end > start:
                data = json.loads(response[start:end + 1])
                if "tool" in data or "done" in data:
                    return data
        except json.JSONDecodeError:
            pass

        return None

    def _format_tool_result(self, result: Dict[str, Any]) -> str:
        """格式化工具结果"""
        if result["success"]:
            return f"执行成功\n\n{result['result']}"
        else:
            return f"执行失败\n\n错误信息: {result['error']}"

    # ========== 产出文件收集与验证 ==========

    def _collect_produced_files(self, tool_name: str, params: Dict[str, Any], result: Dict[str, Any]):
        """从工具调用中收集产出文件"""
        path = params.get("file_path") or params.get("path")
        if isinstance(path, str) and path.lower().endswith(tuple(_DELIVERABLE_EXTS)):
            if os.path.exists(path) and os.path.getsize(path) > 0:
                if path not in self.files_produced:
                    self.files_produced.append(path)
        # 从结果中提取路径
        if result.get("data"):
            d = result["data"]
            if isinstance(d, dict):
                p = d.get("path")
                if isinstance(p, str) and os.path.exists(p) and p not in self.files_produced:
                    self.files_produced.append(p)

    def _verify_files(self) -> List[str]:
        """验证产出文件是否真实存在且非空"""
        verified = []
        for f in self.files_produced:
            try:
                r = self.tool_manager.execute_tool("file_info", file_path=f)
                if r["success"]:
                    verified.append(f"✅ {f}（{os.path.getsize(f)} 字节）")
                else:
                    verified.append(f"❌ {f}（{r['error']}）")
            except Exception:
                verified.append(f"❌ {f}（验证失败）")
        return verified

    # ========== 交付总结 ==========

    def _make_delivery(self, final_text: str, verified: List[str]) -> str:
        """组装最终交付文本"""
        parts = [final_text.strip()]

        if self.files_produced:
            parts.append("\n\n**产出文件：**")
            if verified:
                parts.extend(f"- {v}" for v in verified)
            else:
                parts.extend(f"- {f}" for f in self.files_produced)

        parts.append(f"\n\n**输出目录：** `{self.output_dir}`")
        return "\n".join(parts)

    # ========== 统计 ==========

    def get_task_stats(self) -> Dict[str, Any]:
        """获取任务执行统计"""
        return {
            "输出目录": self.output_dir,
            "本轮产出文件数": len(self.files_produced),
            "本轮执行步骤数": len(self.steps_log),
            "最大迭代轮数": self.max_iterations,
        }
