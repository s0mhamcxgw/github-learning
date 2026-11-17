"""
工具调用 Agent（ReAct 模式）
作用：让 LLM 能够自主选择和调用工具，完成需要"动手"的任务
ReAct = Reasoning + Acting（推理 + 行动）

工作流程：
1. 接收用户需求
2. LLM 分析需求，判断是否需要工具
3. 如需工具，选择工具并执行
4. 根据工具结果继续推理，可能需要多轮工具调用
5. 最终生成完整回答
"""
import json
from typing import Dict, Any, List, Optional
from tools.tool_manager import ToolManager
from core.llm_client import llm
from memory.manager import MemoryManager


class ToolCallingAgent:
    """工具调用 Agent（ReAct 模式）"""

    def __init__(self, memory: MemoryManager = None):
        self.memory = memory
        self.tool_manager = ToolManager()
        self.max_iterations = 15  # 最大工具调用轮数
        self.conversation_history: List[Dict[str, str]] = []

    def process(self, user_input: str) -> str:
        """
        处理用户需求，自动选择和调用工具

        Args:
            user_input: 用户输入

        Returns:
            最终回答
        """
        print(f"\n{'='*50}")
        print(f"  工具调用 Agent 启动（ReAct 模式）")
        print(f"  需求: {user_input[:50]}{'...' if len(user_input) > 50 else ''}")
        print(f"  可用工具: {len(self.tool_manager.get_available_tools())} 个")
        print(f"{'='*50}\n")

        # 重置对话历史
        self.conversation_history = []

        # 构建系统提示词
        system_prompt = self._build_system_prompt()

        # 添加用户输入
        self.conversation_history.append({"role": "user", "content": user_input})

        # ReAct 循环
        for iteration in range(1, self.max_iterations + 1):
            print(f"  --- 第 {iteration} 轮推理 ---\n")

            # 构建完整消息
            messages = [{"role": "system", "content": system_prompt}] + self.conversation_history

            # LLM 推理
            response = llm.chat_non_stream(messages)
            print(f"  [AI 推理]\n{response[:500]}{'...' if len(response) > 500 else ''}\n")

            # 解析响应，判断是否需要调用工具
            tool_call = self._parse_tool_call(response)

            if tool_call:
                # 执行工具
                tool_name = tool_call["tool"]
                tool_params = tool_call["params"]

                print(f"  [工具调用] {tool_name}")
                print(f"  [参数] {json.dumps(tool_params, ensure_ascii=False, indent=2)}\n")

                # 执行工具
                tool_result = self.tool_manager.execute_tool(tool_name, **tool_params)

                # 格式化工具结果
                result_text = self._format_tool_result(tool_result)
                print(f"  [工具结果]\n{result_text[:300]}{'...' if len(result_text) > 300 else ''}\n")

                # 将工具结果添加到对话历史
                self.conversation_history.append({"role": "assistant", "content": response})
                self.conversation_history.append({
                    "role": "user",
                    "content": f"工具执行结果：\n{result_text}\n\n请根据工具结果继续分析，如果已经获得足够信息，请给出最终回答。"
                })
            else:
                # 不需要工具，直接返回最终回答
                print(f"  [最终回答]\n")
                return response

        # 超过最大迭代次数，返回最后一次响应
        print(f"  [达到最大迭代次数，返回最终回答]\n")
        return self.conversation_history[-1]["content"] if self.conversation_history else "处理失败"

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        tools_description = self.tool_manager.get_tools_description()

        return f"""你是一个具备工具调用能力的智能助手。你可以通过调用工具来完成需要实际操作的任务。

{tools_description}

## 工作方式（ReAct 模式）

当用户提出需求时，你需要：
1. 分析需求，判断是否需要调用工具
2. 如果需要工具，严格按照以下格式输出工具调用：

```json
{{"tool": "工具名称", "params": {{"参数名": "参数值"}}}}
```

3. 工具执行后，你会收到工具结果，根据结果继续分析
4. 可能需要多轮工具调用，直到获得足够信息
5. 当信息足够时，直接给出最终回答（不需要再调用工具）

## 重要规则

- 只有在确实需要工具时才调用，简单问题直接回答
- 每次只调用一个工具
- 工具参数必须正确，文件路径必须是绝对路径
- 代码执行工具用于验证代码或运行脚本
- 文件读取工具用于查看本地文件内容
- 文件写入工具用于保存生成的内容
- 包安装工具用于安装缺失的 Python 库
- 命令执行工具用于执行系统命令
- 目录列表工具用于查看项目结构
- docx_writer 用于生成 Word 文档（论文/报告），xlsx_writer 用于生成 Excel 表格，pptx_writer 用于生成 PPT
- 生成文件请保存到：{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")}

## 输出格式

- 需要调用工具时：只输出 JSON 格式的工具调用，不要其他文字
- 不需要工具时：直接输出完整的回答
"""

    def _parse_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """
        解析 LLM 响应，提取工具调用

        Returns:
            工具调用字典 {"tool": "...", "params": {...}}，或 None
        """
        response = response.strip()

        # 尝试直接解析 JSON
        try:
            data = json.loads(response)
            if "tool" in data and "params" in data:
                return data
        except json.JSONDecodeError:
            pass

        # 尝试从 markdown 代码块中提取 JSON
        if "```json" in response:
            try:
                json_str = response.split("```json")[1].split("```")[0].strip()
                data = json.loads(json_str)
                if "tool" in data and "params" in data:
                    return data
            except (IndexError, json.JSONDecodeError):
                pass

        # 尝试从普通代码块中提取
        if "```" in response:
            try:
                json_str = response.split("```")[1].strip()
                if json_str.startswith("{"):
                    data = json.loads(json_str)
                    if "tool" in data and "params" in data:
                        return data
            except (IndexError, json.JSONDecodeError):
                pass

        return None

    def _format_tool_result(self, result: Dict[str, Any]) -> str:
        """格式化工具结果"""
        if result["success"]:
            return f"执行成功\n\n{result['result']}"
        else:
            return f"执行失败\n\n错误信息: {result['error']}"

    def get_tool_stats(self) -> Dict[str, Any]:
        """获取工具统计"""
        return self.tool_manager.get_stats()
