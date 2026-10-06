"""命令行入口：交互式 REPL 界面。

用法：
    python main.py                 # 交互模式
    python main.py -f path/file.py # 启动时直接加载一个文件
"""
import argparse
import sys

from agent.agent import CodeExplainerAgent

BANNER = r"""
==============================================
   代码解释 Agent (Code Explainer Agent)
   能力: 读取文件 / 搜索代码 / 执行Python
   命令: /help 帮助  /reset 清空记忆  /exit 退出
==============================================
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="代码解释 Agent")
    parser.add_argument("-f", "--file", help="启动时预加载的代码文件路径")
    args = parser.parse_args()

    print(BANNER)

    try:
        agent = CodeExplainerAgent()
    except RuntimeError as e:
        print(f"[启动失败] {e}")
        sys.exit(1)

    if args.file:
        # 预加载文件：等价于用户第一句话就是"解释这个文件"
        first = f"请阅读并解释这个文件：{args.file}"
        print(f"\n你> {first}")
        answer = agent.run(first)
        print(f"\nAgent> {answer}")

    print("\n输入你的问题（例如：解释一下 ./main.py 的逻辑）\n")
    while True:
        try:
            user_input = input("你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue
        if user_input == "/exit":
            print("再见！")
            break
        if user_input == "/reset":
            agent.reset()
            print("[已清空对话记忆，记忆消息数: 1]")
            continue
        if user_input == "/help":
            print("可用命令：/help 帮助 | /reset 清空记忆 | /exit 退出\n"
                  "示例问题：\n"
                  "  - 解释一下 agent/tools.py 的整体逻辑\n"
                  "  - 搜索项目里哪里用到了 subprocess\n"
                  "  - 帮我给 main.py 生成中文注释")
            continue

        try:
            answer = agent.run(user_input)
            print(f"\nAgent> {answer}\n")
        except RuntimeError as e:
            print(f"\n[出错了] {e}\n（可用 /reset 清空记忆后重试）\n")


if __name__ == "__main__":
    main()
