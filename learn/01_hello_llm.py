# ============================================================
# 阶段 1：第一次和 LLM 对话
# ============================================================
#
# 运行方式：
#   D:/software/miniconda/envs/13/python.exe learn/01_hello_llm.py
#
# 你会学到：
#   - 怎么用 Python 调用 LLM API
#   - messages 列表的格式（role + content）
#   - system / user / assistant 三种角色分别是什么
# ============================================================

import sys                          # 系统模块
import os                          # 读取环境变量

# 修复 Windows 终端中文乱码问题
sys.stdout.reconfigure(encoding="utf-8")
from dotenv import load_dotenv     # 从 .env 文件加载配置
from openai import OpenAI          # LLM 客户端

# ---------- 第一步：加载配置 ----------
# load_dotenv() 会读取当前目录的 .env 文件，
# 把里面的变量加载到环境变量中
load_dotenv()

api_key  = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL")
model    = os.getenv("LLM_MODEL")

# ---------- 第二步：创建客户端 ----------
# OpenAI() 创建一个可以和 LLM 通信的客户端对象
# base_url 指定服务器地址（这里用火山引擎，不是 OpenAI 官方）
client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)

# ---------- 第三步：准备消息 ----------
#
# 和 LLM 通信时，你要发一个"消息列表"。
# 每条消息有两个字段：
#   role    - 说话的人是谁
#   content - 说的内容
#
# role 只有三种值：
#   "system"    → 你给 AI 的"人设说明"，AI 每次都会读，但用户看不到
#   "user"      → 用户说的话（你）
#   "assistant" → AI 回复的话
#
messages = [
    {
        "role": "system",
        "content": "你是一个耐心的编程老师，用简洁的中文回答问题。"
    },
    {
        "role": "user",
        "content": "用一句话解释：什么是 LLM？"
    },
]

# ---------- 第四步：发送请求，获取回复 ----------
# create() 把消息发给 LLM，等它返回回复
# 这一步会真正联网，需要 1～3 秒
print("正在调用 LLM，请稍候...\n")

response = client.chat.completions.create(
    model=model,
    messages=messages,
)

# ---------- 第五步：取出回复内容 ----------
# response 是一个复杂的对象，回复文本在这个位置：
# response.choices[0].message.content
reply = response.choices[0].message.content

print("AI 的回答：")
print(reply)
