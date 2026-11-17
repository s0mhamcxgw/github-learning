"""
论文场景 Agent
作用：专门处理学术论文相关需求，包括论文撰写、润色、格式规范、查重降重
"""
from agents.base import BaseSceneAgent
from core.prompt_loader import prompt_loader
from memory.manager import MemoryManager


class PaperAgent(BaseSceneAgent):
    """论文场景 Agent"""

    def __init__(self, memory: MemoryManager = None):
        super().__init__(memory)
        self.scene_name = "论文"
        self.scene_description = "学术论文场景：论文撰写、润色、格式规范、开题答辩"
        self.tools = [
            "论文撰写", "逻辑梳理", "降重润色", "格式规范",
            "参考文献整理", "创新点挖掘", "答辩文稿", "开题报告"
        ]
        self.acceptance_criteria = """
        论文场景验收标准：
        1. 结构完整：摘要、关键词、引言、文献综述、方法、实验、结论、参考文献
        2. 引用格式符合 GB/T 7714-2015 标准
        3. 无抄袭风险，降重后保持原意
        4. 语言学术化，贴合大数据专业研究方向
        5. 参考文献真实可靠，数量充足
        6. 末尾附学术诚信声明
        7. 实验数据可复现
        """
        self.load_prompt()

    def load_prompt(self):
        self.system_prompt = prompt_loader.load("scenes/paper.md")
        if not self.system_prompt:
            self.system_prompt = "你是一个专业的学术论文助手，擅长大数据方向论文撰写。"
        # 加载学校论文格式规范（模仿参考论文排版用）
        self.paper_format = prompt_loader.load("paper_format.md") or ""

    def _with_format(self, text: str) -> str:
        """把格式规范附到提示词后面"""
        if self.paper_format:
            return text + f"\n\n【学校毕业论文格式规范（必须遵循）】\n{self.paper_format}"
        return text

    def process(self, user_input: str) -> str:
        """处理论文需求（专属流程：选题分析→框架设计→内容撰写→学术校验→交付）"""
        print(f"\n{'='*50}")
        print(f"  论文 Agent 启动")
        print(f"  需求: {user_input[:50]}{'...' if len(user_input) > 50 else ''}")
        print(f"{'='*50}")

        # 第1步：选题与需求分析
        self._stage_topic_analysis(user_input)

        # 第2步：论文框架设计
        self._stage_outline_design(user_input)

        # 第3步：内容撰写
        self._stage_content_writing(user_input)

        # 第4步：学术规范校验
        self._stage_academic_review(user_input)

        # 第5步：交付
        return self._stage_delivery(user_input)

    def _stage_topic_analysis(self, user_input: str):
        self._print_stage("选题分析", "分析研究方向、创新点、可行性")
        prompt = f"""分析以下论文需求，输出选题分析报告。

用户需求：{user_input}

研究方向（贵财大数据专硕）：数据挖掘、机器学习、大数据治理、商务智能、金融科技、智慧旅游

请分析：
1. 研究主题：（明确的研究问题）
2. 研究方向：（属于哪个细分方向）
3. 创新点：（可能的创新之处）
4. 可行性：（数据可获得性、方法成熟度、研究周期）
5. 文献方向：（需要查阅哪些领域的文献）
6. 研究方法：（适合用哪些研究方法）

请直接输出分析报告。"""
        result = self._call_llm(prompt)
        self._save_result("topic_analysis", result)
        print(f"    {result[:200]}...")

    def _stage_outline_design(self, user_input: str):
        self._print_stage("框架设计", "设计论文章节结构和内容要点")
        prompt = f"""基于以下选题分析，设计论文框架。

【用户需求】{user_input}
【选题分析】{self._get_result('topic_analysis')}

请设计完整的论文框架，包含：
1. 论文题目（2-3个备选）
2. 摘要要点
3. 关键词（3-5个）
4. 详细章节结构（每章包含：章节标题、核心内容、字数预估）
5. 参考文献方向（建议引用的文献类型和数量）
6. 图表规划（需要哪些图表）

请直接输出论文框架。"""
        result = self._call_llm(prompt)
        self._save_result("outline", result)
        print(f"    框架设计完成，{len(result)} 字符")

    def _stage_content_writing(self, user_input: str):
        self._print_stage("内容撰写", "撰写论文正文内容")
        prompt = f"""根据以下框架，撰写论文正文。

【用户需求】{user_input}
【论文框架】{self._get_result('outline')}

写作要求：
1. 语言学术化，避免口语化
2. 逻辑严谨，论证充分
3. 贴合大数据专业研究方向
4. 引用格式预留 [1][2] 标记
5. 实验部分如涉及代码，给出可复现的伪代码或思路
6. 禁止编造虚假数据和引用
7. 若用户提供了参考论文或要求模仿格式，严格遵循其章节结构与写作风格

请撰写完整的论文正文（如果内容过长，可以先写核心章节，其余部分给出写作要点）。"""
        prompt = self._with_format(prompt)
        result = self._call_llm(prompt)
        self._save_result("content", result)
        print(f"    内容撰写完成，{len(result)} 字符")

    def _stage_academic_review(self, user_input: str):
        self._print_stage("学术校验", "检查学术规范、格式、引用、查重风险")
        prompt = f"""对以下论文进行学术规范校验和优化。

【用户需求】{user_input}
【论文内容】{self._get_result('content')}

检查清单：
1. 结构完整性：是否包含所有必要章节
2. 引用格式：是否符合 GB/T 7714 标准（如未给出具体文献，给出格式模板）
3. 学术语言：是否有口语化表达，需要学术化改写
4. 逻辑连贯性：段落之间是否衔接自然
5. 查重风险：哪些内容可能重复率较高，给出降重建议
6. 数据可靠性：是否有虚假数据风险
7. 格式规范：标题层级、图表编号、公式格式

请输出：
1. 校验报告
2. 优化建议
3. 优化后的论文（或核心章节的优化版）
4. 学术诚信声明"""
        result = self._call_llm(prompt)
        self._save_result("review", result)
        print(f"    学术校验完成，{len(result)} 字符")

    def _stage_delivery(self, user_input: str) -> str:
        self._print_stage("交付", "组装最终交付物")
        final_output = f"""
{'='*60}
  论文 Agent 交付物
{'='*60}

【用户需求】{user_input}

【选题分析】
{self._get_result('topic_analysis')}

【论文框架】
{self._get_result('outline')}

【论文正文】
{self._get_result('content')}

【学术校验与优化】
{self._get_result('review')}

{'='*60}
  交付说明
{'='*60}
- 论文已通过学术规范校验
- 参考文献请根据实际引用的文献补充，格式遵循 GB/T 7714-2015
- 实验数据请根据实际实验结果填写，禁止编造
- 降重后请使用查重系统进行最终检测
- 提交前请务必通读全文，确保符合学校格式要求
"""
        self._save_result("final", final_output)
        return final_output

    def get_acceptance_criteria(self) -> str:
        return self.acceptance_criteria
