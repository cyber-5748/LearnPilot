# ============================================================
# 阶段 2：多轮对话
# ============================================================
#
# 运行方式：
#   D:/software/miniconda/envs/13/python.exe learn/02_conversation.py
#
# 你会学到：
#   - LLM 本身没有记忆，"记忆"是怎么实现的
#   - 用列表保存对话历史
#   - while 循环 + input() 实现持续对话
#   - 输入 "退出" 结束程序
# ============================================================

import sys
import os
from dotenv import load_dotenv
from openai import OpenAI

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)
model = os.getenv("LLM_MODEL")

# ---------- 关键：对话历史列表 ----------
#
# LLM 本身没有记忆，每次调用都是全新的。
# "记住你说过什么"的原理是：
#   把所有历史消息都放进列表，每次调用时一起发给 LLM。
#
# 第 1 轮发：[system, user1]
# 第 2 轮发：[system, user1, assistant1, user2]
# 第 3 轮发：[system, user1, assistant1, user2, assistant2, user3]
# ...以此类推
#
messages = [
    {
        "role": "system",
        "content": "你是一个耐心的编程老师，用简洁的中文回答问题。记住用户说过的内容。",
    }
]

print("=" * 40)
print("LearnPilot 对话开始")
print("输入 '退出' 结束对话")
print("=" * 40)

# ---------- 主循环 ----------
while True:
    # 1. 读取用户输入
    user_input = input("\n你：").strip()

    # 2. 检查是否退出
    if user_input == "退出":
        print("对话结束，再见！")
        break

    # 3. 跳过空输入
    if not user_input:
        continue

    # 4. 把用户消息加入历史列表
    messages.append({
        "role": "user",
        "content": user_input,
    })

    # 5. 把完整历史发给 LLM
    response = client.chat.completions.create(
        model=model,
        messages=messages,   # ← 每次都发完整历史，这就是"记忆"的实现方式
    )

    # 6. 取出 AI 回复
    reply = response.choices[0].message.content

    # 7. 把 AI 回复也加入历史列表（下一轮会一起发给 LLM）
    messages.append({
        "role": "assistant",
        "content": reply,
    })

    # 8. 打印 AI 回复
    print(f"\nAI：{reply}")

    # ---------- 小彩蛋：看看历史列表有多长 ----------
    print(f"\n（当前对话共 {len(messages)} 条消息）")
