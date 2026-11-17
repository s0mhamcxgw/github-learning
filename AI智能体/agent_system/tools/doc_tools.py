"""
文档生成工具：Word / Excel / PPT / 文件信息
作用：让智能体能够真正产出可交付的文档文件（写论文、做表格、做PPT）
"""
import os
import json
from datetime import datetime
from typing import Dict, Any
from tools.base import BaseTool


def _ensure_dir(file_path: str):
    """确保文件所在目录存在"""
    dir_path = os.path.dirname(file_path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)


class DocxWriterTool(BaseTool):
    """Word 文档生成工具"""

    def __init__(self):
        super().__init__()
        self.tool_name = "docx_writer"
        self.tool_description = "生成 Word 文档（.docx），支持 markdown 风格的标题/段落/列表/表格，用于写论文、报告、作业等。"
        self.parameters = {
            "file_path": {
                "type": "str",
                "description": "要保存的 Word 文件绝对路径（以 .docx 结尾）",
                "required": True,
            },
            "content": {
                "type": "str",
                "description": "文档内容，支持 markdown 语法：'# '一级标题、'## '二级标题、'### '三级标题、'- '列表项、'| a | b |'表格、普通段落，用换行分隔",
                "required": True,
            },
        }

    def execute(self, file_path: str, content: str, **kwargs) -> Dict[str, Any]:
        param_error = self.validate_params(file_path=file_path, content=content)
        if param_error:
            return self._error(param_error)
        if not file_path.lower().endswith(".docx"):
            return self._error("文件路径必须以 .docx 结尾")
        try:
            import docx
            from docx.shared import Pt, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH
        except ImportError:
            return self._error("缺少 python-docx 库，请先安装: pip install python-docx")

        try:
            _ensure_dir(file_path)
            document = docx.Document()

            lines = content.split("\n")
            i = 0
            while i < len(lines):
                line = lines[i].rstrip()
                if not line.strip():
                    i += 1
                    continue

                # 表格：连续 | 行
                if line.strip().startswith("|") and "|" in line[1:]:
                    table_rows = []
                    while i < len(lines) and lines[i].strip().startswith("|") and "|" in lines[i][1:]:
                        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                        # 跳过分隔行 |---|--|
                        if not all(set(c.replace("-", "").replace(":", "").strip()) == set() for c in cells):
                            table_rows.append(cells)
                        i += 1
                    if table_rows:
                        table = document.add_table(rows=len(table_rows), cols=len(table_rows[0]))
                        table.style = 'Light Grid Accent 1'
                        for r, row in enumerate(table_rows):
                            for c, cell in enumerate(row):
                                if c < len(table.rows[r].cells):
                                    table.rows[r].cells[c].text = cell
                    continue

                # 标题
                if line.startswith("### "):
                    document.add_heading(line[4:].strip(), level=3)
                elif line.startswith("## "):
                    document.add_heading(line[3:].strip(), level=2)
                elif line.startswith("# "):
                    document.add_heading(line[2:].strip(), level=1)
                # 列表
                elif line.startswith("- ") or line.startswith("* "):
                    document.add_paragraph(line[2:].strip(), style='List Bullet')
                elif line.startswith("1. ") or line.startswith("2. ") or line.startswith("3. ") or \
                     line.startswith("4. ") or line.startswith("5. ") or line.startswith("6. ") or \
                     line.startswith("7. ") or line.startswith("8. ") or line.startswith("9. ") or \
                     line.startswith("0. "):
                    document.add_paragraph(line[3:].strip(), style='List Number')
                # 引用
                elif line.startswith("> "):
                    p = document.add_paragraph(line[2:].strip())
                    p.italic = True
                # 普通段落
                else:
                    document.add_paragraph(line.strip())
                i += 1

            document.save(file_path)
            size = os.path.getsize(file_path)
            result_text = f"Word 文档生成成功: {file_path}\n文件大小: {size} 字节"
            return self._success(result_text, data={"path": file_path, "size": size})
        except Exception as e:
            return self._error(f"生成 Word 失败: {type(e).__name__}: {e}")


class XlsxWriterTool(BaseTool):
    """Excel 表格生成工具"""

    def __init__(self):
        super().__init__()
        self.tool_name = "xlsx_writer"
        self.tool_description = "生成 Excel 表格（.xlsx），data 为二维数组（第一行是表头），自动设置列宽，用于数据统计、台账、成绩表等。"
        self.parameters = {
            "file_path": {
                "type": "str",
                "description": "要保存的 Excel 文件绝对路径（以 .xlsx 结尾）",
                "required": True,
            },
            "data": {
                "type": "json",
                "description": "二维数组 JSON：data[0] 是表头，后续是数据行。如 [[\"姓名\",\"成绩\"],[\"张三\",90]]",
                "required": True,
            },
            "sheet_name": {
                "type": "str",
                "description": "工作表名称，默认 Sheet1",
                "required": False,
            },
        }

    def execute(self, file_path: str, data, sheet_name: str = "Sheet1", **kwargs) -> Dict[str, Any]:
        param_error = self.validate_params(file_path=file_path, data=data)
        if param_error:
            return self._error(param_error)
        if not file_path.lower().endswith((".xlsx", ".xlsm")):
            return self._error("文件路径必须以 .xlsx 结尾")

        # data 可能是字符串（JSON）或已解析的列表
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                return self._error(f"data 不是合法 JSON: {e}")
        if not isinstance(data, list) or not data or not isinstance(data[0], list):
            return self._error("data 必须是二维数组，第一行为表头")

        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
        except ImportError:
            return self._error("缺少 openpyxl 库，请先安装: pip install openpyxl")

        try:
            _ensure_dir(file_path)
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = sheet_name[:31]

            header_font = Font(bold=True, color="FFFFFF", size=11)
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")

            for r, row in enumerate(data, start=1):
                for c, value in enumerate(row, start=1):
                    cell = ws.cell(row=r, column=c)
                    cell.value = value
                    if r == 1:
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                    if isinstance(value, (int, float)):
                        cell.number_format = "0.00" if isinstance(value, float) else "General"

            # 自动列宽（中文按2字符宽计算）
            for col_idx in range(1, len(data[0]) + 1):
                max_len = 0
                for r in range(1, len(data) + 1):
                    v = ws.cell(row=r, column=col_idx).value
                    if v is not None:
                        s = str(v)
                        l = sum(2 if ord(ch) > 127 else 1 for ch in s)
                        max_len = max(max_len, l)
                ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = min(max_len + 2, 50)

            wb.save(file_path)
            size = os.path.getsize(file_path)
            result_text = f"Excel 表格生成成功: {file_path}\n数据行数: {len(data)-1} 行, 列数: {len(data[0])} 列\n文件大小: {size} 字节"
            return self._success(result_text, data={"path": file_path, "size": size, "rows": len(data)-1})
        except Exception as e:
            return self._error(f"生成 Excel 失败: {type(e).__name__}: {e}")


