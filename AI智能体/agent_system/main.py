"""
智能体主入口（V6.0 - 自主任务引擎 + 记忆系统 + 工作流引擎 + 场景化Agent + 工具调用）
作用：启动智能体，进行多轮对话，支持：
      - 自主任务引擎：一句话完成工作（规划→执行→验证→交付真实文件）
      - 短期记忆持久化、长期记忆自动积累
      - 五阶闭环工作流（通用）
      - 四大场景专属Agent（编程/论文/办公/视频）
      - 工具调用能力（代码执行、文件读写、包管理、命令执行、Word/Excel/PPT生成）
运行方式：在 PyCharm 中直接运行此文件，或命令行 python main.py

命令列表：
  exit        - 退出
  clear       - 清空当前对话
  /memory     - 查看记忆统计
  /sessions   - 列出历史会话
  /load <id>  - 加载指定会话
  /new        - 新建会话
  /prefs      - 查看用户偏好
  /agents     - 查看所有场景Agent
  /tools      - 查看所有可用工具
  /workflow   - 强制使用通用五阶闭环工作流（下一条消息）
  /scene <名> - 强制使用指定场景Agent（下一条消息，如 /scene 编程）
  /tool       - 强制使用工具调用模式（下一条消息）
  /quick      - 强制使用快速对话（下一条消息）
  /task       - 强制使用自主任务模式（下一条消息）
  /stats      - 查看统计信息

产出文件默认保存到: outputs/ 目录
"""
import sys
from config.settings import settings
from core.llm_client import llm
from core.prompt_loader import prompt_loader
from core.task_agent import TaskAgent
from memory.manager import MemoryManager
from workflows.workflow_manager import WorkflowManager
from workflows.scene_classifier import SceneClassifier
from agents.agent_manager import AgentManager
from tools.tool_calling_agent import ToolCallingAgent


