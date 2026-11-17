"""
工具调用系统测试
验证：工具注册、工具管理器、代码执行、文件读写、目录列表等
"""
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.tool_manager import ToolManager
from tools.code_executor import CodeExecutorTool
from tools.file_tools import FileReadTool, FileWriteTool
from tools.system_tools import PackageInstallTool, CommandTool, DirectoryListTool


def test_tool_registration():
    """测试1：工具注册和管理"""
    print("\n" + "="*50)
    print("测试1：工具注册和管理")
    print("="*50)

    manager = ToolManager()
    stats = manager.get_stats()

    print(f"  已注册工具数: {stats['已注册工具数']}")
    print(f"  可用工具数: {stats['可用工具数']}")
    print(f"  工具列表: {stats['工具列表']}")

    # 检查所有默认工具是否注册
    expected_tools = ["code_executor", "file_read", "file_write",
                      "package_install", "command_executor", "directory_list"]
    all_registered = True
    for tool_name in expected_tools:
        tool = manager.get_tool(tool_name)
        if tool:
            print(f"  ✓ {tool_name}: {tool.tool_description[:40]}...")
        else:
            print(f"  ✗ {tool_name}: 未注册")
            all_registered = False

    # 测试工具描述生成
    description = manager.get_tools_description()
    print(f"\n  工具描述长度: {len(description)} 字符")

    print(f"\n工具注册测试: {'通过' if all_registered else '失败'}")
    return all_registered


def test_code_executor():
    """测试2：代码执行工具"""
    print("\n" + "="*50)
    print("测试2：代码执行工具")
    print("="*50)

    executor = CodeExecutorTool()

    # 测试1：简单代码
    print("\n  测试2.1：简单代码执行")
    result = executor.execute(code="print('Hello, 智能体!')\nprint(1+1)")
    print(f"  成功: {result['success']}")
    print(f"  结果: {result['result'][:100]}...")
    test1_pass = result['success'] and "Hello" in result['result']

    # 测试2：计算代码
    print("\n  测试2.2：计算代码执行")
    code = """
import math
result = sum(range(1, 101))
print(f"1到100的和: {result}")
print(f"圆周率: {math.pi:.4f}")
"""
    result = executor.execute(code=code)
    print(f"  成功: {result['success']}")
    print(f"  结果: {result['result'][:100]}...")
    test2_pass = result['success'] and "5050" in result['result']

    # 测试3：错误代码
    print("\n  测试2.3：错误代码处理")
    result = executor.execute(code="print(undefined_variable)")
    print(f"  成功: {result['success']}")
    print(f"  包含错误信息: {'NameError' in result['result'] or '错误' in result['result']}")
    test3_pass = result['success']  # 工具执行成功，代码本身报错是正常的

    all_pass = test1_pass and test2_pass and test3_pass
    print(f"\n代码执行工具测试: {'通过' if all_pass else '部分失败'}")
    return all_pass


def test_file_tools():
    """测试3：文件读写工具"""
    print("\n" + "="*50)
    print("测试3：文件读写工具")
    print("="*50)

    # 创建临时测试文件
    temp_dir = tempfile.mkdtemp()
    test_file = os.path.join(temp_dir, "test.txt")

    # 测试写入
    print("\n  测试3.1：文件写入")
    writer = FileWriteTool()
    result = writer.execute(file_path=test_file, content="这是测试内容\n第二行\n第三行")
    print(f"  成功: {result['success']}")
    print(f"  结果: {result['result'][:80]}...")
    test1_pass = result['success'] and os.path.exists(test_file)

    # 测试读取
    print("\n  测试3.2：文件读取")
    reader = FileReadTool()
    result = reader.execute(file_path=test_file)
    print(f"  成功: {result['success']}")
    print(f"  内容正确: {'测试内容' in result['result']}")
    test2_pass = result['success'] and "测试内容" in result['result']

    # 测试读取不存在的文件
    print("\n  测试3.3：读取不存在的文件")
    result = reader.execute(file_path=os.path.join(temp_dir, "nonexistent.txt"))
    print(f"  成功: {result['success']}（应为 False）")
    print(f"  错误信息: {result['error'][:50]}...")
    test3_pass = not result['success']

    # 清理
    os.unlink(test_file)
    os.rmdir(temp_dir)

    all_pass = test1_pass and test2_pass and test3_pass
    print(f"\n文件读写工具测试: {'通过' if all_pass else '部分失败'}")
    return all_pass


def test_system_tools():
    """测试4：系统工具（目录列表、命令执行）"""
    print("\n" + "="*50)
    print("测试4：系统工具")
    print("="*50)

    # 测试目录列表
    print("\n  测试4.1：目录列表工具")
    dir_tool = DirectoryListTool()
    project_dir = os.path.dirname(os.path.abspath(__file__))
    result = dir_tool.execute(directory=project_dir)
    print(f"  成功: {result['success']}")
    print(f"  包含 main.py: {'main.py' in result['result']}")
    test1_pass = result['success']

    # 测试命令执行
    print("\n  测试4.2：命令执行工具")
    cmd_tool = CommandTool()
    result = cmd_tool.execute(command="echo 测试命令执行成功")
    print(f"  成功: {result['success']}")
    print(f"  结果包含输出: {'测试命令' in result['result'] or '成功' in result['result']}")
    test2_pass = result['success']

    # 测试安全限制
    print("\n  测试4.3：危险命令拦截")
    result = cmd_tool.execute(command="format C:")
    print(f"  成功: {result['success']}（应为 False）")
    print(f"  被拦截: {'安全限制' in result['error']}")
    test3_pass = not result['success']

    all_pass = test1_pass and test2_pass and test3_pass
    print(f"\n系统工具测试: {'通过' if all_pass else '部分失败'}")
    return all_pass


def test_tool_manager_execute():
    """测试5：工具管理器统一调度"""
    print("\n" + "="*50)
    print("测试5：工具管理器统一调度")
    print("="*50)

    manager = ToolManager()

    # 通过管理器执行代码
    print("\n  测试5.1：通过管理器执行代码")
    result = manager.execute_tool("code_executor", code="print('通过管理器执行成功')")
    print(f"  成功: {result['success']}")
    print(f"  结果: {result['result'][:80]}...")
    test1_pass = result['success']

    # 测试不存在的工具
    print("\n  测试5.2：调用不存在的工具")
    result = manager.execute_tool("nonexistent_tool", param1="value")
    print(f"  成功: {result['success']}（应为 False）")
    print(f"  错误: {result['error']}")
    test2_pass = not result['success']

    all_pass = test1_pass and test2_pass
    print(f"\n工具管理器调度测试: {'通过' if all_pass else '部分失败'}")
    return all_pass


if __name__ == "__main__":
    print("\n" + "#"*50)
    print("#  工具调用系统测试")
    print("#"*50)

    results = {}
    results["工具注册"] = test_tool_registration()
    results["代码执行"] = test_code_executor()
    results["文件读写"] = test_file_tools()
    results["系统工具"] = test_system_tools()
    results["管理器调度"] = test_tool_manager_execute()

    print("\n" + "="*50)
    print("测试结果汇总")
    print("="*50)
    all_pass = True
    for name, ok in results.items():
        status = "通过" if ok else "失败"
        print(f"  {name}: {status}")
        if not ok:
            all_pass = False

    print("="*50)
    if all_pass:
        print("工具调用系统全部测试通过！")
        print("运行 python main.py 启动智能体，输入 /tools 查看可用工具")
        print("输入 /tool 强制下一条消息使用工具调用模式")
    else:
        print("部分测试失败，请检查上方错误信息。")
    print("="*50)
