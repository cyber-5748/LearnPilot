# ============================================================
# State：图的"共享记事本"
# ============================================================
#
# 阶段11 关键升级：messages 字段加了 Annotated + operator.add
#
# 之前的写法：
#   history: list[dict]
#   → 每次节点返回新值，直接覆盖旧值
#
# 现在的写法：
#   messages: Annotated[list[dict], operator.add]
#   → 每次节点返回新消息列表，自动追加（append）到已有的列表
#
# 为什么这很重要？
#   有了 Checkpointer 之后，State 会被持久化保存。
#   下次用同一个 thread_id 调用图时，messages 会从数据库恢复。
#   如果用"覆盖"语义，历史就丢了；
#   用"追加"语义，每次对话都会累积在 messages 里。
#
# 同时：有了 Checkpointer，不再需要 load_history / save_history 节点，
#       LangGraph 自动处理保存和恢复。
# ============================================================

import operator
from typing import Annotated, TypedDict


class AgentState(TypedDict):
    session_id:   str                              # 当前会话 ID（同 thread_id）
    user_message: str                              # 用户这次发的消息（每次覆盖）
    messages:     Annotated[list[dict], operator.add]  # 对话历史（自动追加）
    intent:       str                              # 意图识别结果（每次覆盖）
    context:      list[str]                        # RAG 本地检索结果（每次覆盖）
    web_results:  list[str]                        # Tavily 网络搜索结果（每次覆盖）
    reply:        str                              # LLM 回复（每次覆盖）
