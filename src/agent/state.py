"""
聊天 Agent 的共享状态定义。

messages 使用 Annotated[list, operator.add] 实现追加语义，
配合 SqliteSaver Checkpointer 自动持久化对话历史。
"""

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
