# ============================================================
# 节点（Node）：每个节点做一件具体的事
# ============================================================

from openai import OpenAI
from src.config import settings
from src.rag.knowledge_base import search as kb_search
from src.tools.search import web_search
from src.agent.state import AgentState

LEARN_PROMPT = """你是 LearnPilot，一个耐心的 AI 编程老师。
当用户提问时：
1. 先用一句话解释核心概念
2. 再给一个简短的代码示例（如果适用）
3. 最后问用户有没有不懂的地方
用简洁的中文回答。"""

CHAT_PROMPT = """你是 LearnPilot，一个友好的 AI 学习伙伴。
用轻松自然的中文和用户聊天，保持简短。"""


# ── 节点1：意图识别 ───────────────────────────────────────────

def classify_intent_node(state: AgentState) -> dict:
    """判断用户消息是"学习"还是"闲聊"。"""
    classify_prompt = """判断下面这句话的意图，只输出一个词：
- 如果是编程、技术、学习、代码相关的问题，输出：学习
- 如果是日常闲聊、问好、随便聊聊，输出：闲聊
只输出"学习"或"闲聊"，不要输出其他内容。"""

    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
    resp = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": classify_prompt},
            {"role": "user",   "content": state["user_message"]},
        ],
        max_tokens=10,
    )
    raw    = resp.choices[0].message.content.strip()
    intent = "学习" if "学习" in raw else "闲聊"
    print(f"[意图识别] '{state['user_message']}' → {intent}")
    return {"intent": intent}


# ── 节点2：本地 RAG 检索 ──────────────────────────────────────

def retrieve_context_node(state: AgentState) -> dict:
    """从本地知识库检索相关片段。"""
    chunks = kb_search(state["user_message"], n_results=3)
    print(f"[RAG] 检索到 {len(chunks)} 个本地片段")
    return {"context": chunks}


# ── 节点3：网络搜索（新增）───────────────────────────────────

def web_search_node(state: AgentState) -> dict:
    """
    用 Tavily 搜索网络，补充本地知识库没有的内容。

    设计决策：不管本地有没有检索到内容，都执行网络搜索。
    理由：本地知识库是静态的，网络能提供更新、更全的信息。
    后续迭代点：可以判断本地结果是否足够，不够时才搜网络。
    """
    results = web_search(state["user_message"], max_results=3)
    return {"web_results": results}


# ── 节点4：学习问题回复（升级：融合本地+网络两路结果）──────────

def call_llm_learn_node(state: AgentState) -> dict:
    """用教学风格回复，融合本地 RAG 结果、网络搜索结果和对话历史。"""

    # 拼装参考资料：本地知识库 + 网络搜索
    context     = state.get("context", [])
    web_results = state.get("web_results", [])
    all_sources = []

    if context:
        all_sources.append("【本地知识库】\n" + "\n\n".join(context))
    if web_results:
        all_sources.append("【网络搜索结果】\n" + "\n\n".join(web_results))

    if all_sources:
        system = (
            LEARN_PROMPT
            + "\n\n【参考资料】\n"
            + "以下资料来自实时检索，内容是最新的。请直接基于这些资料回答，"
            + "不要说自己无法获取最新信息或没有联网能力。\n\n"
            + "\n\n---\n\n".join(all_sources)
        )
    else:
        system = LEARN_PROMPT

    messages = [{"role": "system", "content": system}]
    messages.extend(state["messages"])
    messages.append({"role": "user", "content": state["user_message"]})

    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
    resp   = client.chat.completions.create(model=settings.llm_model, messages=messages)
    reply  = resp.choices[0].message.content

    return {
        "reply": reply,
        "messages": [
            {"role": "user",      "content": state["user_message"]},
            {"role": "assistant", "content": reply},
        ],
    }


# ── 节点5：闲聊回复 ──────────────────────────────────────────

def call_llm_chat_node(state: AgentState) -> dict:
    """用轻松风格回复闲聊。"""
    messages = [{"role": "system", "content": CHAT_PROMPT}]
    messages.extend(state["messages"])
    messages.append({"role": "user", "content": state["user_message"]})

    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
    resp   = client.chat.completions.create(model=settings.llm_model, messages=messages)
    reply  = resp.choices[0].message.content

    return {
        "reply": reply,
        "messages": [
            {"role": "user",      "content": state["user_message"]},
            {"role": "assistant", "content": reply},
        ],
    }


# ── 路由函数 ─────────────────────────────────────────────────

def route_by_intent(state: AgentState) -> str:
    return state["intent"]
