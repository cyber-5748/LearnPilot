import uuid
import copy
import sqlite3
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from openai import OpenAI

from src.agent.graph import agent_graph, DB_PATH
from src.agent.nodes import (
    classify_intent_node,
    retrieve_context_node,
    web_search_node,
    LEARN_PROMPT,
    CHAT_PROMPT,
)
from src.config import settings
from langgraph.checkpoint.sqlite import SqliteSaver
from src.storage_plans import set_session_name, delete_session_name, get_session_names, pin_session

router = APIRouter()


class ChatRequest(BaseModel):
    message:    str        = Field(..., min_length=1)
    session_id: str | None = Field(None)


class ChatResponse(BaseModel):
    reply:      str
    session_id: str


class RenameRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=60)


@router.post("/chat/stream")
def chat_stream(request: ChatRequest):
    """流式输出：SSE 格式，逐 token 推送。"""
    session_id = request.session_id or str(uuid.uuid4())

    def generate():
        from datetime import datetime, timezone
        conn  = sqlite3.connect(DB_PATH, check_same_thread=False)
        saver = SqliteSaver(conn)
        cfg   = {"configurable": {"thread_id": session_id, "checkpoint_ns": ""}}
        try:
            # 1. 加载历史消息
            existing = saver.get(cfg)
            history  = existing["channel_values"].get("messages", []) if existing else []

            # 2. 意图识别 → RAG → 网络搜索（非流式，速度快）
            tmp_state = {
                "session_id":   session_id,
                "user_message": request.message,
                "messages":     history,
                "intent":       "",
                "context":      [],
                "web_results":  [],
                "reply":        "",
            }
            tmp_state.update(classify_intent_node(tmp_state))
            intent = tmp_state["intent"]

            if intent == "学习":
                tmp_state.update(retrieve_context_node(tmp_state))
                tmp_state.update(web_search_node(tmp_state))
                sources = []
                if tmp_state.get("context"):
                    sources.append("【本地知识库】\n" + "\n\n".join(tmp_state["context"]))
                if tmp_state.get("web_results"):
                    sources.append("【网络搜索结果】\n" + "\n\n".join(tmp_state["web_results"]))
                if sources:
                    system = (
                        LEARN_PROMPT
                        + "\n\n【参考资料】\n"
                        + "以下资料来自实时检索，内容是最新的。请直接基于这些资料回答，"
                        + "不要说自己无法获取最新信息或没有联网能力。\n\n"
                        + "\n\n---\n\n".join(sources)
                    )
                else:
                    system = LEARN_PROMPT
            else:
                system = CHAT_PROMPT

            # 3. 构建 LLM 消息列表
            llm_messages = [{"role": "system", "content": system}]
            llm_messages.extend(history)
            llm_messages.append({"role": "user", "content": request.message})

            # 4. 推送 session_id（让前端立刻拿到）
            yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"

            # 5. 流式调用 LLM
            client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
            stream = client.chat.completions.create(
                model=settings.llm_model,
                messages=llm_messages,
                stream=True,
            )
            full_reply = ""
            for chunk in stream:
                token = chunk.choices[0].delta.content or ""
                if token:
                    full_reply += token
                    yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"

            # 6. 存入 checkpointer
            new_messages = history + [
                {"role": "user",      "content": request.message},
                {"role": "assistant", "content": full_reply},
            ]
            if existing:
                new_ckpt = copy.deepcopy(existing)
            else:
                new_ckpt = {
                    "v": 4, "ts": "", "id": "",
                    "channel_values": {
                        "session_id":   session_id,
                        "user_message": request.message,
                        "messages":     [],
                        "intent":       intent,
                        "context":      tmp_state.get("context", []),
                        "web_results":  tmp_state.get("web_results", []),
                        "reply":        full_reply,
                    },
                    "channel_versions": {},
                    "versions_seen":    {},
                    "updated_channels": ["messages", "reply"],
                }
            new_ckpt["id"] = str(uuid.uuid4())
            new_ckpt["ts"] = datetime.now(timezone.utc).isoformat()
            new_ckpt["channel_values"]["messages"]     = new_messages
            new_ckpt["channel_values"]["reply"]        = full_reply
            new_ckpt["channel_values"]["user_message"] = request.message
            new_ckpt["channel_values"]["intent"]       = intent
            saver.put(cfg, new_ckpt, {"source": "loop", "step": 1, "parents": {}}, {})

            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            conn.close()

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or str(uuid.uuid4())
    initial_state = {
        "session_id":   session_id,
        "user_message": request.message,
        "messages":     [],
        "intent":       "",
        "context":      [],
        "web_results":  [],
        "reply":        "",
    }
    config = {"configurable": {"thread_id": session_id}}
    final_state = agent_graph.invoke(initial_state, config=config)
    return ChatResponse(reply=final_state["reply"], session_id=session_id)


@router.get("/sessions")
def list_sessions():
    conn  = sqlite3.connect(DB_PATH, check_same_thread=False)
    saver = SqliteSaver(conn)
    rows  = conn.execute(
        "SELECT DISTINCT thread_id FROM checkpoints ORDER BY rowid DESC"
    ).fetchall()
    names = get_session_names()   # {session_id: {name, pinned}}

    result = []
    for (thread_id,) in rows:
        if thread_id == "test-phase11":
            continue
        config   = {"configurable": {"thread_id": thread_id}}
        state    = saver.get(config)
        if not state:
            continue
        messages = state.get("channel_values", {}).get("messages", [])
        default  = next((m["content"][:30] for m in messages if m["role"] == "user"), "新对话")
        meta     = names.get(thread_id, {})
        result.append({
            "session_id": thread_id,
            "preview":    meta.get("name") or default,
            "pinned":     meta.get("pinned", False),
        })

    # 置顶的排前面
    result.sort(key=lambda x: (not x["pinned"],))
    return result


@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    conn  = sqlite3.connect(DB_PATH, check_same_thread=False)
    saver = SqliteSaver(conn)
    state = saver.get({"configurable": {"thread_id": session_id}})
    if not state:
        return {"messages": []}
    return {"messages": state.get("channel_values", {}).get("messages", [])}


@router.patch("/sessions/{session_id}/rename")
def rename_session(session_id: str, body: RenameRequest):
    set_session_name(session_id, body.name)
    return {"ok": True}


@router.patch("/sessions/{session_id}/pin")
def pin_session_api(session_id: str, pinned: bool = True):
    pin_session(session_id, pinned)
    return {"ok": True}


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("DELETE FROM checkpoints   WHERE thread_id = ?", (session_id,))
    conn.execute("DELETE FROM writes        WHERE thread_id = ?", (session_id,))
    conn.commit()
    delete_session_name(session_id)
    return {"ok": True}
