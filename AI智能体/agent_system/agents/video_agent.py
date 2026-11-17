"""
视频场景 Agent
作用：专门处理视频创作相关需求，包括脚本撰写、分镜设计、剪辑指导
"""
from agents.base import BaseSceneAgent
from core.prompt_loader import prompt_loader
from memory.manager import MemoryManager


class VideoAgent(BaseSceneAgent):
    """视频场景 Agent"""

    def __init__(self, memory: MemoryManager = None):
        super().__init__(memory)
        self.scene_name = "视频"
        self.scene_description = "视频创作场景：脚本撰写、分镜设计、剪辑指导"
        self.tools = [
            "脚本撰写", "分镜设计", "台词创作", "剪辑指导",
            "字幕文案", "配音稿", "封面设计", "标题简介"
        ]
        self.acceptance_criteria = """
        视频场景验收标准：
        1. 脚本完整：台词、分镜、时长标注、画面描述齐全
        2. 节奏合理：内容分配均匀，重点突出，时长符合要求
        3. 分镜清晰：每个镜头的画面、台词、时长、转场明确
        4. 配套齐全：字幕、配音稿、封面文案、标题简介
        5. 可执行性强：可按脚本直接拍摄或剪辑
        6. 贴合具体使用场景（答辩/作业/展示）
        7. 推荐合适的剪辑工具和技巧
        """
        self.load_prompt()

    def load_prompt(self):
        self.system_prompt = prompt_loader.load("scenes/video.md")
        if not self.system_prompt:
            self.system_prompt = "你是一个专业的视频创作助手，擅长脚本撰写和分镜设计。"

    def process(self, user_input: str) -> str:
        """处理视频需求（专属流程：场景定位→脚本框架→分镜设计→配套输出→交付）"""
        print(f"\n{'='*50}")
        print(f"  视频 Agent 启动")
        print(f"  需求: {user_input[:50]}{'...' if len(user_input) > 50 else ''}")
        print(f"{'='*50}")

        # 第1步：视频场景定位
        self._stage_scene定位(user_input)

        # 第2步：脚本框架设计
        self._stage_script_framework(user_input)

        # 第3步：分镜与台词设计
        self._stage_storyboard(user_input)

        # 第4步：配套内容输出
        self._stage_supporting(user_input)

        # 第5步：交付
        return self._stage_delivery(user_input)

    def _stage_scene定位(self, user_input: str):
        self._print_stage("场景定位", "分析视频类型、目标受众、时长要求")
        prompt = f"""分析以下视频创作需求。

用户需求：{user_input}

请分析：
1. 视频类型：答辩展示/课程作业/成果宣讲/实验记录/学习总结/其他
2. 目标受众：评审专家/导师/同学/公众
3. 时长要求：预估时长（如未指定，根据类型建议）
4. 核心内容：视频需要传达的核心信息
5. 风格定位：学术严谨/活泼生动/专业商务/简洁明了
6. 制作方式：真人出镜/录屏/动画/图文/混合
7. 剪辑工具：推荐使用剪映专业版还是Premiere Pro

请直接输出分析结果。"""
        result = self._call_llm(prompt)
        self._save_result("scene定位", result)
        print(f"    {result[:200]}...")

    def _stage_script_framework(self, user_input: str):
        self._print_stage("脚本框架", "设计视频整体结构和内容节奏")
        prompt = f"""基于以下需求，设计视频脚本框架。

【用户需求】{user_input}
【场景定位】{self._get_result('scene定位')}

请设计：
1. 视频标题（2-3个备选）
2. 整体结构：开头（吸引注意）→ 主体（内容展开）→ 结尾（总结升华）
3. 各部分时长分配
4. 内容要点：每个部分需要传达的核心信息
5. 节奏设计：哪里需要快节奏、哪里需要慢下来
6. 视觉元素建议：需要哪些画面、图表、动画
7. 背景音乐风格建议

请直接输出脚本框架。"""
        result = self._call_llm(prompt)
        self._save_result("framework", result)
        print(f"    脚本框架设计完成，{len(result)} 字符")

    def _stage_storyboard(self, user_input: str):
        self._print_stage("分镜设计", "设计详细分镜表和台词")
        prompt = f"""根据以下框架，设计详细的分镜表和台词。

【用户需求】{user_input}
【脚本框架】{self._get_result('framework')}

请输出分镜表，格式如下：

| 镜号 | 时长 | 画面描述 | 台词/旁白 | 字幕 | 转场 | 备注 |
|------|------|----------|-----------|------|------|------|
| 1 | 0:00-0:10 | ... | ... | ... | ... | ... |

要求：
1. 分镜完整，覆盖整个视频
2. 台词口语化，适合朗读
3. 画面描述具体，可直接拍摄或制作
4. 时长标注精确到秒
5. 转场方式明确（淡入淡出/滑动/缩放/硬切等）
6. 如涉及数据展示，给出图表建议

请直接输出分镜表。"""
        result = self._call_llm(prompt)
        self._save_result("storyboard", result)
        print(f"    分镜设计完成，{len(result)} 字符")

    def _stage_supporting(self, user_input: str):
        self._print_stage("配套输出", "生成字幕、配音稿、封面、标题简介")
        prompt = f"""为以下视频生成配套内容。

【用户需求】{user_input}
【分镜表】{self._get_result('storyboard')}

请输出：
1. 完整字幕文件（SRT格式，包含时间轴）
2. 配音稿（纯台词，方便录制，标注停顿和重音）
3. 封面设计建议（主标题、副标题、视觉元素、配色）
4. 视频标题（3个备选，适合平台发布）
5. 视频简介（100字以内）
6. 标签/关键词（5-10个）
7. 剪辑注意事项（5条关键提醒）

请直接输出配套内容。"""
        result = self._call_llm(prompt)
        self._save_result("supporting", result)
        print(f"    配套内容生成完成，{len(result)} 字符")

    def _stage_delivery(self, user_input: str) -> str:
        self._print_stage("交付", "组装最终交付物")
        final_output = f"""
{'='*60}
  视频 Agent 交付物
{'='*60}

【用户需求】{user_input}

【视频场景定位】
{self._get_result('scene定位')}

【脚本框架】
{self._get_result('framework')}

【分镜表与台词】
{self._get_result('storyboard')}

【配套内容】
{self._get_result('supporting')}

{'='*60}
  交付说明
{'='*60}
- 脚本和分镜可直接用于拍摄或剪辑
- 字幕文件可导入剪映/Premiere使用
- 配音稿可直接用于录制
- 封面建议可用于设计封面图
- 剪辑工具推荐：入门用剪映专业版，进阶用Premiere Pro
- 制作过程中如有问题，可随时告诉我具体卡点
"""
        self._save_result("final", final_output)
        return final_output

    def get_acceptance_criteria(self) -> str:
        return self.acceptance_criteria
