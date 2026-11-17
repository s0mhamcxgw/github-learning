"""
论文专用工具：PDF 提取 + 标准毕业论文 Word 生成
作用：
  - pdf_extract：提取参考论文/资料全文（带页码），供智能体学习格式与内容
  - paper_writer：按"贵州财经大学本科毕业论文"格式生成 Word
    （页眉 + 封面 + 声明 + 摘要 + 目录 + 正文排版 + 分章追加写长论文）
"""
import os
import json
from typing import Dict, Any
from tools.base import BaseTool

# 默认页眉
_DEFAULT_HEADER = "贵州财经大学本科生毕业论文（设计）"

# 默认封面信息（可被 cover_info 覆盖）
_DEFAULT_COVER = {
    "title": "论文题目",
    "student_id": "学号",
    "name": "姓名",
    "class_name": "班级",
    "major": "专业",
    "college": "学院",
    "supervisor": "导师",
    "date": "2026年1月",
}

# 声明页固定文本
_DECLARATION = """本人郑重声明所呈交的论文是我个人在导师的指导下独立完成的。除了文中特别加以标注和致谢的地方外，论文中不包含其他人已经发表或撰写的研究成果。
论文作者签名：

本人同意贵州财经大学有关保留使用学位论文的规定，即：学校有权保留送交论文的复印件，允许论文被查阅和借阅；学校可以上网公布全部内容，可以采用影印、缩印或其他复制手段保存论文。
论文作者签名：　　　　　　　　　　指导教师签名：
签名日期：　　　　　　年　　月"""


class PdfExtractTool(BaseTool):
    """PDF 文本提取工具"""

    def __init__(self):
        super().__init__()
        self.tool_name = "pdf_extract"
        self.tool_description = "提取 PDF 文档的全文文本（带页码标记），用于阅读参考论文、资料、PDF 文件内容。"
        self.parameters = {
            "file_path": {
                "type": "str",
                "description": "PDF 文件绝对路径",
                "required": True,
            },
            "max_chars": {
                "type": "int",
                "description": "最多返回字符数，默认 60000，防止内容过长",
                "required": False,
            },
            "page_range": {
                "type": "str",
                "description": "只提取指定页，如 '1-5'、'3'，不填则提取全部页",
                "required": False,
            },
        }

    def execute(self, file_path: str, max_chars: int = 60000, page_range: str = None, **kwargs) -> Dict[str, Any]:
        param_error = self.validate_params(file_path=file_path)
        if param_error:
            return self._error(param_error)
        if not file_path.lower().endswith(".pdf"):
            return self._error("不是 PDF 文件: " + file_path)
        if not os.path.exists(file_path):
            return self._error(f"文件不存在: {file_path}")
        try:
            from pypdf import PdfReader
        except ImportError:
            return self._error("缺少 pypdf 库，请先安装: pip install pypdf")

        try:
            reader = PdfReader(file_path)
            total = len(reader.pages)
            start, end = 0, total
            if page_range:
                try:
                    if "-" in page_range:
                        a, b = page_range.split("-")
                        start, end = max(0, int(a) - 1), min(total, int(b))
                    else:
                        start, end = max(0, int(page_range) - 1), int(page_range)
                except Exception:
                    return self._error(f"page_range 格式错误: {page_range}，应为 '1-5' 或 '3'")

            parts = []
            for i in range(start, end):
                text = reader.pages[i].extract_text() or ""
                parts.append(f"\n===== 第 {i+1} 页 =====\n{text}")
            content = "".join(parts).strip()

            if len(content) > max_chars:
                content = content[:max_chars] + f"\n...（内容共 {len(content)} 字符，已截断，仅显示前 {max_chars} 字符）"

            result_text = f"PDF 提取成功: {file_path}\n总页数: {total}，本次提取第 {start+1}-{end} 页，内容 {len(content)} 字符\n\n{content}"
            return self._success(result_text, data={"content": content, "pages": total})
        except Exception as e:
            return self._error(f"PDF 提取失败: {type(e).__name__}: {e}")