class Agent:
    """智能体主类（V5.0 - 记忆 + 工作流 + 场景化Agent + 工具调用）"""

    def __init__(self):
        # 1. 校验配置
        if not settings.validate():
            sys.exit(1)

        # 2. 加载系统提示词
        self.system_prompt = prompt_loader.load("system_prompt.md")

        # 3. 初始化记忆管理器
        self.memory = MemoryManager()

        # 4. 初始化工作流管理器
        self.workflow_manager = WorkflowManager(memory=self.memory)

        # 5. 初始化场景识别器
        self.scene_classifier = SceneClassifier()

        # 6. 初始化场景 Agent 管理器
        self.agent_manager = AgentManager(memory=self.memory)

        # 7. 初始化工具调用 Agent
        self.tool_agent = ToolCallingAgent(memory=self.memory)

        # 8. 初始化自主任务引擎（一句话完成工作）
        self.task_agent = TaskAgent(memory=self.memory)

        # 9. 模式控制
        self.force_workflow = False
        self.force_quick = False
        self.force_scene = None
        self.force_tool = False
        self.force_task = False

        # 10. 开始新会话
        self.memory.start_new_session("新对话")
        if self.system_prompt:
            self.memory.add_system_message(self.system_prompt)

        print(f"\n{'='*60}")
        print(f"  {settings.AGENT_NAME} v{settings.AGENT_VERSION}")
        print(f"  模型: {settings.DEFAULT_MODEL}")
        print(f"  记忆: 已启用 | 工作流: 已启用 | 场景Agent: 4个 | 工具: {len(self.tool_agent.tool_manager.get_available_tools())}个")
        print(f"  自主任务: 已启用（一句话完成工作，产出文件到 {settings.OUTPUT_DIR}）")
        print(f"{'='*60}")
        print("命令: exit退出 | clear清空 | /memory记忆 | /agents场景 | /tools工具")
        print("      /workflow工作流 | /scene <名>场景Agent | /tool工具调用 | /quick快速对话 | /task自主任务")
        print()

    def chat(self, user_input: str):
        """处理一轮对话（自动判断模式）"""
        # 判断使用哪种模式
        use_task = self.workflow_manager.should_use_workflow(user_input)  # 复杂任务默认走自主任务引擎
        use_scene_agent = False
        use_workflow = False
        use_tool = False
        use_quick = not use_task

        # 强制模式覆盖
        if self.force_workflow:
            use_workflow = True
            use_scene_agent = False
            use_tool = False
            use_quick = False
            self.force_workflow = False
            print("[系统] 已强制使用通用五阶闭环工作流\n")
        if self.force_scene:
            use_scene_agent = True
            use_quick = False
            use_tool = False
            use_task = False
            print(f"[系统] 已强制使用 {self.force_scene} 场景 Agent\n")
        if self.force_tool:
            use_tool = True
            use_scene_agent = False
            use_quick = False
            use_task = False
            self.force_tool = False
            print("[系统] 已强制使用工具调用模式\n")
        if self.force_quick:
            use_quick = True
            use_scene_agent = False
            use_tool = False
            use_task = False
            self.force_quick = False
            print("[系统] 已强制使用快速对话\n")
        if self.force_task:
            use_task = True
            use_scene_agent = False
            use_workflow = False
            use_tool = False
            use_quick = False
            self.force_task = False
            print("[系统] 已强制使用自主任务模式（一句话完成工作）\n")

        if use_task:
            self._chat_with_task(user_input)
        elif use_quick:
            self._chat_quick(user_input)
        elif use_tool:
            self._chat_with_tool(user_input)
        elif use_workflow:
            self._chat_with_workflow(user_input)
        elif use_scene_agent:
            self._chat_with_scene_agent(user_input)
        else:
            self._chat_quick(user_input)

    def _chat_quick(self, user_input: str):
        """快速对话"""
        self.memory.add_user_message(user_input)
        context_messages = self.memory.get_context_messages(user_input)

        print(f"\n[{settings.AGENT_NAME}]: ", end="", flush=True)
        full_response = ""
        for chunk in llm.chat(context_messages):
            print(chunk, end="", flush=True)
            full_response += chunk
        print("\n")

        self.memory.add_assistant_message(full_response)
        self.memory.extract_and_store(user_input, full_response)

    def _chat_with_workflow(self, user_input: str):
        """通用五阶闭环工作流"""
        self.memory.add_user_message(user_input)
        print(f"\n[{settings.AGENT_NAME}]: 正在启动通用五阶闭环工作流...\n")
        result = self.workflow_manager.execute(user_input)
        print(result)
        self.memory.add_assistant_message(result[:2000])
        self.memory.extract_and_store(user_input, result)

    def _chat_with_scene_agent(self, user_input: str):
        """使用场景专属 Agent"""
        self.memory.add_user_message(user_input)

        # 识别场景
        if self.force_scene:
            scene = self.force_scene
            self.force_scene = None
        else:
            scene, _ = self.scene_classifier.classify(user_input)

        print(f"\n[{settings.AGENT_NAME}]: 正在调用 {scene} 场景专属 Agent...\n")

        # 调用场景 Agent
        result = self.agent_manager.process(scene, user_input)
        print(result)

        self.memory.add_assistant_message(result[:2000])
        self.memory.extract_and_store(user_input, result)

    def _chat_with_tool(self, user_input: str):
        """使用工具调用模式（ReAct）"""
        self.memory.add_user_message(user_input)
        print(f"\n[{settings.AGENT_NAME}]: 正在启动工具调用模式...\n")
        result = self.tool_agent.process(user_input)
        print(f"\n{result}")
        self.memory.add_assistant_message(result[:2000])
        self.memory.extract_and_store(user_input, result)

    def _chat_with_task(self, user_input: str):
        """自主任务模式：一句话完成工作（规划→执行→验证→交付）"""
        self.memory.add_user_message(user_input)
        print(f"\n[{settings.AGENT_NAME}]: 自主任务引擎启动，正在规划并执行...\n")
        result = ""
        for event in self.task_agent.process(user_input):
            etype = event["type"]
            if etype == "plan":
                print("\n" + "─" * 50)
                print("  📋 任务计划")
                print("─" * 50)
                print(event["content"])
                print()
            elif etype == "tool_call":
                print(f"\n  ⚙️  {event['content']}")
            elif etype == "tool_result":
                # 只打印截断的工具结果
                text = event["content"]
                if len(text) > 400:
                    print(f"     {text[:400]}...")
                else:
                    print(f"     {text}")
            elif etype == "done":
                result = event["content"]
                print("\n" + "=" * 60)
                print("  ✅ 任务完成")
                print("=" * 60)
                print(result)
                print()
                if event.get("files"):
                    print("\n产出文件：")
                    for f in event["files"]:
                        print(f"  📄 {f}")
                print()
        self.memory.add_assistant_message(result[:2000])
        self.memory.extract_and_store(user_input, result)

    def show_tools(self):
        """显示所有可用工具"""
        stats = self.tool_agent.get_tool_stats()
        print("\n" + "="*50)
        print("  可用工具列表")
        print("="*50)
        print(f"  已注册工具数: {stats['已注册工具数']}")
        print(f"  可用工具数: {stats['可用工具数']}")
        print()

        tools = self.tool_agent.tool_manager.get_available_tools()
        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {tool['name']}")
            print(f"     描述: {tool['description'][:60]}...")
            params = list(tool['parameters'].keys())
            print(f"     参数: {', '.join(params)}")
            print()

        print("="*50)
        print("使用 /tool 强制下一条消息使用工具调用模式")
        print("="*50 + "\n")

    def show_agents(self):
        """显示所有场景 Agent"""
        stats = self.agent_manager.get_stats()
        print("\n" + "="*50)
        print("  场景化 Agent 列表")
        print("="*50)
        print(f"  可用场景数: {stats['可用场景数']}")
        print(f"  历史调用次数: {stats['历史调用次数']}")
        print()

        for scene in stats['可用场景']:
            info = self.agent_manager.get_agent_info(scene)
            print(f"  【{scene} Agent】")
            print(f"    描述: {info.get('scene_description', '')}")
            print(f"    工具: {', '.join(info.get('tools', []))}")
            print()

        print("="*50)
        print("使用 /scene <场景名> 强制下一条消息使用指定 Agent")
        print("示例: /scene 编程 | /scene 论文 | /scene 办公 | /scene 视频")
        print("="*50 + "\n")

    def show_memory_stats(self):
        """显示记忆统计"""
        stats = self.memory.get_memory_stats()
        print("\n" + "="*40)
        print("  记忆系统统计")
        print("="*40)
        print(f"  [短期记忆]")
        print(f"    当前会话: {stats['短期记忆']['当前会话']}")
        print(f"    历史会话数: {stats['短期记忆']['历史会话数']}")
        print(f"    当前消息数: {stats['短期记忆']['当前消息数']}")
        print(f"  [长期记忆]")
        print(f"    用户偏好: {stats['长期记忆']['preferences_count']} 条")
        print(f"    FAQ库: {stats['长期记忆']['faq_count']} 条")
        print(f"    历史经验: {stats['长期记忆']['experiences_count']} 条")
        print(f"    知识库: {stats['长期记忆']['knowledge_count']} 条")
        print("="*40 + "\n")

    def show_sessions(self):
        """列出历史会话"""
        sessions = self.memory.list_sessions()
        if not sessions:
            print("\n[系统] 暂无历史会话\n")
            return
        print("\n" + "="*50)
        print("  历史会话列表")
        print("="*50)
        for i, s in enumerate(sessions, 1):
            print(f"  {i}. [{s['session_id']}] {s['title']}")
            print(f"     创建: {s['created_at'][:19]} | 消息数: {s['message_count']}")
        print("="*50)
        print("使用 /load <会话ID> 加载指定会话\n")

    def load_session(self, session_id: str):
        """加载历史会话"""
        if self.memory.load_session(session_id):
            print(f"\n[系统] 会话 {session_id} 已加载，继续对话吧。\n")
        else:
            print(f"\n[系统] 会话 {session_id} 不存在。\n")

    def new_session(self):
        """新建会话"""
        self.memory.start_new_session("新对话")
        if self.system_prompt:
            self.memory.add_system_message(self.system_prompt)
        print("\n[系统] 已创建新会话，历史会话已保存。\n")

    def show_preferences(self):
        """显示用户偏好"""
        prefs = self.memory.long_term.get_preferences()
        if not prefs:
            print("\n[系统] 暂无记录的用户偏好\n")
            return
        print("\n" + "="*40)
        print("  用户偏好")
        print("="*40)
        for p in prefs:
            print(f"  [{p['category']}] {p['key']}: {p['value']}")
            if p.get('note'):
                print(f"    备注: {p['note']}")
        print("="*40 + "\n")

    def show_stats(self):
        """显示综合统计"""
        print("\n" + "="*50)
        print("  智能体综合统计")
        print("="*50)

        # 记忆统计
        mem_stats = self.memory.get_memory_stats()
        print(f"  [记忆系统]")
        print(f"    历史会话: {mem_stats['短期记忆']['历史会话数']} 个")
        print(f"    用户偏好: {mem_stats['长期记忆']['preferences_count']} 条")
        print(f"    FAQ: {mem_stats['长期记忆']['faq_count']} 条")
        print(f"    经验: {mem_stats['长期记忆']['experiences_count']} 条")
        print(f"    知识: {mem_stats['长期记忆']['knowledge_count']} 条")

        # Agent 统计
        agent_stats = self.agent_manager.get_stats()
        print(f"\n  [场景Agent]")
        print(f"    可用场景: {', '.join(agent_stats['可用场景'])}")
        print(f"    历史调用: {agent_stats['历史调用次数']} 次")

        # 工作流统计
        wf_stats = self.workflow_manager.get_workflow_stats()
        print(f"\n  [工作流]")
        print(f"    历史执行: {wf_stats['历史执行次数']} 次")

        print("="*50 + "\n")

    def run(self):
        """运行交互循环"""
        while True:
            try:
                user_input = input("[你]: ").strip()
                if not user_input:
                    continue

                # 命令处理
                if user_input.lower() == "exit":
                    print(f"\n[{settings.AGENT_NAME}] 再见！所有记忆已保存，期待下次为你服务。")
                    break
                if user_input.lower() == "clear":
                    self.memory.clear_current_session()
                    continue
                if user_input.lower() == "/memory":
                    self.show_memory_stats()
                    continue
                if user_input.lower() == "/sessions":
                    self.show_sessions()
                    continue
                if user_input.lower() == "/new":
                    self.new_session()
                    continue
                if user_input.lower() == "/prefs":
                    self.show_preferences()
                    continue
                if user_input.lower() == "/agents":
                    self.show_agents()
                    continue
                if user_input.lower() == "/tools":
                    self.show_tools()
                    continue
                if user_input.lower() == "/tool":
                    self.force_tool = True
                    print("[系统] 下一条消息将强制使用工具调用模式\n")
                    continue
                if user_input.lower() == "/workflow":
                    self.force_workflow = True
                    print("[系统] 下一条消息将强制使用通用五阶闭环工作流\n")
                    continue
                if user_input.lower() == "/quick":
                    self.force_quick = True
                    print("[系统] 下一条消息将强制使用快速对话\n")
                    continue
                if user_input.lower() == "/task":
                    self.force_task = True
                    print("[系统] 下一条消息将强制使用自主任务模式（一句话完成工作）\n")
                    continue
                if user_input.lower() == "/stats":
                    self.show_stats()
                    continue
                if user_input.startswith("/scene "):
                    scene = user_input[7:].strip()
                    if scene in self.agent_manager.get_available_scenes():
                        self.force_scene = scene
                        print(f"[系统] 下一条消息将强制使用 {scene} 场景 Agent\n")
                    else:
                        print(f"[系统] 未知场景: {scene}，可用场景: {', '.join(self.agent_manager.get_available_scenes())}\n")
                    continue
                if user_input.startswith("/load "):
                    session_id = user_input[6:].strip()
                    self.load_session(session_id)
                    continue

                # 正常对话
                self.chat(user_input)

            except KeyboardInterrupt:
                print("\n\n[系统] 已中断输入")
                continue
            except Exception as e:
                print(f"\n[错误] {type(e).__name__}: {e}\n")


if __name__ == "__main__":
    agent = Agent()
    agent.run()
