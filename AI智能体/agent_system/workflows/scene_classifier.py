"""
场景识别器
作用：根据用户输入自动判断所属场景（编程/论文/办公/视频），
并返回对应的场景配置（系统提示词补充、验收标准、处理策略）
"""
import json
from typing import Dict, Tuple
from core.llm_client import llm


class SceneClassifier:
    """场景识别器"""

    # 场景定义
    SCENES = {
        "编程": {
            "keywords": ["代码", "程序", "python", "pycharm", "vscode", "bug", "报错",
                        "函数", "类", "算法", "数据处理", "机器学习", "模型", "爬虫",
                        "环境配置", "安装", "依赖", "api", "接口", "脚本", "调试"],
            "description": "编程科研场景：代码编写、调试、环境配置、项目开发",
            "acceptance_criteria": """
            编程场景验收标准：
            1. 代码兼容 Python 3.13.2，可在 PyCharm CE 中运行
            2. 无明文 API Key/密码，敏感信息使用环境变量
            3. 遵循 PEP 8 规范，关键步骤有注释
            4. 包含错误处理和边界情况处理
            5. 附带运行说明和依赖安装命令
            """
        },
        "论文": {
            "keywords": ["论文", "开题", "文献", "综述", "摘要", "引用", "参考文献",
                        "查重", "降重", "期刊", "毕业", "学位", "研究方法", "实验",
                        "学术", "格式", "答辩"],
            "description": "学术论文场景：论文撰写、润色、格式规范、开题答辩",
            "acceptance_criteria": """
            论文场景验收标准：
            1. 结构完整：摘要、引言、文献综述、方法、实验、结论、参考文献
            2. 引用格式符合 GB/T 7714 标准
            3. 无抄袭风险，降重后保持原意
            4. 贴合大数据专业研究方向
            5. 附带学术诚信声明
            """
        },
        "办公": {
            "keywords": ["word", "excel", "ppt", "汇报", "总结", "申请", "报告",
                        "表格", "文档", "演示", "幻灯片", "公文", "台账", "统计",
                        "邮件", "简历"],
            "description": "办公事务场景：文档处理、数据统计、演示文稿制作",
            "acceptance_criteria": """
            办公场景验收标准：
            1. 内容完整，包含所有要求的模块
            2. 格式统一：字体、字号、行距、段落格式一致
            3. 数据准确，计算无误
            4. 逻辑清晰，层次分明
            5. 可直接编辑使用
            """
        },
        "视频": {
            "keywords": ["视频", "剪辑", "分镜", "脚本", "配音", "字幕", "封面",
                        "短视频", "答辩视频", "展示", "录制", "剪映", "premiere"],
            "description": "视频创作场景：脚本撰写、分镜设计、制作指导",
            "acceptance_criteria": """
            视频场景验收标准：
            1. 脚本完整：台词、分镜、时长标注齐全
            2. 节奏合理，重点突出
            3. 分镜描述清晰，可直接执行
            4. 配套齐全：字幕、配音稿、封面文案
            5. 贴合具体使用场景（答辩/作业/展示）
            """
        }
    }

    def __init__(self):
        self.llm = llm

    def classify(self, user_input: str) -> Tuple[str, Dict]:
        """
        识别用户输入所属场景

        Args:
            user_input: 用户输入

        Returns:
            (场景名称, 场景配置字典)
        """
        input_lower = user_input.lower().strip()

        # 规则0：极短输入（问候等）直接返回默认场景，不走LLM
        if len(input_lower) < 5:
            scene = "编程"
            confidence = "短输入默认"
            scene_config = self.SCENES[scene]
            scene_config["scene_name"] = scene
            scene_config["confidence"] = confidence
            print(f"[场景识别] 判定为「{scene}」场景（{confidence}）")
            return scene, scene_config

        # 规则1：强关键词直接判定（办公软件名、视频专用词）
        strong_rules = {
            "办公": ["ppt", "powerpoint", "word", "excel", "幻灯片", "演示文稿", "表格"],
            "视频": ["视频", "剪辑", "分镜", "剪映", "premiere", "配音", "字幕"],
        }
        for scene, keywords in strong_rules.items():
            for kw in keywords:
                if kw in input_lower:
                    scene_config = self.SCENES[scene]
                    scene_config["scene_name"] = scene
                    scene_config["confidence"] = "强关键词匹配"
                    print(f"[场景识别] 判定为「{scene}」场景（强关键词匹配: {kw}）")
                    return scene, scene_config

        # 规则2：普通关键词快速匹配
        keyword_scene = self._keyword_match(user_input)
        if keyword_scene:
            scene = keyword_scene
            confidence = "关键词匹配"
        else:
            # 规则3：关键词无法判断时，用 LLM 智能识别
            scene = self._llm_classify(user_input)
            confidence = "LLM识别"

        scene_config = self.SCENES.get(scene, self.SCENES["编程"])
        scene_config["scene_name"] = scene
        scene_config["confidence"] = confidence

        print(f"[场景识别] 判定为「{scene}」场景（{confidence}）")
        return scene, scene_config

    def _keyword_match(self, user_input: str) -> str:
        """基于关键词的快速场景匹配"""
        input_lower = user_input.lower()
        scores = {}
        for scene, config in self.SCENES.items():
            score = sum(1 for kw in config["keywords"] if kw.lower() in input_lower)
            scores[scene] = score

        max_score = max(scores.values())
        if max_score >= 2:  # 至少匹配2个关键词才判定
            return max(scores, key=scores.get)
        return None

    def _llm_classify(self, user_input: str) -> str:
        """基于 LLM 的智能场景识别"""
        prompt = f"""请判断以下用户需求属于哪个场景，只返回场景名称（编程/论文/办公/视频）。

用户需求：{user_input[:300]}

场景定义：
- 编程：代码编写、调试、环境配置、项目开发、数据处理、机器学习
- 论文：学术论文撰写、开题报告、文献综述、查重降重、答辩准备
- 办公：Word/Excel/PPT文档处理、汇报总结、数据统计、邮件公文
- 视频：视频脚本、分镜设计、剪辑指导、配音字幕

只返回一个词：编程、论文、办公或视频。"""

        try:
            result = self.llm.chat_non_stream([{"role": "user", "content": prompt}])
            result = result.strip().strip("。").strip()
            # 提取场景名
            for scene in self.SCENES.keys():
                if scene in result:
                    return scene
            return "编程"  # 默认编程
        except Exception:
            return "编程"

    def get_all_scenes(self) -> Dict:
        """获取所有场景定义"""
        return self.SCENES
