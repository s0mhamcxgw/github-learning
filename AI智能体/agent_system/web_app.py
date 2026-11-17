"""
智能体 Web 可视化界面（Gradio）
作用：提供浏览器交互界面，支持对话、模式选择、工具调用、记忆查看
运行方式：python web_app.py，然后浏览器打开 http://127.0.0.1:7860
"""
import os
import sys
import time
import gradio as gr

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from core.llm_client import llm
from core.prompt_loader import prompt_loader
from core.task_agent import TaskAgent
from memory.manager import MemoryManager
from workflows.workflow_manager import WorkflowManager
from workflows.scene_classifier import SceneClassifier
from agents.agent_manager import AgentManager
from tools.tool_calling_agent import ToolCallingAgent


# ========== 全局初始化 ==========

# 校验配置
settings.validate()

# 加载系统提示词
system_prompt = prompt_loader.load("system_prompt.md")

# 初始化各模块
memory = MemoryManager()
workflow_manager = WorkflowManager(memory=memory)
scene_classifier = SceneClassifier()
agent_manager = AgentManager(memory=memory)
tool_agent = ToolCallingAgent(memory=memory)
task_agent = TaskAgent(memory=memory)

# 开始新会话
memory.start_new_session("Web对话")
if system_prompt:
    memory.add_system_message(system_prompt)


# ========== 对话处理函数 ==========

# 支持直接读取的文本类文件后缀
_TEXT_EXTS = {
    '.txt', '.md', '.py', '.json', '.csv', '.log', '.xml', '.yaml', '.yml',
    '.html', '.htm', '.java', '.c', '.cpp', '.h', '.hpp', '.sql', '.ini',
    '.cfg', '.toml', '.rst', '.tex', '.js', '.ts', '.go', '.rs', '.sh', '.bat'
}

# 上传文件持久化目录（复制到项目内，防止 Gradio 临时文件被清理）
_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "uploads")


def _persist_upload(file_path):
    """把上传的临时文件复制到项目 outputs/uploads/，返回持久化路径"""
    try:
        os.makedirs(_UPLOAD_DIR, exist_ok=True)
        fname = os.path.basename(file_path)
        dst = os.path.join(_UPLOAD_DIR, fname)
        if os.path.abspath(file_path) != os.path.abspath(dst):
            import shutil
            if os.path.exists(dst):
                stem, ext = os.path.splitext(fname)
                dst = os.path.join(_UPLOAD_DIR, f"{stem}_{int(time.time())}{ext}")
            shutil.copy2(file_path, dst)
        return dst
    except Exception:
        return file_path


def _normalize_files(files):
    """把 gr.File 返回的各种形式统一成文件路径列表"""
    if not files:
        return []
    if not isinstance(files, (list, tuple)):
        files = [files]
    paths = []
    for f in files:
        if hasattr(f, 'name'):      # 临时文件对象
            paths.append(f.name)
        elif isinstance(f, str):    # 路径字符串
            paths.append(f)
    return paths


def read_file_content(file_path, max_chars=50000):
    """读取上传文件内容为文本（支持 txt/md/代码/docx/pdf 等）"""
    fname = os.path.basename(file_path)
    ext = os.path.splitext(fname)[1].lower()
    try:
        if ext in _TEXT_EXTS:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        elif ext == '.docx':
            try:
                import docx
            except ImportError:
                return f"【{fname}】读取失败：缺少 python-docx 库，请执行 pip install python-docx"
            doc = docx.Document(file_path)
            parts = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    cells = [c.text.strip() for c in row.cells]
                    if any(cells):
                        parts.append(' | '.join(cells))
            content = '\n'.join(parts)
        elif ext == '.pdf':
            # PDF 不硬塞全文（长文档会被截断），改为提示路径，让任务引擎用 pdf_extract 完整读取
            return (f"【用户上传文件：{fname}，已保存到 {file_path}】\n"
                    f"这是一个 PDF 文件。如果需要读取其完整内容，请使用 pdf_extract 工具，"
                    f"参数 file_path=\"{file_path}\"（可配合 page_range 指定页范围分批读取）。")
        elif ext in ('.xlsx', '.xls'):
            return f"【{fname}】Excel 请先另存为 CSV 后再上传（或用工具调用模式让 AI 直接读取）"
        else:
            return f"【{fname}】暂不支持该格式，请转成 txt / md / docx / pdf 后上传"

        if not content.strip():
            return f"【{fname}】读取成功但未提取到文字（可能是扫描版/图片型 PDF，无法直接识别）"
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n...（内容共 {len(content)} 字符，已截断，仅展示前 {max_chars} 字符）"
        return f"【用户上传文件：{fname}（已保存到 {file_path}）】\n{content}\n【文件内容结束】"
    except Exception as e:
        return f"【{fname}】读取失败：{type(e).__name__}: {e}"