class PptxWriterTool(BaseTool):
    """PPT 演示文稿生成工具"""

    def __init__(self):
        super().__init__()
        self.tool_name = "pptx_writer"
        self.tool_description = "生成 PPT 演示文稿（.pptx），slides 为幻灯片列表，每页包含标题和要点，用于答辩、汇报、展示。"
        self.parameters = {
            "file_path": {
                "type": "str",
                "description": "要保存的 PPT 文件绝对路径（以 .pptx 结尾）",
                "required": True,
            },
            "slides": {
                "type": "json",
                "description": "幻灯片结构 JSON：[[\"标题1\", \"要点1\\n要点2\"], [\"标题2\", \"要点1\"]]，每项是 [标题, 要点文本]",
                "required": True,
            },
        }

    def execute(self, file_path: str, slides, **kwargs) -> Dict[str, Any]:
        param_error = self.validate_params(file_path=file_path, slides=slides)
        if param_error:
            return self._error(param_error)
        if not file_path.lower().endswith(".pptx"):
            return self._error("文件路径必须以 .pptx 结尾")

        if isinstance(slides, str):
            try:
                slides = json.loads(slides)
            except json.JSONDecodeError as e:
                return self._error(f"slides 不是合法 JSON: {e}")
        if not isinstance(slides, list) or not slides:
            return self._error("slides 必须是列表，每项为 [标题, 要点文本]")

        try:
            from pptx import Presentation
            from pptx.util import Inches, Pt
        except ImportError:
            return self._error("缺少 python-pptx 库，请先安装: pip install python-pptx")

        try:
            _ensure_dir(file_path)
            prs = Presentation()
            # 16:9 宽屏
            prs.slide_width = Inches(13.333)
            prs.slide_height = Inches(7.5)
            slide_layout = prs.slide_layouts[1]  # 标题+内容

            for item in slides:
                if not isinstance(item, list) or len(item) < 2:
                    continue
                title, body = item[0], item[1]
                slide = prs.slides.add_slide(slide_layout)
                slide.shapes.title.text = str(title)
                body_shape = slide.placeholders[1]
                text_frame = body_shape.text_frame
                text_frame.clear()
                lines = str(body).split("\n")
                for i, line in enumerate(lines):
                    if i == 0:
                        text_frame.text = line
                    else:
                        p = text_frame.add_paragraph()
                        p.text = line
                    p = text_frame.paragraphs[i]
                    p.level = 1 if line.strip().startswith("  ") or line.strip().startswith("- ") else 0

            prs.save(file_path)
            size = os.path.getsize(file_path)
            result_text = f"PPT 生成成功: {file_path}\n幻灯片页数: {len(prs.slides)} 页\n文件大小: {size} 字节"
            return self._success(result_text, data={"path": file_path, "size": size, "slides": len(prs.slides)})
        except Exception as e:
            return self._error(f"生成 PPT 失败: {type(e).__name__}: {e}")


class FileInfoTool(BaseTool):
    """文件信息检查工具（用于验证产出物）"""

    def __init__(self):
        super().__init__()
        self.tool_name = "file_info"
        self.tool_description = "检查文件是否存在及其大小、修改时间，用于验证文件是否成功生成。"
        self.parameters = {
            "file_path": {
                "type": "str",
                "description": "要检查的文件绝对路径",
                "required": True,
            },
        }

    def execute(self, file_path: str, **kwargs) -> Dict[str, Any]:
        param_error = self.validate_params(file_path=file_path)
        if param_error:
            return self._error(param_error)

        if not os.path.exists(file_path):
            return self._error(f"文件不存在: {file_path}")

        try:
            stat = os.stat(file_path)
            size = stat.st_size
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            if size == 0:
                return self._error(f"文件存在但大小为 0 字节（可能生成失败）: {file_path}")
            result_text = f"文件检查通过: {file_path}\n大小: {size} 字节 | 修改时间: {mtime}"
            return self._success(result_text, data={"path": file_path, "size": size, "mtime": mtime})
        except Exception as e:
            return self._error(f"检查文件失败: {type(e).__name__}: {e}")