class PaperWriterTool(BaseTool):
    """标准本科毕业论文 Word 生成工具"""

    def __init__(self):
        super().__init__()
        self.tool_name = "paper_writer"
        self.tool_description = "生成标准本科毕业论文 Word（.docx）：自动带页眉'贵州财经大学本科生毕业论文（设计）'、封面（题目/学号/姓名/班级/专业/学院/导师/日期）、声明页、摘要、目录域、正文论文排版。mode=create 创建新文档（含封面声明摘要），mode=append 分章追加正文（写长论文时多次调用）。"
        self.parameters = {
            "file_path": {
                "type": "str",
                "description": "要保存的 .docx 文件绝对路径",
                "required": True,
            },
            "content": {
                "type": "str",
                "description": "markdown 风格内容：# 章标题、## 节标题、### 小节标题、普通段落为正文、'- '列表、'| a | b |'表格。mode=create 时建议包含摘要、Abstract、目录、正文章节；mode=append 时是后续章节",
                "required": True,
            },
            "mode": {
                "type": "str",
                "description": "create=新建（自动生成页眉/封面/声明，再写入content）；append=向已有文件分页追加content。默认 create",
                "required": False,
            },
            "cover_info": {
                "type": "json",
                "description": "封面信息 JSON 字符串：{\"title\":\"论文题目\",\"student_id\":\"学号\",\"name\":\"姓名\",\"class_name\":\"班级\",\"major\":\"专业\",\"college\":\"学院\",\"supervisor\":\"导师姓名 职称\",\"date\":\"2026年1月\"}",
                "required": False,
            },
            "header_text": {
                "type": "str",
                "description": "页眉文本，默认'贵州财经大学本科生毕业论文（设计）'",
                "required": False,
            },
        }

    def execute(self, file_path: str, content: str, mode: str = "create",
                cover_info: str = None, header_text: str = None, **kwargs) -> Dict[str, Any]:
        param_error = self.validate_params(file_path=file_path, content=content)
        if param_error:
            return self._error(param_error)
        if not file_path.lower().endswith(".docx"):
            return self._error("文件路径必须以 .docx 结尾")

        try:
            import docx
            from docx.shared import Pt, Cm, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
            from docx.oxml.ns import qn
            from docx.oxml import OxmlElement
        except ImportError:
            return self._error("缺少 python-docx 库，请先安装: pip install python-docx")

        cover = dict(_DEFAULT_COVER)
        if cover_info:
            try:
                if isinstance(cover_info, str):
                    cover_info = json.loads(cover_info)
                cover.update({k: v for k, v in cover_info.items() if v})
            except Exception as e:
                return self._error(f"cover_info 不是合法 JSON: {e}，应为 {json.dumps(_DEFAULT_COVER, ensure_ascii=False)}")
        header_text = header_text or _DEFAULT_HEADER

        def set_font(run, cn_font="宋体", size=12, bold=False):
            run.font.name = "Times New Roman"
            run._element.rPr.rFonts.set(qn("w:eastAsia"), cn_font)
            run.font.size = Pt(size)
            run.font.bold = bold

        def add_body(doc, text, size=12, bold=False, indent=True):
            p = doc.add_paragraph()
            if indent:
                p.paragraph_format.first_line_indent = Pt(size * 2)
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
            r = p.add_run(text)
            set_font(r, "宋体", size, bold)
            return p

        def add_heading(doc, text, level):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(6)
            if level == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(text)
                set_font(r, "黑体", 16, True)          # 三号
            elif level == 2:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                r = p.add_run(text)
                set_font(r, "黑体", 14, True)          # 四号
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                r = p.add_run(text)
                set_font(r, "黑体", 12, True)          # 小四
            return p

        def add_toc(doc):
            """插入目录域（Word 打开后右键更新域即可生成目录）"""
            p = doc.add_paragraph()
            r = p.add_run()
            fld = OxmlElement("w:fldSimple")
            fld.set(qn("w:instr"), r'TOC \o "1-3" \h \z \u')
            run_el = OxmlElement("w:r")
            t = OxmlElement("w:t")
            t.text = "（目录：请在 Word 中右键此处 → 更新域 自动生成）"
            run_el.append(t)
            fld.append(run_el)
            p._p.append(fld)

        def parse_md(doc, content):
            """把 markdown 风格内容写入 doc（标题/正文/列表/表格）"""
            lines = content.split("\n")
            i = 0
            while i < len(lines):
                line = lines[i].rstrip()
                if not line.strip():
                    i += 1
                    continue
                if line.strip().startswith("|") and "|" in line[1:]:
                    rows = []
                    while i < len(lines) and lines[i].strip().startswith("|") and "|" in lines[i][1:]:
                        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                        if not all(set(c.replace("-", "").replace(":", "").strip()) == set() for c in cells):
                            rows.append(cells)
                        i += 1
                    if rows:
                        table = doc.add_table(rows=len(rows), cols=len(rows[0]))
                        table.style = 'Light Grid Accent 1'
                        for ri, row in enumerate(rows):
                            for ci, cell in enumerate(row):
                                if ci < len(table.rows[ri].cells):
                                    table.rows[ri].cells[ci].text = cell
                    continue
                if line.startswith("### "):
                    add_heading(doc, line[4:].strip(), 3)
                elif line.startswith("## "):
                    add_heading(doc, line[3:].strip(), 2)
                elif line.startswith("# "):
                    add_heading(doc, line[2:].strip(), 1)
                elif line.startswith("- ") or line.startswith("* "):
                    p = doc.add_paragraph(style="List Bullet")
                    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
                    r = p.add_run(line[2:].strip())
                    set_font(r, "宋体", 12)
                else:
                    add_body(doc, line.strip())
                i += 1

        try:
            _dir = os.path.dirname(file_path)
            if _dir and not os.path.exists(_dir):
                os.makedirs(_dir, exist_ok=True)

            if mode == "create":
                doc = docx.Document()
                # 页边距
                for section in doc.sections:
                    section.top_margin = Cm(2.54)
                    section.bottom_margin = Cm(2.54)
                    section.left_margin = Cm(3.17)
                    section.right_margin = Cm(3.17)
                # 页眉
                header_p = doc.sections[0].header.paragraphs[0]
                header_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                hr = header_p.add_run(header_text)
                set_font(hr, "宋体", 10.5)

                # ---- 封面 ----
                for _ in range(3):
                    doc.add_paragraph()
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run("本科毕业论文（设计）")
                set_font(r, "黑体", 22, True)          # 二号
                for _ in range(2):
                    doc.add_paragraph()
                # 论文题目（可能两行）
                title = cover["title"]
                for line in [title[i:i+18] for i in range(0, len(title), 18)] or [title]:
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    r = p.add_run(line)
                    set_font(r, "宋体", 16, True)      # 三号
                for _ in range(2):
                    doc.add_paragraph()
                # 信息行
                info_items = [
                    ("学 生 学 号", cover["student_id"]),
                    ("学 生 姓 名", cover["name"]),
                    ("所 属 班 级", cover["class_name"]),
                    ("所 学 专 业", cover["major"]),
                    ("所 属 学 院", cover["college"]),
                    ("导师姓名、职称", cover["supervisor"]),
                ]
                for label, value in info_items:
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
                    r = p.add_run(f"{label}：{value}")
                    set_font(r, "宋体", 14)             # 四号
                for _ in range(2):
                    doc.add_paragraph()
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(cover["date"])
                set_font(r, "宋体", 14)

                # ---- 声明页 ----
                doc.add_page_break()
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run("声明及论文使用的授权")
                set_font(r, "黑体", 16, True)
                for seg in _DECLARATION.split("\n"):
                    add_body(doc, seg)

                # ---- 正文内容（摘要/Abstract/目录/章节）----
                doc.add_page_break()
                parse_md(doc, content)

                # 目录域（放在摘要后，正文前由 LLM 控制顺序；此处追加在末尾的目录域作为兜底）
                has_toc = "目录" in content
                if not has_toc:
                    doc.add_page_break()
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    r = p.add_run("目 录")
                    set_font(r, "黑体", 16, True)
                    add_toc(doc)

            else:  # append
                if not os.path.exists(file_path):
                    return self._error(f"append 模式需要已存在的文件: {file_path}")
                doc = docx.Document(file_path)
                doc.add_page_break()
                parse_md(doc, content)

            doc.save(file_path)
            size = os.path.getsize(file_path)
            result_text = f"论文 Word 生成成功: {file_path}\n模式: {mode} | 文件大小: {size} 字节"
            return self._success(result_text, data={"path": file_path, "size": size})
        except Exception as e:
            return self._error(f"生成论文 Word 失败: {type(e).__name__}: {e}")
