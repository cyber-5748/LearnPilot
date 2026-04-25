# ============================================================
# 阶段 4：给 AI 一个工具（Function Calling）
# ============================================================
#
# 运行方式：
#   D:/software/miniconda/envs/13/python.exe learn/04_tools.py
#
# 你会学到：
#   - 为什么 LLM 需要工具（它不知道最新信息、不会计算）
#   - 怎么定义一个工具（告诉 AI 工具叫什么、能做什么、需要什么参数）
#   - AI 如何"决定"用不用工具
#   - 工具调用的完整流程（ReAct 模式）：
#       1. 用户提问
#       2. AI 思考：需要用工具吗？
#       3. 如果需要：AI 返回"我要调用工具X，参数是Y"
#       4. 你的程序真正执行这个工具，得到结果
#       5. 把结果告诉 AI
#       6. AI 根据结果给出最终回答
# ============================================================

import sys
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)
model = os.getenv("LLM_MODEL")


# ============================================================
# 第一步：定义真实的工具函数（普通 Python 函数）
# ============================================================

def search_knowledge(query: str) -> str:
    """
    模拟搜索知识库。
    真实项目里这里会调用 Tavily 搜索或查询数据库，
    现在先用假数据演示流程。
    """
    # 模拟知识库数据
    knowledge_base = {
        "python": "Python 是一门高级编程语言，1991年由 Guido van Rossum 创建，以简洁易读著称。",
        "langchain": "LangChain 是一个构建 LLM 应用的框架，提供链式调用、工具集成、记忆管理等功能。",
        "langgraph": "LangGraph 是 LangChain 团队开发的 Agent 编排框架，用有向图描述 Agent 的工作流程。",
        "agent": "AI Agent 是能够感知环境、做出决策、调用工具来完成任务的 AI 系统，而不仅仅是问答。",
    }
    query_lower = query.lower()
    for keyword, info in knowledge_base.items():
        if keyword in query_lower:
            return info
    return f"知识库中未找到关于 '{query}' 的信息。"


def calculate(expression: str) -> str:
    """
    计算数学表达式。
    LLM 不擅长精确计算，这种事交给程序来做更可靠。
    """
    try:
        result = eval(expression)   # 注意：生产环境不要用 eval，这里仅作演示
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算出错：{e}"


# ============================================================
# 第二步：把工具"描述"给 AI
# ============================================================
# AI 不能直接调用你的 Python 函数，
# 你需要用 JSON 格式告诉它：
#   - 工具叫什么名字
#   - 能做什么（description，这很重要，AI 靠这个决定用不用它）
#   - 需要什么参数

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",           # 函数名（要和上面定义的一致）
            "description": "搜索知识库，获取编程概念的解释。当用户询问某个技术概念时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "要搜索的关键词，例如 'Python'、'LangGraph'",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算数学表达式，例如加减乘除。当用户需要精确计算时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，例如 '123 * 456' 或 '(10 + 5) / 3'",
                    }
                },
                "required": ["expression"],
            },
        },
    },
]

# 工具名 → 真实函数 的映射表，后面执行工具时用
tool_map = {
    "search_knowledge": search_knowledge,
    "calculate": calculate,
}


# ============================================================
# 第三步：完整的工具调用流程
# ============================================================

def chat_with_tools(user_question: str):
    print(f"\n用户：{user_question}")
    print("-" * 40)

    messages = [
        {"role": "system", "content": "你是编程老师。回答问题时，如果需要查资料就用搜索工具，需要计算就用计算工具。"},
        {"role": "user",   "content": user_question},
    ]

    # --- 第一次调用：让 AI 决定要不要用工具 ---
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,                    # 把工具列表告诉 AI
        tool_choice="auto",             # "auto" = AI 自己决定用不用工具
    )

    msg = response.choices[0].message

    # --- 判断 AI 的决定 ---
    if not msg.tool_calls:
        # AI 认为不需要工具，直接给出答案
        print(f"AI（直接回答）：{msg.content}")
        return

    # AI 决定使用工具
    print(f"AI 决定使用工具，共 {len(msg.tool_calls)} 个调用：")

    # 把 AI 的"我要调用工具"这条消息加入历史
    messages.append(msg)

    # --- 逐个执行 AI 要求的工具调用 ---
    for tool_call in msg.tool_calls:
        func_name = tool_call.function.name
        func_args = json.loads(tool_call.function.arguments)  # 参数是 JSON 字符串，需要解析

        print(f"  → 调用工具：{func_name}，参数：{func_args}")

        # 真正执行工具函数
        tool_result = tool_map[func_name](**func_args)

        print(f"  → 工具返回：{tool_result}")

        # 把工具执行结果加入消息列表，告诉 AI
        messages.append({
            "role": "tool",                  # role 是 "tool"，表示这是工具的返回结果
            "tool_call_id": tool_call.id,    # 对应哪次工具调用
            "content": tool_result,
        })

    # --- 第二次调用：AI 根据工具结果给出最终答案 ---
    final_response = client.chat.completions.create(
        model=model,
        messages=messages,
    )

    print(f"\nAI（综合工具结果后回答）：{final_response.choices[0].message.content}")


# ============================================================
# 测试三种场景
# ============================================================

# 场景1：需要搜索知识库
chat_with_tools("LangGraph 是什么？")

print("\n" + "=" * 40)

# 场景2：需要计算
chat_with_tools("123 乘以 456 等于多少？")

print("\n" + "=" * 40)

# 场景3：不需要工具，AI 直接回答
chat_with_tools("你好，请用一句话打个招呼。")