def process_message(user_input, mode, scene, history, files=None):
    """
    处理用户消息，根据模式选择不同的处理方式

    Args:
        user_input: 用户输入
        mode: 处理模式（自动/自主任务/快速对话/场景Agent/工具调用/通用工作流）
        scene: 场景（编程/论文/办公/视频，仅场景Agent模式有效）
        history: 对话历史
        files: 上传的文件列表（可选）

    Yields:
        (更新后的对话历史, 产出文件列表)
    """
    if not user_input or not user_input.strip():
        yield history, None
        return

    user_input = user_input.strip()

    # 读取上传文件内容，拼进用户消息（文件持久化保存 + 内容/路径并入上下文，任务引擎可完整读取）
    file_paths = _normalize_files(files)
    if file_paths:
        file_parts = []
        for fp in file_paths:
            saved = _persist_upload(fp)   # 复制到项目 outputs/uploads/，防 Gradio 临时文件被清理
            part = read_file_content(saved)
            if part:
                file_parts.append(part)
        if file_parts:
            file_text = "\n\n".join(file_parts)
            if user_input:
                user_input = file_text + "\n\n我的问题：" + user_input
            else:
                user_input = file_text + "\n\n请根据以上文件内容帮我处理。"

    # 添加用户消息到记忆
    memory.add_user_message(user_input)

    produced_files = []

    # ---- 自主任务模式：流式展示 规划→执行→交付 ----
    if mode == "自主任务":
        log_parts = []
        for event in task_agent.process(user_input):
            if event["type"] == "plan":
                log_parts.append("📋 **任务计划**\n\n" + event["content"])
            elif event["type"] == "tool_call":
                log_parts.append(event["content"])
            elif event["type"] == "tool_result":
                log_parts.append(event["content"])
            elif event["type"] == "done":
                produced_files = event.get("files", [])
                log_parts.append("✅ **任务完成**\n\n" + event["content"])
            # 实时刷新界面（只展示最近 2 条过程，避免消息过长）
            live = history + [(user_input, "\n\n---\n\n".join(log_parts[-2:]))]
            yield live, produced_files
        response = "\n\n".join(log_parts)
        final_history = history + [(user_input, response)]

    else:
        # ---- 其他模式：一次性返回 ----
        if mode == "快速对话":
            response = _chat_quick(user_input)
        elif mode == "场景Agent":
            response = _chat_scene_agent(user_input, scene)
        elif mode == "工具调用":
            response = _chat_tool(user_input)
        elif mode == "通用工作流":
            response = _chat_workflow(user_input)
        else:  # 自动模式
            response = _chat_auto(user_input)
        final_history = history + [(user_input, response)]

    # 添加助手回复到记忆
    memory.add_assistant_message(response[:2000])

    # 自动提取长期记忆
    try:
        memory.extract_and_store(user_input, response)
    except:
        pass

    yield final_history, (produced_files if produced_files else None)


def _chat_quick(user_input):
    """快速对话"""
    context_messages = memory.get_context_messages(user_input)
    full_response = ""
    for chunk in llm.chat(context_messages):
        full_response += chunk
    return full_response


def _chat_scene_agent(user_input, scene):
    """场景 Agent"""
    if not scene or scene == "自动识别":
        scene, _ = scene_classifier.classify(user_input)
    result = agent_manager.process(scene, user_input)
    return result


def _chat_tool(user_input):
    """工具调用（ReAct）"""
    result = tool_agent.process(user_input)
    return result


def _chat_workflow(user_input):
    """通用五阶闭环工作流"""
    result = workflow_manager.execute(user_input)
    return result


def _chat_auto(user_input):
    """自动模式：简单问题快速对话，复杂任务用自主任务引擎（真正执行工具、产出文件）"""
    if workflow_manager.should_use_workflow(user_input):
        # 复杂任务 → 自主任务引擎（与"自主任务"模式相同的能力）
        result = ""
        for event in task_agent.process(user_input):
            if event["type"] == "done":
                result = event["content"]
        return result
    else:
        # 简单问题快速对话
        return _chat_quick(user_input)


# ========== 辅助函数 ==========

def clear_history():
    """清空对话历史"""
    memory.clear_current_session()
    return [], "对话已清空", None


def new_session():
    """新建会话"""
    memory.start_new_session("Web对话")
    if system_prompt:
        memory.add_system_message(system_prompt)
    return [], "已创建新会话", None


def get_memory_stats():
    """获取记忆统计"""
    stats = memory.get_memory_stats()
    result = f"""## 记忆系统统计

### 短期记忆
- 当前会话: {stats['短期记忆']['当前会话']}
- 历史会话数: {stats['短期记忆']['历史会话数']}
- 当前消息数: {stats['短期记忆']['当前消息数']}

### 长期记忆
- 用户偏好: {stats['长期记忆']['preferences_count']} 条
- FAQ库: {stats['长期记忆']['faq_count']} 条
- 历史经验: {stats['长期记忆']['experiences_count']} 条
- 知识库: {stats['长期记忆']['knowledge_count']} 条
"""
    return result


def get_tools_list():
    """获取工具列表"""
    tools = tool_agent.tool_manager.get_available_tools()
    result = "## 可用工具列表\n\n"
    for i, tool in enumerate(tools, 1):
        result += f"### {i}. {tool['name']}\n"
        result += f"**描述**: {tool['description']}\n\n"
        result += "**参数**:\n"
        for param_name, param_def in tool['parameters'].items():
            required = "必填" if param_def.get('required') else "可选"
            result += f"- `{param_name}` ({param_def['type']}, {required}): {param_def['description']}\n"
        result += "\n"
    return result


