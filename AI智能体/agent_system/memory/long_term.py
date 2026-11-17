"""
长期记忆模块
作用：永久保存用户偏好、常见问题FAQ、历史经验、知识库
存储：分类 JSON 文件，保存在 data/memory/long_term/ 目录
检索：支持关键词匹配，智能体回答时自动检索相关记忆
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from config.settings import settings


class LongTermMemory:
    """长期记忆：知识库管理"""

    def __init__(self):
        self.base_dir = os.path.join(settings.MEMORY_DIR, "long_term")
        os.makedirs(self.base_dir, exist_ok=True)

        # 各类记忆的文件路径
        self.preferences_file = os.path.join(self.base_dir, "preferences.json")
        self.faq_file = os.path.join(self.base_dir, "faq.json")
        self.experiences_file = os.path.join(self.base_dir, "experiences.json")
        self.knowledge_file = os.path.join(self.base_dir, "knowledge.json")

        # 初始化文件
        self._init_files()

    def _init_files(self):
        """初始化各类记忆文件（如果不存在）"""
        default_data = {
            "preferences": {"items": [], "updated_at": None},
            "faq": {"items": [], "updated_at": None},
            "experiences": {"items": [], "updated_at": None},
            "knowledge": {"items": [], "updated_at": None}
        }

        file_map = {
            self.preferences_file: "preferences",
            self.faq_file: "faq",
            self.experiences_file: "experiences",
            self.knowledge_file: "knowledge"
        }

        for filepath, key in file_map.items():
            if not os.path.exists(filepath):
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(default_data[key], f, ensure_ascii=False, indent=2)

    # ========== 用户偏好 ==========

    def add_preference(self, category: str, key: str, value: str, note: str = ""):
        """
        添加用户偏好

        Args:
            category: 偏好分类（如"编程"、"论文"、"办公"、"通用"）
            key: 偏好项（如"主力IDE"、"代码注释语言"）
            value: 偏好值（如"PyCharm"、"中文"）
            note: 备注说明
        """
        data = self._load(self.preferences_file)
        # 检查是否已存在相同的 key，存在则更新
        for item in data["items"]:
            if item["key"] == key and item["category"] == category:
                item["value"] = value
                item["note"] = note
                item["updated_at"] = datetime.now().isoformat()
                data["updated_at"] = datetime.now().isoformat()
                self._save(self.preferences_file, data)
                print(f"[长期记忆] 偏好已更新: [{category}] {key} = {value}")
                return

        data["items"].append({
            "id": len(data["items"]) + 1,
            "category": category,
            "key": key,
            "value": value,
            "note": note,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })
        data["updated_at"] = datetime.now().isoformat()
        self._save(self.preferences_file, data)
        print(f"[长期记忆] 偏好已保存: [{category}] {key} = {value}")

    def get_preferences(self, category: str = None) -> List[Dict]:
        """获取用户偏好，可按分类筛选"""
        data = self._load(self.preferences_file)
        if category:
            return [item for item in data["items"] if item["category"] == category]
        return data["items"]

    # ========== FAQ 常见问题 ==========

    def add_faq(self, question: str, answer: str, category: str = "通用", tags: List[str] = None):
        """
        添加常见问题

        Args:
            question: 问题
            answer: 答案/解决方案
            category: 分类
            tags: 标签列表
        """
        data = self._load(self.faq_file)
        data["items"].append({
            "id": len(data["items"]) + 1,
            "question": question,
            "answer": answer,
            "category": category,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "hit_count": 0
        })
        data["updated_at"] = datetime.now().isoformat()
        self._save(self.faq_file, data)
        print(f"[长期记忆] FAQ已添加: {question[:30]}...")

    def search_faq(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        关键词检索 FAQ

        Args:
            query: 查询关键词
            top_k: 返回最相关的前K条

        Returns:
            匹配的 FAQ 列表
        """
        data = self._load(self.faq_file)
        if not data["items"]:
            return []

        query_words = set(query.lower().split())
        scored = []

        for item in data["items"]:
            # 简单关键词匹配：问题、答案、标签中包含的关键词数
            text = f"{item['question']} {item['answer']} {' '.join(item.get('tags', []))}".lower()
            score = sum(1 for word in query_words if word in text)
            if score > 0:
                scored.append((score, item))

        # 按匹配度排序
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [item for _, item in scored[:top_k]]

        # 更新命中次数
        for item in results:
            item["hit_count"] = item.get("hit_count", 0) + 1
        self._save(self.faq_file, data)

        return results

    # ========== 历史经验 ==========

    def add_experience(self, title: str, content: str, scenario: str = "通用", outcome: str = ""):
        """
        添加历史经验沉淀

        Args:
            title: 经验标题
            content: 经验内容（问题+解决方案+教训）
            scenario: 适用场景（编程/论文/办公/视频）
            outcome: 结果/效果
        """
        data = self._load(self.experiences_file)
        data["items"].append({
            "id": len(data["items"]) + 1,
            "title": title,
            "content": content,
            "scenario": scenario,
            "outcome": outcome,
            "created_at": datetime.now().isoformat()
        })
        data["updated_at"] = datetime.now().isoformat()
        self._save(self.experiences_file, data)
        print(f"[长期记忆] 经验已沉淀: {title}")

    def get_experiences(self, scenario: str = None) -> List[Dict]:
        """获取历史经验，可按场景筛选"""
        data = self._load(self.experiences_file)
        if scenario:
            return [item for item in data["items"] if item["scenario"] == scenario]
        return data["items"]

    # ========== 知识库 ==========

    def add_knowledge(self, topic: str, content: str, source: str = "用户交互"):
        """
        添加知识点

        Args:
            topic: 知识主题
            content: 知识内容
            source: 来源（用户交互/文档/网络/经验总结）
        """
        data = self._load(self.knowledge_file)
        data["items"].append({
            "id": len(data["items"]) + 1,
            "topic": topic,
            "content": content,
            "source": source,
            "created_at": datetime.now().isoformat()
        })
        data["updated_at"] = datetime.now().isoformat()
        self._save(self.knowledge_file, data)
        print(f"[长期记忆] 知识已保存: {topic}")

    def search_knowledge(self, query: str, top_k: int = 3) -> List[Dict]:
        """关键词检索知识库"""
        data = self._load(self.knowledge_file)
        if not data["items"]:
            return []

        query_words = set(query.lower().split())
        scored = []

        for item in data["items"]:
            text = f"{item['topic']} {item['content']}".lower()
            score = sum(1 for word in query_words if word in text)
            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:top_k]]

    # ========== 综合检索 ==========

    def retrieve_relevant(self, query: str, top_k: int = 5) -> Dict[str, List]:
        """
        综合检索：根据用户查询，从所有长期记忆中检索相关信息

        Args:
            query: 用户查询
            top_k: 每类返回的最大条数

        Returns:
            包含 preferences/faq/experiences/knowledge 的字典
        """
        return {
            "preferences": self.get_preferences(),  # 偏好总是全部返回
            "faq": self.search_faq(query, top_k),
            "experiences": self.get_experiences(),  # 经验总是返回（数量不会太多）
            "knowledge": self.search_knowledge(query, top_k)
        }

    def get_stats(self) -> Dict:
        """获取长期记忆统计信息"""
        return {
            "preferences_count": len(self.get_preferences()),
            "faq_count": len(self._load(self.faq_file)["items"]),
            "experiences_count": len(self.get_experiences()),
            "knowledge_count": len(self._load(self.knowledge_file)["items"])
        }

    # ========== 内部工具 ==========

    def _load(self, filepath: str) -> Dict:
        """加载 JSON 文件"""
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, filepath: str, data: Dict):
        """保存 JSON 文件"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
