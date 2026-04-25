# ============================================================
# 阶段 3：流式输出（打字机效果）
# ============================================================
#
# 运行方式：
#   D:/software/miniconda/envs/13/python.exe learn/03_streaming.py
#
# 你会学到：
#   - stream=True 是什么，和普通调用有什么区别
#   - 为什么 ChatGPT 的回答是一个字一个字出现的
#   - chunk（数据块）是什么
#   - 怎么把碎片拼成完整的回复
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

messages = [
    {"role": "system", "content": "你是一个耐心的编程老师，用简洁的中文回答问题。"},
    {"role": "user",   "content": "用3句话介绍一下 Python 语言。"},
]

# ============================================================
# 对比一：普通调用（等 AI 全部生成完，一次性返回）
# ============================================================
print("【普通调用】等待中...")

response = client.chat.completions.create(
    model=model,
    messages=messages,
    # stream 默认是 False，不写就是普通模式
)

print("【普通调用】收到完整回复：")
print(response.choices[0].message.content)

print("\n" + "=" * 40 + "\n")

# ============================================================
# 对比二：流式调用（AI 生成一个字，立刻发过来一个字）
# ============================================================
print("【流式调用】开始逐字接收：\n")

# 关键区别：加上 stream=True
stream = client.chat.completions.create(
    model=model,
    messages=messages,
    stream=True,        # ← 就是这一个参数的区别
)

# stream 是一个"迭代器"，可以用 for 循环逐块读取
# 每个 chunk（数据块）包含一小段文字
collected_text = []   # 用来收集所有碎片，最后拼成完整回复

for chunk in stream:
    # chunk.choices[0].delta.content 是这一块的文字内容
    # delta 表示"增量"，即这次新增的部分
    delta = chunk.choices[0].delta.content

    if delta:                          # delta 可能是 None，要判断一下
        print(delta, end="", flush=True)  # end="" 不换行，flush=True 立刻输出
        collected_text.append(delta)

print()  # 最后换一行

# 把所有碎片拼在一起，得到完整回复
full_reply = "".join(collected_text)

print(f"\n【拼合结果】共收到 {len(collected_text)} 个数据块，总长度 {len(full_reply)} 字符")
