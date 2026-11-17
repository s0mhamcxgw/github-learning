"""
记忆管理器
作用：统一调度短期记忆和长期记忆，实现：
1. 对话前自动注入相关长期记忆到上下文
2. 对话后自动从对话中提取偏好、FAQ、经验
3. 记忆的增删改查统一入口
"""
import json
from typing import List, Dict, Optional
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from core.llm_client import llm


class MemoryManager:
    """记忆管理器：统一调度短期和长期记忆"""

    def __init__(self):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()

    def start_new_session(self, title: str = "新对话"):
        """开始新会话"""
        self.short_term.create_session(title)

    def load_session(self, session_id: str) -> bool:
        """加载历史会话"""
        return self.short_term.load_session(session_id)

    def add_user_message(self, content: str):
        """添加用户消息"""
        self.short_term.add_message("user", content)

    def add_assistant_message(self, content: str):
        """添加助手消息"""
        self.short_term.add_message("assistant", content)

    def add_system_message(self, content: str):
        """添加系统消息"""
        self.short_term.add_message("system", content)

    def get_context_messages(self, user_input: str) -> List[Dict[str, str]]:
        """
        获取完整的对话上下文（包含系统提示词 + 注入的长期记忆 + 历史对话）

        Args:
            user_input: 当前用户输入（用于检索相关长期记忆）

        Returns:
            完整的消息列表，可直接传给 LLM
        """
        # 1. 获取基础消息（含系统提示词）
        messages = self.short_term.get_messages(include_system=True)

        # 2. 检索相关长期记忆
        relevant = self.long_term.retrieve_relevant(user_input)

        # 3. 构建记忆注入提示词
        memory_context = self._build_memory_context(relevant)
        if memory_context:
            # 在系统提示词后、用户消息前注入记忆上下文
            # 找到第一个非 system 消息的位置
            insert_idx = 0
            for i, msg in enumerate(messages):
                if msg["role"] != "system":
                    insert_idx = i
                    break
            else:
                insert_idx = len(messages)

            messages.insert(insert_idx, {
                "role": "system",
                "content": memory_context
            })

        return messages

    def _build_memory_context(self, relevant: Dict) -> str:
        """
        构建记忆注入的上下文文本

        Args:
            relevant: 检索到的相关记忆

        Returns:
            记忆上下文文本
        """
        parts = []
        parts.append("【长期记忆上下文】以下是关于用户的已知信息和历史经验，请在回答时参考：")

        # 用户偏好
        if relevant["preferences"]:
            parts.append("\n【用户偏好】")
            for p in relevant["preferences"]:
                parts.append(f"- [{p['category']}] {p['key']}: {p['value']}")

        # 相关 FAQ
        if relevant["faq"]:
            parts.append("\n【相关常见问题】")
            for f in relevant["faq"]:
                parts.append(f"- Q: {f['question']}")
                parts.append(f"  A: {f['answer'][:100]}...")

        # 历史经验
        if relevant["experiences"]:
            parts.append("\n【历史经验】")
            for e in relevant["experiences"][-3:]:  # 最多显示最近3条
                parts.append(f"- [{e['scenario']}] {e['title']}: {e['content'][:80]}...")

        # 相关知识
        if relevant["knowledge"]:
            parts.append("\n【相关知识库】")
            for k in relevant["knowledge"]:
                parts.append(f"- {k['topic']}: {k['content'][:100]}...")

        if len(parts) > 1:
            return "\n".join(parts)
        return ""

    def extract_and_store(self, user_input: str, assistant_response: str):
        """
        从对话中自动提取有价值的信息并存入长期记忆
        （使用 LLM 进行提取，提取失败不影响主流程）

        Args:
            user_input: 用户输入
            assistant_response: 助手回复
        """
        try:
            # 构建提取提示词
            extract_prompt = f"""请从以下对话中提取有价值的信息，以JSON格式返回。

用户输入：{user_input[:500]}
助手回复：{assistant_response[:500]}

请提取以下内容（如果没有则返回空数组）：
1. preferences: 用户表达的偏好、习惯、要求（格式：{{"category": "分类", "key": "偏好项", "value": "偏好值", "note": "备注"}}）
2. faq: 可以沉淀为常见问题的问答对（格式：{{"question": "问题", "answer": "答案", "category": "分类", "tags": ["标签"]}}）
3. experiences: 值得记录的经验教训（格式：{{"title": "标题", "content": "内容", "scenario": "场景", "outcome": "结果"}}）

只返回JSON，不要其他文字。格式：{{"preferences": [], "faq": [], "experiences": []}}"""

            messages = [{"role": "user", "content": extract_prompt}]
            result = llm.chat_non_stream(messages)

            # 解析 JSON（处理可能的 markdown 包裹）
            result = result.strip()
            if result.startswith("```"):
                result = result.split("\n", 1)[1] if "\n" in result else result
                result = result.rsplit("```", 1)[0] if "```" in result else result

            data = json.loads(result)

            # 存储提取的信息
            for p in data.get("preferences", []):
                if all(k in p for k in ["category", "key", "value"]):
                    self.long_term.add_preference(
                        p["category"], p["key"], p["value"], p.get("note", "")
                    )

            for f in data.get("faq", []):
                if all(k in f for k in ["question", "answer"]):
                    self.long_term.add_faq(
                        f["question"], f["answer"],
                        f.get("category", "通用"), f.get("tags", [])
                    )

            for e in data.get("experiences", []):
                if all(k in e for k in ["title", "content"]):
                    self.long_term.add_experience(
                        e["title"], e["content"],
                        e.get("scenario", "通用"), e.get("outcome", "")
                    )

        except Exception as e:
            # 提取失败不影响主流程，静默处理
            pass

    def list_sessions(self) -> List[Dict]:
        """列出所有历史会话"""
        return self.short_term.list_sessions()

    def clear_current_session(self):
        """清空当前会话"""
        self.short_term.clear()

    def get_memory_stats(self) -> Dict:
        """获取记忆统计"""
        long_stats = self.long_term.get_stats()
        sessions = self.short_term.list_sessions()
        return {
            "短期记忆": {
                "当前会话": self.short_term.current_session_id,
                "历史会话数": len(sessions),
                "当前消息数": len(self.short_term.messages)
            },
            "长期记忆": long_stats
        }