def get_preferences():
    """获取用户偏好"""
    prefs = memory.long_term.get_preferences()
    if not prefs:
        return "暂无记录的用户偏好"
    result = "## 用户偏好\n\n"
    for p in prefs:
        result += f"- **[{p['category']}] {p['key']}**: {p['value']}"
        if p.get('note'):
            result += f" ({p['note']})"
        result += "\n"
    return result


# ========== Gradio 界面构建 ==========

def build_interface():
    """构建 Gradio 界面"""

    with gr.Blocks(
        title=f"{settings.AGENT_NAME} v{settings.AGENT_VERSION}",
    ) as demo:

        # 标题
        gr.Markdown(f"""
        # {settings.AGENT_NAME} v{settings.AGENT_VERSION}
        **模型**: {settings.DEFAULT_MODEL} | **记忆系统**: 已启用 | **工作流**: 已启用 | **场景Agent**: 4个 | **工具**: {len(tool_agent.tool_manager.get_available_tools())}个
        """)

        with gr.Row():
            # 左侧：对话区
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="对话窗口",
                    elem_classes=["chatbot"],
                    height=500
                )

                with gr.Row():
                    file_input = gr.File(
                        label="上传文件（写论文/读资料用：支持 txt/md/代码/docx/pdf，可多选）",
                        file_count="multiple",
                        scale=4,
                        elem_classes=["file-upload"],
                    )

                with gr.Row():
                    msg_input = gr.Textbox(
                        label="输入你的问题",
                        placeholder="输入问题后按回车发送...（可先上传文件，再问基于文件的问题）",
                        scale=4,
                        lines=2
                    )
                    send_btn = gr.Button("发送", variant="primary", scale=1)

                with gr.Row():
                    clear_btn = gr.Button("清空对话")
                    new_btn = gr.Button("新建会话")

                # 产出文件区（自主任务/自动模式生成的 Word/Excel/PPT 等）
                gr.Markdown("### 产出文件")
                file_outputs = gr.File(
                    label="智能体生成的文件（可点击下载）",
                    file_count="multiple",
                    interactive=False,
                    elem_classes=["file-outputs"],
                )

            # 右侧：控制面板
            with gr.Column(scale=1, elem_classes=["sidebar"]):
                gr.Markdown("### 控制面板")

                mode_select = gr.Dropdown(
                    label="处理模式",
                    choices=["自动", "自主任务", "快速对话", "场景Agent", "工具调用", "通用工作流"],
                    value="自动",
                    info="自动：简单问题直接答、复杂任务自动执行并产出文件；自主任务：强制走任务执行引擎"
                )

                scene_select = gr.Dropdown(
                    label="场景（仅场景Agent模式有效）",
                    choices=["自动识别", "编程", "论文", "办公", "视频"],
                    value="自动识别"
                )

                gr.Markdown("---")
                gr.Markdown("### 信息查看")

                with gr.Row():
                    memory_btn = gr.Button("记忆统计", size="sm")
                    tools_btn = gr.Button("工具列表", size="sm")
                    prefs_btn = gr.Button("用户偏好", size="sm")

                info_output = gr.Markdown(
                    "点击上方按钮查看相关信息",
                    label="信息输出"
                )

                status_output = gr.Textbox(
                    label="状态",
                    value="系统就绪",
                    interactive=False
                )

        # 事件绑定
        msg_input.submit(
            process_message,
            inputs=[msg_input, mode_select, scene_select, chatbot, file_input],
            outputs=[chatbot, file_outputs]
        ).then(lambda: "", outputs=[msg_input]).then(lambda: None, outputs=[file_input])

        send_btn.click(
            process_message,
            inputs=[msg_input, mode_select, scene_select, chatbot, file_input],
            outputs=[chatbot, file_outputs]
        ).then(lambda: "", outputs=[msg_input]).then(lambda: None, outputs=[file_input])

        clear_btn.click(
            clear_history,
            outputs=[chatbot, status_output, file_outputs]
        )

        new_btn.click(
            new_session,
            outputs=[chatbot, status_output, file_outputs]
        )

        memory_btn.click(
            get_memory_stats,
            outputs=[info_output]
        )

        tools_btn.click(
            get_tools_list,
            outputs=[info_output]
        )

        prefs_btn.click(
            get_preferences,
            outputs=[info_output]
        )

    return demo


# ========== 主入口 ==========

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"  启动 {settings.AGENT_NAME} v{settings.AGENT_VERSION} Web 界面")
    print(f"  模型: {settings.DEFAULT_MODEL}")
    print(f"  浏览器打开: http://127.0.0.1:7860")
    print(f"{'='*60}\n")

    demo = build_interface()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        inbrowser=True,  # 自动打开浏览器
        theme=gr.themes.Soft(),
        css="""
        .chatbot { height: 500px; }
        .sidebar { background-color: #f8f9fa; }
        """
    )
