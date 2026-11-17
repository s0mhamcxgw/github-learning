"""
五阶闭环工作流
作用：实现智能体的核心差异化能力——工程化流水线作业
五阶：需求解析 → 方案设计 → 全量落地 → 校验优化 → 复盘归档

每个阶段都调用 LLM 完成特定任务，输出结构化结果，
前一阶段的结果作为后一阶段的输入，形成完整闭环。
"""
import json
from typing import Dict, Any
from workflows.base import BaseWorkflow
from workflows.scene_classifier import SceneClassifier
from memory.manager import MemoryManager


class FiveStageWorkflow(BaseWorkflow):
    """五阶闭环工作流"""

    def __init__(self, memory: MemoryManager = None):
        super().__init__(memory)
        self.workflow_name = "五阶闭环工作流"
        self.scene_classifier = SceneClassifier()
        self.current_scene = None
        self.scene_config = None

    def run(self, user_input: str) -> str:
        """
        执行完整的五阶闭环工作流

        Args:
            user_input: 用户输入

        Returns:
            最终交付文本
        """
        print(f"\n{'='*60}")
        print(f"  启动五阶闭环工作流")
        print(f"  用户输入: {user_input[:50]}{'...' if len(user_input) > 50 else ''}")
        print(f"{'='*60}")

        # 场景识别（工作流前置步骤）
        self.current_scene, self.scene_config = self.scene_classifier.classify(user_input)

        # 第一阶：需求解析
        self._stage1_analyze(user_input)

        # 第二阶：方案设计
        self._stage2_design(user_input)

        # 第三阶：全量落地
        self._stage3_execute(user_input)

        # 第四阶：校验优化
        self._stage4_verify(user_input)

        # 第五阶：复盘归档
        final_output = self._stage5_archive(user_input)

        return final_output

    # ========== 第一阶：需求解析 ==========

    def _stage1_analyze(self, user_input: str):
        """第一阶：需求精准解析"""
        self._print_stage(1, "需求精准解析", "定目标、抓核心、判定场景、明确交付标准")

        prompt = f"""请对以下用户需求进行深度解析，输出结构化的需求解析卡。

用户需求：{user_input}

所属场景：{self.current_scene}
场景说明：{self.scene_config['description']}

请按以下格式输出需求解析卡：

## 需求解析卡

### 1. 核心任务
（用一句话概括用户真正想要什么）

### 2. 场景判定
- 主场景：{self.current_scene}
- 子场景：（如：数据预处理/论文开题/PPT制作等）

### 3. 交付标准
- 交付物类型：（代码/文档/表格/PPT/脚本等）
- 质量要求：（可运行/格式规范/内容完整等）
- 风格要求：（学术/商务/简洁/详细等）

### 4. 环境约束
- 编程环境：Python 3.13.2 + PyCharm CE 2024.3
- API：阿里云百炼 qwen3.8-max
- 其他约束：（根据需求识别）

### 5. 需求漏洞与补充建议
（用户需求中不明确的地方，以及需要补充的信息）

### 6. 风险预判
（可能遇到的问题：技术难点/格式问题/数据问题等）

请直接输出解析卡，不要其他解释。"""

        result = self._call_llm(prompt)
        self._save_result("stage1_analysis", result)
        self._print_stage_result(result)

    # ========== 第二阶：方案设计 ==========

    def _stage2_design(self, user_input: str):
        """第二阶：工程方案设计"""
        self._print_stage(2, "工程方案设计", "定架构、定流程、规划步骤、预判风险")

        analysis = self._get_result("stage1_analysis")

        prompt = f"""基于以下需求解析，设计完整的执行方案。

【用户需求】
{user_input}

【需求解析卡】
{analysis}

【场景】{self.current_scene}

请设计执行方案，包含以下内容：

## 执行方案

### 1. 整体架构
（完成这个任务需要哪些模块/部分，它们之间的关系）

### 2. 执行步骤
（分步骤列出，每步包含：步骤名、具体操作、预期产出）
步骤1：...
步骤2：...
步骤3：...

### 3. 核心要点
（这个任务最关键的3-5个要点，必须注意）

### 4. 风险与应对
| 风险 | 可能性 | 影响 | 应对方案 |
|------|--------|------|----------|
| ... | ... | ... | ... |

### 5. 优化方向
（完成基础版后，可以从哪些方面进一步优化）

### 6. 工具选择
（需要用到哪些工具/库/软件，为什么选择）

请直接输出方案，不要其他解释。"""

        result = self._call_llm(prompt)
        self._save_result("stage2_design", result)
        self._print_stage_result(result)

    # ========== 第三阶：全量落地 ==========

    def _stage3_execute(self, user_input: str):
        """第三阶：全量内容落地"""
        self._print_stage(3, "全量内容落地", "出成品、可即用、按方案输出完整交付物")

        analysis = self._get_result("stage1_analysis")
        design = self._get_result("stage2_design")

        prompt = f"""严格按照以下方案，输出完整的成品交付物。

【用户需求】
{user_input}

【需求解析】
{analysis}

【执行方案】
{design}

【场景】{self.current_scene}

【环境约束】
- Python 3.13.2 + PyCharm CE 2024.3
- 代码中禁止明文写 API Key，使用 os.environ.get() 读取
- 所有包安装命令使用虚拟环境：E:\\ai智能体开发\\.venv\\Scripts\\pip.exe

请输出完整的成品，要求：
1. 严格按照执行方案的步骤输出
2. 内容完整，可直接使用，无需用户二次大幅修改
3. 代码必须可运行，包含必要的注释和错误处理
4. 文档格式规范，结构清晰
5. 附带使用说明和注意事项

请直接输出成品内容。"""

        result = self._call_llm(prompt)
        self._save_result("stage3_output", result)
        self._print_stage_result(result)

    # ========== 第四阶：校验优化 ==========

    def _stage4_verify(self, user_input: str):
        """第四阶：全维度校验优化"""
        self._print_stage(4, "全维度校验优化", "保质量、无问题、自检+优化+验收清单")

        analysis = self._get_result("stage1_analysis")
        output = self._get_result("stage3_output")
        acceptance = self.scene_config.get("acceptance_criteria", "")

        prompt = f"""对以下成品进行全维度校验和优化。

【用户需求】
{user_input}

【需求解析】
{analysis}

【成品内容】
{output}

【场景验收标准】
{acceptance}

请完成以下工作：

## 校验报告

### 1. 逐项验收
对照验收标准，逐项检查：
- 标准1：通过/不通过（说明原因）
- 标准2：通过/不通过（说明原因）
...

### 2. 发现的问题
（列出所有问题：格式错误/逻辑漏洞/内容缺失/安全隐患等）

### 3. 优化建议
（针对每个问题，给出具体的优化方案）

## 优化后的成品

（在原成品基础上进行优化，输出完整的优化后版本。如果原成品已经很好，可以说明"无需优化"并保留原内容。）

## 最终验收清单
| 检查项 | 状态 | 备注 |
|--------|------|------|
| ... | ✅/❌ | ... |

请直接输出校验报告和优化后的成品。"""

        result = self._call_llm(prompt)
        self._save_result("stage4_verified", result)
        self._print_stage_result(result)

    # ========== 第五阶：复盘归档 ==========

    def _stage5_archive(self, user_input: str) -> str:
        """第五阶：复盘迭代归档"""
        self._print_stage(5, "复盘迭代归档", "可复用、可迭代、总结经验、沉淀资产")

        analysis = self._get_result("stage1_analysis")
        design = self._get_result("stage2_design")
        output = self._get_result("stage3_output")
        verified = self._get_result("stage4_verified")

        prompt = f"""对本次任务进行复盘和归档。

【用户需求】
{user_input}

【场景】{self.current_scene}

【最终成品】
{verified}

请完成以下复盘：

## 复盘报告

### 1. 任务完成情况
- 目标达成度：（百分比+说明）
- 交付物质量：（优秀/良好/合格+说明）
- 耗时与效率：（评估）

### 2. 成功经验
（本次任务中做得好的地方，可复用的方法）

### 3. 问题与教训
（遇到的问题，以及如何避免下次再犯）

### 4. 可复用模板
（从本次任务中提炼出的可复用模板/框架/代码片段，供后续类似任务使用）

### 5. 后续拓展方向
（这个任务还可以如何深化或拓展）

### 6. 用户偏好记录
（从本次交互中观察到的用户偏好，建议存入长期记忆）

请直接输出复盘报告。"""

        review = self._call_llm(prompt)
        self._save_result("stage5_review", review)

        # 沉淀到长期记忆
        if self.memory:
            self._archive_to_memory(user_input, review)

        # 组装最终输出
        final_output = self._assemble_final_output(user_input, review)

        print(f"\n{'='*60}")
        print(f"  五阶闭环工作流执行完成！")
        print(f"  场景：{self.current_scene} | 阶段：5/5 全部完成")
        print(f"{'='*60}\n")

        return final_output

    def _archive_to_memory(self, user_input: str, review: str):
        """将复盘结果沉淀到长期记忆"""
        try:
            # 提取用户偏好
            self.memory.long_term.add_experience(
                title=f"[{self.current_scene}] {user_input[:30]}",
                content=review[:500],
                scenario=self.current_scene,
                outcome="工作流执行完成"
            )
        except Exception:
            pass  # 归档失败不影响主流程

    def _assemble_final_output(self, user_input: str, review: str) -> str:
        """组装最终交付输出"""
        verified = self._get_result("stage4_verified")

        output = f"""
{'='*60}
  最终交付 | {self.current_scene}场景
{'='*60}

【用户需求】
{user_input}

【交付物】
{verified}

{'='*60}
  复盘总结
{'='*60}
{review}

【工作流执行记录】
- 场景识别：{self.current_scene}
- 阶段1 需求解析：完成
- 阶段2 方案设计：完成
- 阶段3 全量落地：完成
- 阶段4 校验优化：完成
- 阶段5 复盘归档：完成
- 记忆沉淀：已自动保存到长期记忆
"""
        return output
