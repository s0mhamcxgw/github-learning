"""
短期记忆模块
作用：保存对话历史，支持多轮对话上下文、会话切换、历史回顾
存储：每个会话一个 JSON 文件，保存在 data/memory/sessions/ 目录
"""
import os
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from config.settings import settings


class ShortTermMemory:
    """短期记忆：对话历史管理"""

    def __init__(self):
        self.session_dir = os.path.join(settings.MEMORY_DIR, "sessions")
        os.makedirs(self.session_dir, exist_ok=True)
        self.current_session_id = None
        self.messages: List[Dict[str, str]] = []

    def create_session(self, title: str = "新对话") -> str:
        """
        创建新会话

        Args:
            title: 会话标题

        Returns:
            会话ID
        """
        # 用时间戳生成会话ID
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session_id = session_id
        self.messages = []

        # 保存会话元信息
        session_data = {
            "session_id": session_id,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "message_count": 0,
            "messages": []
        }
        self._save_session(session_data)
        print(f"[短期记忆] 新会话已创建: {session_id} ({title})")
        return session_id

    def load_session(self, session_id: str) -> bool:
        """
        加载历史会话

        Args:
            session_id: 会话ID

        Returns:
            是否加载成功
        """
        filepath = os.path.join(self.session_dir, f"{session_id}.json")
        if not os.path.exists(filepath):
            print(f"[短期记忆] 会话不存在: {session_id}")
            return False

        with open(filepath, "r", encoding="utf-8") as f:
            session_data = json.load(f)

        self.current_session_id = session_id
        self.messages = session_data.get("messages", [])
        print(f"[短期记忆] 会话已加载: {session_id} ({len(self.messages)} 条消息)")
        return True

    def add_message(self, role: str, content: str):
        """
        添加一条消息到当前会话

        Args:
            role: 角色（system/user/assistant）
            content: 内容
        """
        self.messages.append({"role": role, "content": content})
        self._auto_save()

    def get_messages(self, include_system: bool = True) -> List[Dict[str, str]]:
        """
        获取对话历史

        Args:
            include_system: 是否包含 system 消息

        Returns:
            消息列表
        """
        if include_system:
            return self.messages.copy()
        return [m for m in self.messages if m["role"] != "system"]

    def get_recent_messages(self, n: int = 10) -> List[Dict[str, str]]:
        """获取最近 n 条消息"""
        return self.messages[-n:].copy()

    def clear(self):
        """清空当前会话消息（保留 system 提示词）"""
        system_msgs = [m for m in self.messages if m["role"] == "system"]
        self.messages = system_msgs
        self._auto_save()
        print("[短期记忆] 对话历史已清空（保留系统提示词）")

    def list_sessions(self) -> List[Dict]:
        """列出所有历史会话"""
        sessions = []
        if not os.path.exists(self.session_dir):
            return sessions
        for filename in sorted(os.listdir(self.session_dir), reverse=True):
            if filename.endswith(".json"):
                filepath = os.path.join(self.session_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    sessions.append({
                        "session_id": data.get("session_id", filename.replace(".json", "")),
                        "title": data.get("title", "未命名"),
                        "created_at": data.get("created_at", ""),
                        "message_count": data.get("message_count", 0)
                    })
                except Exception:
                    continue
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """删除指定会话"""
        filepath = os.path.join(self.session_dir, f"{session_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"[短期记忆] 会话已删除: {session_id}")
            return True
        return False

    def _auto_save(self):
        """自动保存当前会话"""
        if not self.current_session_id:
            return
        session_data = {
            "session_id": self.current_session_id,
            "title": self._infer_title(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "message_count": len(self.messages),
            "messages": self.messages
        }
        self._save_session(session_data)

    def _infer_title(self) -> str:
        """从第一条用户消息推断会话标题"""
        for msg in self.messages:
            if msg["role"] == "user":
                # 取前20个字作为标题
                content = msg["content"].strip().replace("\n", " ")
                return content[:20] + "..." if len(content) > 20 else content
        return "新对话"

    def _save_session(self, session_data: Dict):
        """保存会话到文件"""
        filepath = os.path.join(self.session_dir, f"{session_data['session_id']}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
