"""Agent 核心：ReAct 循环（推理 → 工具调用 → 观察 → ... → 最终输出）。

同时内置上下文记忆（保留完整对话历史）与步骤上限保护。
"""
from agent import llm
from agent.tools import TOOL_SPECS, execute_tool

MAX_STEPS = 12  # 单轮问答中工具调用循环的上限，防止死循环烧钱

SYSTEM_PROMPT = """你是一个专业的代码解释助手（Code Explainer Agent）。

你的职责：
- 解释代码的逻辑、结构与执行流程
- 为代码生成清晰的中文注释
- 回答用户关于代码的各种问题
- 必要时运行代码来验证你对行为的推断

工作方式（重要）：
1. 当用户提到一个文件或目录时，先用 read_file / search_code 工具获取真实源码，
   绝不要凭空猜测代码内容
2. 需要验证行为时，用 execute_python 工具实际运行代码片段
3. 解释时使用简体中文，结构清晰：先概述功能，再逐段解释关键逻辑
4. 如果用户的问题与代码无关，礼貌地说明你专注于代码解释领域

回答风格：
- 用 Markdown 组织内容（标题、列表、代码块）
- 解释代码时引用行号或函数名，方便用户定位
- 复杂概念配合简单的例子说明
"""


class CodeExplainerAgent:
    """代码解释 Agent：封装上下文记忆与 ReAct 决策循环。"""

    def __init__(self):
        self.messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    # ---------- 对外接口 ----------

    def run(self, user_input: str) -> str:
        """处理一轮用户输入，返回最终回答。

        内部循环：LLM 推理 → 若要求调用工具则执行并回填结果 → 直到给出最终回答。
        """
        self.messages.append({"role": "user", "content": user_input})

        for step in range(1, MAX_STEPS + 1):
            message = llm.chat(self.messages, tools=TOOL_SPECS)
            self.messages.append(message)  # 记入历史，实现多轮上下文记忆

            tool_calls = getattr(message, "tool_calls", None)
            if not tool_calls:
                return message.content or "（模型未返回内容）"

            # 模型要求调用工具：执行并把结果作为 tool 消息回填
            for call in tool_calls:
                name = call.function.name
                import json
                try:
                    arguments = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    arguments = {}
                print(f"  [工具调用 {step}] {name}({arguments})")

                result = execute_tool(name, arguments)
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                })

        return f"已达到单轮最大步骤数（{MAX_STEPS}），为节省费用提前停止。可换个更具体的问题再试。"

    def reset(self) -> None:
        """清空对话历史，开始新会话。"""
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    @property
    def history_size(self) -> int:
        """当前记忆的消息条数（用于展示）。"""
        return len(self.messages)
