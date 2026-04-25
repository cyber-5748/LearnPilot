# ============================================================
# 图（Graph）：阶段11 — Checkpointer 持久化版
# ============================================================
#
# 阶段11 核心新知识：Checkpointer
#
#   graph.compile(checkpointer=SqliteSaver(...))
#
#   作用：每次图执行完毕，自动把整个 State 存入 SQLite 数据库。
#         下次用相同 thread_id 调用时，自动恢复上次的 State。
#
#   调用方式变了：
#     之前：graph.invoke(initial_state)
#     现在：graph.invoke(initial_state, config={"configurable": {"thread_id": "xxx"}})
#
#   thread_id 相当于我们之前的 session_id，LangGraph 用它来区分不同会话。
#
#   好处：
#     - 不再需要 load_history_node / save_history_node
#     - 服务重启后记忆不丢失（存在 SQLite 文件里）
#     - 未来可以换成 PostgreSQL 等数据库，代码不用改
#
# 图结构（比之前更简洁）：
#   START
#     ↓
#   classify_intent
#     ↙           ↘
# retrieve_context  call_llm_chat
#     ↓
# call_llm_learn
#     ↘           ↙
#     （END）
# ============================================================

import sqlite3
from pathlib import Path
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from src.agent.state import AgentState
from src.agent.nodes import (
    classify_intent_node,
    retrieve_context_node,
    web_search_node,
    call_llm_learn_node,
    call_llm_chat_node,
    route_by_intent,
)

# SQLite 数据库文件路径（持久保存对话记忆）
DB_PATH = "./data/memory.db"
Path("./data").mkdir(exist_ok=True)


def build_graph():
    """构建带 Checkpointer 的 LangGraph 图。"""

    graph = StateGraph(AgentState)

    # 注册节点
    graph.add_node("classify_intent",  classify_intent_node)
    graph.add_node("retrieve_context", retrieve_context_node)
    graph.add_node("web_search",       web_search_node)       # 新增
    graph.add_node("call_llm_learn",   call_llm_learn_node)
    graph.add_node("call_llm_chat",    call_llm_chat_node)

    # 边
    # 学习路径：意图识别 → 本地检索 → 网络搜索 → LLM 回复
    # 闲聊路径：意图识别 → LLM 回复
    graph.add_edge(START, "classify_intent")
    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "学习": "retrieve_context",
            "闲聊": "call_llm_chat",
        }
    )
    graph.add_edge("retrieve_context", "web_search")      # 本地检索完，再搜网络
    graph.add_edge("web_search",       "call_llm_learn")  # 两路结果汇入 LLM
    graph.add_edge("call_llm_learn",   END)
    graph.add_edge("call_llm_chat",    END)

    # ── 关键：创建 SqliteSaver 并编译 ────────────────────────
    # SqliteSaver 需要一个 sqlite3 连接，check_same_thread=False
    # 允许多线程共享同一个连接（FastAPI 多线程环境需要）
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    return graph.compile(checkpointer=checkpointer)


agent_graph = build_graph()
