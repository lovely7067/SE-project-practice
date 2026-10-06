# 代码解释 Agent (Code Explainer Agent)

一个基于 LLM 的命令行代码助手：阅读真实源码，解释代码逻辑、生成注释、回答代码问题，并能实际运行 Python 片段验证行为。

## 功能特性

- **Agent 循环**：输入 → LLM 推理 → 工具调用 → 结果回传 → 最终输出（ReAct 模式）
- **三种工具**
  | 工具 | 说明 |
  |---|---|
  | `read_file` | 读取代码文件（带行号，限制 100KB） |
  | `search_code` | 按正则在目录中搜索代码（自动跳过 .git 等目录） |
  | `execute_python` | 沙箱执行 Python 片段（子进程隔离，15 秒超时） |
- **上下文记忆**：保留完整对话历史，支持多轮追问
- **健壮性**：LLM 调用指数退避重试（3 次）、工具异常不中断循环、单轮步骤上限（12 步）防死循环

## 快速开始

### 环境要求

- Python 3.10+
- 一个 LLM API Key（默认使用 DeepSeek）

### 安装

```bash
cd code-explainer-agent
pip install -r requirements.txt

# 配置 API Key
copy .env.example .env   # Windows
# 然后编辑 .env，填入 LLM_API_KEY=sk-xxxx
```

DeepSeek API Key 获取：https://platform.deepseek.com （API Keys → 创建）

### 运行

```bash
python main.py                 # 交互模式
python main.py -f main.py      # 启动即解释指定文件
```

交互示例：

```
你> 解释一下 agent/agent.py 的整体逻辑
  [工具调用 1] read_file({'path': 'agent/agent.py'})
Agent> （分段的中文解释……）

你> 那它最多会循环多少步？
Agent> MAX_STEPS = 12 步，防止死循环……
```

命令：`/help` 帮助 | `/reset` 清空记忆 | `/exit` 退出

> Windows 若出现中文乱码，先执行 `chcp 65001` 切换终端为 UTF-8 编码，或直接在 PyCharm / VS Code 的终端中运行。

### 更换 LLM 服务商

编辑 `.env`：

```
LLM_API_KEY=你的Key
LLM_BASE_URL=https://api.deepseek.com   # 换成其他 OpenAI 兼容服务地址
LLM_MODEL=deepseek-chat
```

兼容 OpenAI 协议的服务（DeepSeek、通义千问兼容模式、Kimi 等）均可直接替换。

## 项目结构

```
code-explainer-agent/
├── main.py              # 命令行入口（REPL 交互）
├── agent/
│   ├── llm.py           # LLM 调用封装（重试机制）
│   ├── tools.py         # 工具定义与实现（read/search/execute）
│   └── agent.py         # Agent 核心：ReAct 循环 + 上下文记忆
├── requirements.txt
├── .env.example         # 环境变量模板
├── README.md            # 本文件
└── Design.md            # 设计文档
```
