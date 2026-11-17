"""
办公场景 Agent
作用：专门处理办公文档相关需求，包括 Word/Excel/PPT 制作、汇报总结
"""
from agents.base import BaseSceneAgent
from core.prompt_loader import prompt_loader
from memory.manager import MemoryManager


class OfficeAgent(BaseSceneAgent):
    """办公场景 Agent"""

    def __init__(self, memory: MemoryManager = None):
        super().__init__(memory)
        self.scene_name = "办公"
        self.scene_description = "办公事务场景：Word/Excel/PPT文档处理、汇报总结"
        self.tools = [
            "Word撰写", "Excel制表", "PPT制作", "汇报提纲",
            "文案改写", "公文格式", "数据统计", "邮件撰写"
        ]
        self.acceptance_criteria = """
        办公场景验收标准：
        1. 内容完整，包含所有要求的模块
        2. 格式统一：字体、字号、行距、段落格式一致
        3. 数据准确，计算无误
        4. 逻辑清晰，层次分明，重点突出
        5. 可直接编辑使用
        6. PPT每页内容精炼，避免大段文字
        7. Excel公式可复用
        8. 附带使用说明
        """
        self.load_prompt()

    def load_prompt(self):
        self.system_prompt = prompt_loader.load("scenes/office.md")
        if not self.system_prompt:
            self.system_prompt = "你是一个专业的办公文档助手，擅长Word/Excel/PPT制作。"

    def process(self, user_input: str) -> str:
        """处理办公需求（专属流程：文档类型识别→结构设计→内容生成→格式校验→交付）"""
        print(f"\n{'='*50}")
        print(f"  办公 Agent 启动")
        print(f"  需求: {user_input[:50]}{'...' if len(user_input) > 50 else ''}")
        print(f"{'='*50}")

        # 第1步：文档类型识别
        self._stage_doc_type(user_input)

        # 第2步：结构设计
        self._stage_structure(user_input)

        # 第3步：内容生成
        self._stage_content(user_input)

        # 第4步：格式校验
        self._stage_format_review(user_input)

        # 第5步：交付
        return self._stage_delivery(user_input)

    def _stage_doc_type(self, user_input: str):
        self._print_stage("文档类型识别", "判断文档类型和使用场景")
        prompt = f"""分析以下办公需求，识别文档类型。

用户需求：{user_input}

请判断：
1. 文档类型：Word/Excel/PPT/其他
2. 使用场景：学业汇报/科研答辩/课程作业/工作总结/申请材料/其他
3. 目标受众：导师/同学/评审专家/领导/其他
4. 风格要求：学术/商务/简洁/详细/正式/活泼
5. 篇幅预估：页数/字数
6. 核心内容模块：需要包含哪些部分

请直接输出分析结果。"""
        result = self._call_llm(prompt)
        self._save_result("doc_type", result)
        print(f"    {result[:200]}...")

    def _stage_structure(self, user_input: str):
        self._print_stage("结构设计", "设计文档结构和内容框架")
        prompt = f"""基于以下需求，设计文档结构。

【用户需求】{user_input}
【文档类型分析】{self._get_result('doc_type')}

请设计：
1. 文档标题（2-3个备选）
2. 完整的内容结构（章节/页面/表格结构）
3. 每个部分的内容要点
4. 排版建议（字体、字号、配色、布局）
5. 如需PPT：每页的标题和核心内容
6. 如需Excel：表格列名和数据结构
7. 如需Word：标题层级和段落安排

请直接输出结构设计。"""
        result = self._call_llm(prompt)
        self._save_result("structure", result)
        print(f"    结构设计完成，{len(result)} 字符")

    def _stage_content(self, user_input: str):
        self._print_stage("内容生成", "生成完整的文档内容")
        prompt = f"""根据以下结构，生成完整的文档内容。

【用户需求】{user_input}
【文档结构】{self._get_result('structure')}

内容要求：
1. 内容完整，覆盖所有模块
2. 语言符合场景要求（学术/商务/正式）
3. 数据如有需要，请给出示例数据并标注"示例"
4. PPT每页内容精炼，要点化表达
5. Excel给出公式和示例数据
6. Word段落清晰，逻辑连贯

请直接输出完整的文档内容。"""
        result = self._call_llm(prompt)
        self._save_result("content", result)
        print(f"    内容生成完成，{len(result)} 字符")

    def _stage_format_review(self, user_input: str):
        self._print_stage("格式校验", "检查格式规范和内容完整性")
        prompt = f"""对以下文档进行格式校验和优化。

【用户需求】{user_input}
【文档内容】{self._get_result('content')}

检查清单：
1. 内容完整性：是否覆盖所有要求的模块
2. 格式统一性：字体、字号、行距、段落格式是否一致
3. 逻辑连贯性：内容是否层次分明、逻辑清晰
4. 数据准确性：如有数据，计算是否正确
5. 排版美观性：布局是否合理，重点是否突出
6. 可编辑性：是否可以直接复制到Word/Excel/PPT中使用
7. 场景适配性：是否符合使用场景和受众

请输出：
1. 校验报告
2. 优化建议
3. 优化后的文档内容"""
        result = self._call_llm(prompt)
        self._save_result("review", result)
        print(f"    格式校验完成，{len(result)} 字符")

    def _stage_delivery(self, user_input: str) -> str:
        self._print_stage("交付", "组装最终交付物")
        final_output = f"""
{'='*60}
  办公 Agent 交付物
{'='*60}

【用户需求】{user_input}

【文档类型分析】
{self._get_result('doc_type')}

【文档结构设计】
{self._get_result('structure')}

【文档内容】
{self._get_result('content')}

【格式校验与优化】
{self._get_result('review')}

{'='*60}
  交付说明
{'='*60}
- 文档内容可直接复制到对应软件（Word/Excel/PPT）中使用
- 格式可能需要根据学校/单位的具体模板进行微调
- 数据如为示例，请替换为真实数据
- PPT建议使用学校统一模板，内容可直接复制
- Excel公式已给出，可根据实际数据范围调整
"""
        self._save_result("final", final_output)
        return final_output

    def get_acceptance_criteria(self) -> str:
        return self.acceptance_criteria
