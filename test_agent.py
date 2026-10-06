"""端到端冒烟测试：验证 Agent 循环、工具调用与上下文记忆。

运行：python test_agent.py
"""
from agent.agent import CodeExplainerAgent


def check(name: str, cond: bool, detail: str = ""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}" + (f"  -> {detail}" if detail and not cond else ""))
    return cond


def msg_role(m) -> str:
    """兼容 dict 消息与 ChatCompletionMessage 对象两种形态。"""
    if isinstance(m, dict):
        return m.get("role", "")
    return getattr(m, "role", "") or ""


agent = CodeExplainerAgent()
all_pass = True

# 测试1：工具调用 + 代码解释（应先调用 read_file 再回答）
print("=" * 50)
print("测试1：让 Agent 解释本项目的 main.py（应触发 read_file）")
answer1 = agent.run("请简要解释 main.py 这个文件的作用，控制在150字内")
print(f"回答：{answer1[:200]}...")
used_tool = any(msg_role(m) == "tool" for m in agent.messages)
all_pass &= check("Agent 通过工具读取了文件", used_tool)
all_pass &= check("返回了中文解释", len(answer1) > 30)

# 测试2：上下文记忆（追问上一轮话题，无需重新读文件）
print("=" * 50)
print("测试2：多轮记忆（追问 main.py 中的细节）")
before = len(agent.messages)
answer2 = agent.run("它支持哪些命令行参数？")
print(f"回答：{answer2[:200]}...")
all_pass &= check("第二轮回答非空", len(answer2) > 10)
all_pass &= check("对话历史持续增长（记忆生效）", len(agent.messages) > before)

# 测试3：代码执行工具（让 Agent 实际运行代码）
print("=" * 50)
print("测试3：让 Agent 用工具执行一段代码")
answer3 = agent.run("用工具执行代码验证一下：1到100求和是多少？")
print(f"回答：{answer3[:200]}...")
all_pass &= check("回答包含正确结果 5050", "5050" in answer3)

print("=" * 50)
print("全部通过！" if all_pass else "存在失败项，请检查上方日志。")
raise SystemExit(0 if all_pass else 1)
