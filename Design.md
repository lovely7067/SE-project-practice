# 设计文档 (Design.md)

## 1. 项目定位

代码解释 Agent：面向开发者的命令行助手，能读取真实源码并用自然语言解释、生成注释、回答代码问题。不依赖重型 Agent 框架，使用 LLM 原生 API（OpenAI 兼容协议，Function Calling）自研 Agent 循环，架构清晰、依赖极简（仅 `openai` + `python-dotenv`）。

## 2. 总体架构

```
┌─────────────┐     ┌──────────────────────────────────────┐
│  CLI (REPL) │────▶│            Agent 核心层               │
│   main.py   │     │  CodeExplainerAgent (agent/agent.py)  │
└─────────────┘     └──────┬───────────────────┬───────────┘
                           │ ReAct 循环        │ 上下文记忆
                    ┌──────▼──────┐     ┌──────▼──────┐
                    │  LLM 调用层  │     │ 消息历史列表 │
                    │ agent/llm.py│     └─────────────┘
                    │ (重试+退避)  │
                    └──────┬──────┘
                           │ Function Calling
                    ┌──────▼──────────────────────┐
                    │        工具层 (tools.py)     │
                    │ read_file / search_code /   │
                    │ execute_python (沙箱子进程)  │
                    └─────────────────────────────┘
```

## 3. 核心流程：ReAct 循环

`CodeExplainerAgent.run(user_input)` 的执行流程：

1. 用户输入追加到消息历史
2. 调用 LLM（携带工具描述）
3. **若模型返回 `tool_calls`**：执行对应工具，把结果以 `role=tool` 消息回填历史，回到步骤 2
4. **若模型返回普通文本**：即为最终答案，返回给用户
5. 步骤计数达到上限 `MAX_STEPS=12` 时强制停止（防死循环、控成本）

一轮问答中模型可连续多次调用工具（例如先 `search_code` 定位、再 `read_file` 读取、最后 `execute_python` 验证），体现"推理与行动交替"的 Agent 设计模式。

## 4. 模块设计

### 4.1 LLM 层（`agent/llm.py`）
- 懒加载单例客户端；通过环境变量配置 `LLM_API_KEY / LLM_BASE_URL / LLM_MODEL`，可无改动切换任何 OpenAI 兼容服务商
- `chat()` 统一封装：指数退避重试（2s/4s），覆盖网络抖动、限流、超时

### 4.2 工具层（`agent/tools.py`）
- `TOOL_SPECS`：OpenAI Function Calling 的 JSON Schema 描述，与实现解耦，新增工具只需加一条描述 + 一个分支
- 安全边界：文件大小上限（100KB）、搜索文件数上限（200）、执行输出截断（4000 字符）、子进程超时（15 秒）
- `execute_tool()` 统一分发并兜底捕获所有异常，保证工具故障只会"返回错误文本给模型"而不会让程序崩溃

### 4.3 Agent 层（`agent/agent.py`）
- System Prompt 定义角色、职责与工作方式（强调"先读码再解释，不凭空猜测"）
- 消息历史即上下文记忆；`reset()` 开新会话
- `MAX_STEPS` 保护：单轮最多 12 次推理-工具循环

### 4.4 交互层（`main.py`）
- REPL 循环；支持 `-f` 参数预加载文件
- 内置命令：`/help`、`/reset`、`/exit`；`Ctrl+C` 优雅退出

## 5. 错误处理设计

| 故障点 | 处理方式 |
|---|---|
| 未配置 API Key | 启动时明确报错并提示操作步骤 |
| LLM 网络/限流失败 | 指数退避重试 3 次，仍失败则回报用户 |
| 工具参数缺失/非法 | 捕获 KeyError / 正则错误，转为错误文本回传模型自行纠正 |
| 代码执行超时/崩溃 | subprocess 超时终止，stdout/stderr/exit code 全量回传 |
| 工具无限循环 | MAX_STEPS=12 硬上限 |
| 上下文超长 | 文件/搜索/执行结果均截断至 4000 字符 |

## 6. 技术选型理由

- **Python**：LLM 生态最成熟，作业演示直观
- **原生 API 而非 LangChain 等框架**：Agent 循环仅约 40 行，架构透明可控，更能体现对 Agent 本质的理解（作业评审中"Agent 架构"占 30%）
- **DeepSeek**：OpenAI 兼容协议、国内直连、成本低；更换服务商只改环境变量
