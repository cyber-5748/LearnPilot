# 阶段 1：直接调用 LLM 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 `POST /chat` 接口，直接调用 DeepSeek/OpenAI，支持普通回复和流式回复，并将对话历史保存到数据库。

**Architecture:** 新增 `src/llm/client.py` 封装 OpenAI SDK 客户端（DeepSeek 与 OpenAI 共用同一个客户端，只切换 `base_url`）。新增 `Message` ORM 模型存储对话历史。新增 `src/api/chat.py` 提供两个端点：`POST /chat`（完整回复）和 `POST /chat/stream`（流式 SSE 回复）。

**Tech Stack:** openai SDK 2.x（AsyncOpenAI）、FastAPI StreamingResponse、SQLAlchemy async、pytest + unittest.mock

---

## 学习重点（阅读代码时关注这些问题）

- LLM 的输入是一个 **消息列表**，每条消息有 `role`（system/user/assistant）和 `content`
- `system` 消息是给 AI 的"人设说明"，在列表最前面，用户看不到
- `user` 消息是用户说的话，`assistant` 消息是 AI 回复的话
- 流式输出：AI 不是一次性返回整段文字，而是一个字一个字地"打印出来"，就像打字机
- DeepSeek 兼容 OpenAI 接口，只需换一个 `base_url` 和 `api_key`

---

## 文件结构

```
src/
  llm/
    __init__.py          CREATE — 包标记
    client.py            CREATE — LLM 客户端工厂函数（返回 AsyncOpenAI 实例）
  schemas/
    __init__.py          CREATE — 包标记
    chat.py              CREATE — ChatRequest、ChatResponse Pydantic 模型
  models/
    message.py           CREATE — Message ORM 模型（对话历史表）
    __init__.py          MODIFY — 新增 Message 导入
  api/
    chat.py              CREATE — POST /chat 和 POST /chat/stream 路由
    health.py            不改动
main.py                  MODIFY — 注册 chat router
tests/
  test_chat_api.py       CREATE — /chat 接口集成测试（mock LLM）
  test_message_model.py  CREATE — Message 模型 CRUD 测试
```

---

## 任务 1：Message 数据库模型

**目的：** 每次对话的消息（用户说的 + AI 回的）都存入数据库，方便下次加载历史。

**Files:**
- Create: `src/models/message.py`
- Modify: `src/models/__init__.py`
- Create: `tests/test_message_model.py`

- [ ] **步骤 1：写失败测试**

创建 `tests/test_message_model.py`：

```python
# tests/test_message_model.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.learning_session import LearningSession
from src.models.message import Message
from src.models.user_profile import UserProfile


@pytest.mark.asyncio
async def test_create_message(test_db: AsyncSession):
    """验证 Message 可以正常写入数据库，role 和 content 字段正确保存。"""
    # 先创建 UserProfile 和 LearningSession，Message 外键依赖它们
    profile = UserProfile(name="测试用户", goal="学习 LLM")
    test_db.add(profile)
    await test_db.commit()
    await test_db.refresh(profile)

    session = LearningSession(user_profile_id=profile.id, intent="chat")
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)

    # 保存一条用户消息
    msg = Message(
        session_id=session.id,
        role="user",
        content="你好，我想学 Python",
    )
    test_db.add(msg)
    await test_db.commit()
    await test_db.refresh(msg)

    assert msg.id is not None
    assert msg.role == "user"
    assert msg.content == "你好，我想学 Python"
    assert msg.created_at is not None


@pytest.mark.asyncio
async def test_create_assistant_message(test_db: AsyncSession):
    """验证 assistant 角色的消息也能正常保存。"""
    profile = UserProfile(name="学习者")
    test_db.add(profile)
    await test_db.commit()
    await test_db.refresh(profile)

    session = LearningSession(user_profile_id=profile.id, intent="chat")
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)

    msg = Message(
        session_id=session.id,
        role="assistant",
        content="你好！Python 是一门非常适合初学者的语言。",
    )
    test_db.add(msg)
    await test_db.commit()
    await test_db.refresh(msg)

    assert msg.role == "assistant"
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
conda run -n 13 pytest tests/test_message_model.py -v
```

预期：`ImportError: cannot import name 'Message' from 'src.models.message'`

- [ ] **步骤 3：创建 `src/models/message.py`**

```python
# src/models/message.py
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class Message(Base, TimestampMixin):
    """对话消息记录：保存每轮对话中用户和 AI 的发言。

    知识点：
    - role 字段只有三种值：
      * "system"    — 给 AI 的人设说明（用户看不到）
      * "user"      — 用户说的话
      * "assistant" — AI 回复的话
    - 把历史消息按 created_at 排序后，发给 LLM，它就能"记住"之前说了什么
    """

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("learning_sessions.id"))
    role: Mapped[str] = mapped_column(String(20))   # "user" | "assistant" | "system"
    content: Mapped[str] = mapped_column(Text)
```

- [ ] **步骤 4：更新 `src/models/__init__.py`**

```python
# src/models/__init__.py
from src.models.learning_session import LearningSession
from src.models.message import Message
from src.models.progress import Progress
from src.models.user_profile import UserProfile

__all__ = ["UserProfile", "LearningSession", "Progress", "Message"]
```

- [ ] **步骤 5：运行测试，确认通过**

```bash
conda run -n 13 pytest tests/test_message_model.py -v
```

预期：
```
PASSED tests/test_message_model.py::test_create_message
PASSED tests/test_message_model.py::test_create_assistant_message
```

- [ ] **步骤 6：提交**

```bash
git add src/models/message.py src/models/__init__.py tests/test_message_model.py
git commit -m "feat: 新增 Message 模型，用于存储对话历史"
```

---

## 任务 2：LLM 客户端封装

**目的：** 把"如何创建 OpenAI 客户端"的逻辑集中在一个地方，其他模块直接调用。

**Files:**
- Create: `src/llm/__init__.py`
- Create: `src/llm/client.py`

- [ ] **步骤 1：创建 `src/llm/__init__.py`**（空文件）

- [ ] **步骤 2：创建 `src/llm/client.py`**

```python
# src/llm/client.py
from openai import AsyncOpenAI

from src.config import settings


def get_llm_client() -> AsyncOpenAI:
    """返回配置好的异步 LLM 客户端。

    知识点：
    - DeepSeek 完全兼容 OpenAI 接口，只需换 api_key 和 base_url
    - AsyncOpenAI 是异步版本，适合在 FastAPI（也是异步框架）中使用
    - 如果两个 key 都填了，优先用 DeepSeek（更便宜）
    """
    if settings.deepseek_api_key:
        return AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
    return AsyncOpenAI(api_key=settings.openai_api_key)


def get_model_name() -> str:
    """返回当前配置使用的模型名称。"""
    if settings.deepseek_api_key:
        return settings.deepseek_model
    return settings.openai_model
```

- [ ] **步骤 3：手动验证客户端可以创建（不调用 API）**

```bash
conda run -n 13 python -c "
from src.llm.client import get_llm_client, get_model_name
client = get_llm_client()
print('客户端类型:', type(client).__name__)
print('使用模型:', get_model_name())
"
```

预期输出（取决于你的 `.env` 配置）：
```
客户端类型: AsyncOpenAI
使用模型: deepseek-chat
```

- [ ] **步骤 4：提交**

```bash
git add src/llm/
git commit -m "feat: 新增 LLM 客户端封装，支持 DeepSeek / OpenAI 切换"
```

---

## 任务 3：请求/响应数据结构（Schema）

**目的：** 定义接口的输入格式和输出格式，FastAPI 会自动做校验和文档生成。

**Files:**
- Create: `src/schemas/__init__.py`
- Create: `src/schemas/chat.py`

- [ ] **步骤 1：创建 `src/schemas/__init__.py`**（空文件）

- [ ] **步骤 2：创建 `src/schemas/chat.py`**

```python
# src/schemas/chat.py
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """用户发送给 /chat 接口的请求体。

    知识点：
    - Pydantic 模型会自动校验字段类型，不符合就返回 422 错误
    - session_id 是可选的（None 表示"开启新对话"）
    - int | None 是 Python 3.10+ 的写法，等价于 Optional[int]
    """

    message: str = Field(..., min_length=1, description="用户输入的消息")
    session_id: int | None = Field(None, description="会话 ID，为空则自动创建新会话")


class ChatResponse(BaseModel):
    """/chat 接口返回的响应体。"""

    reply: str = Field(..., description="AI 的回复内容")
    session_id: int = Field(..., description="本次对话所属的会话 ID")
```

- [ ] **步骤 3：提交**

```bash
git add src/schemas/
git commit -m "feat: 新增 ChatRequest / ChatResponse Schema"
```

---

## 任务 4：POST /chat 接口（普通回复）

**目的：** 实现核心聊天接口，LLM 返回完整回复后一次性响应。

**Files:**
- Create: `src/api/chat.py`
- Modify: `main.py`
- Create: `tests/test_chat_api.py`

- [ ] **步骤 1：写失败测试**

创建 `tests/test_chat_api.py`：

```python
# tests/test_chat_api.py
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


def _mock_llm_response(content: str) -> MagicMock:
    """构造一个模拟的 OpenAI 响应对象。

    知识点：MagicMock 可以模拟任意对象的属性和方法，
    这样测试就不需要真正调用 LLM API（省钱、速度快、结果可预期）。
    """
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = content
    return mock_completion


@pytest.mark.asyncio
async def test_chat_returns_reply(async_client: AsyncClient):
    """POST /chat 应返回 200 及 AI 回复内容。"""
    mock_response = _mock_llm_response("你好！我是 LearnPilot，很高兴帮你学习。")

    with patch("src.api.chat.get_llm_client") as mock_factory:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_factory.return_value = mock_client

        response = await async_client.post("/chat", json={"message": "你好"})

    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "你好！我是 LearnPilot，很高兴帮你学习。"
    assert isinstance(data["session_id"], int)


@pytest.mark.asyncio
async def test_chat_creates_new_session_when_no_session_id(async_client: AsyncClient):
    """不传 session_id 时，应自动创建新会话并在响应中返回。"""
    mock_response = _mock_llm_response("新会话已创建。")

    with patch("src.api.chat.get_llm_client") as mock_factory:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_factory.return_value = mock_client

        response = await async_client.post("/chat", json={"message": "开始学习"})

    assert response.status_code == 200
    assert response.json()["session_id"] is not None


@pytest.mark.asyncio
async def test_chat_reuses_existing_session(async_client: AsyncClient):
    """传入已有 session_id 时，应复用该会话（不新建）。"""
    mock_response = _mock_llm_response("继续上次的内容。")

    with patch("src.api.chat.get_llm_client") as mock_factory:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_factory.return_value = mock_client

        # 第一次：创建会话
        r1 = await async_client.post("/chat", json={"message": "第一条消息"})
        session_id = r1.json()["session_id"]

        # 第二次：复用同一会话
        r2 = await async_client.post(
            "/chat", json={"message": "第二条消息", "session_id": session_id}
        )

    assert r2.json()["session_id"] == session_id


@pytest.mark.asyncio
async def test_chat_empty_message_returns_422(async_client: AsyncClient):
    """空消息应被 Pydantic 校验拦截，返回 422。"""
    response = await async_client.post("/chat", json={"message": ""})
    assert response.status_code == 422
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
conda run -n 13 pytest tests/test_chat_api.py -v
```

预期：`ImportError` 或 `404 Not Found`（路由未注册）

- [ ] **步骤 3：创建 `src/api/chat.py`**

```python
# src/api/chat.py
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.llm.client import get_llm_client, get_model_name
from src.models.learning_session import LearningSession
from src.models.message import Message
from src.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()

# system prompt：告诉 AI 它是谁、该怎么回答
# 这条消息放在消息列表最前面，用户看不到，但 AI 每次都会"读到"它
SYSTEM_PROMPT = (
    "你是 LearnPilot，一个专注于帮助用户学习的 AI 私教。"
    "请用简洁、清晰的中文回答问题，并在合适时给出具体的学习建议。"
)


async def _get_or_create_session(session_id: int | None, db: AsyncSession) -> int:
    """获取已有会话 ID；若未提供则新建一个学习会话。"""
    if session_id is not None:
        return session_id
    new_session = LearningSession(user_profile_id=1, intent="chat")
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session.id


async def _load_history(session_id: int, db: AsyncSession) -> list[dict]:
    """从数据库加载该会话的历史消息，格式化为 OpenAI 消息列表。

    知识点：
    把历史消息拼成列表发给 LLM，它就能"记住"之前说了什么。
    例：[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return [{"role": m.role, "content": m.content} for m in messages]


@router.post("/chat", response_model=ChatResponse, summary="普通对话")
async def chat(
    request: ChatRequest, db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """接收用户消息，调用 LLM，返回完整回复，并保存对话记录。

    知识点 — 发给 LLM 的消息列表结构：
    [
      {"role": "system",    "content": "你是 LearnPilot..."},   ← 人设说明
      {"role": "user",      "content": "上次问的问题"},           ← 历史消息
      {"role": "assistant", "content": "上次的回答"},             ← 历史消息
      {"role": "user",      "content": "这次问的问题"},           ← 本次输入
    ]
    """
    session_id = await _get_or_create_session(request.session_id, db)
    history = await _load_history(session_id, db)

    # 拼装完整消息列表
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": request.message})

    # 调用 LLM
    client = get_llm_client()
    completion = await client.chat.completions.create(
        model=get_model_name(),
        messages=messages,
    )
    reply = completion.choices[0].message.content

    # 保存本轮对话到数据库
    db.add(Message(session_id=session_id, role="user", content=request.message))
    db.add(Message(session_id=session_id, role="assistant", content=reply))
    await db.commit()

    return ChatResponse(reply=reply, session_id=session_id)


@router.post("/chat/stream", summary="流式对话（打字机效果）")
async def chat_stream(
    request: ChatRequest, db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    """流式版本：AI 生成一个字就立刻推送给客户端，像打字机一样。

    知识点 — SSE（Server-Sent Events）格式：
    每条数据以 "data: " 开头，以 "\n\n" 结尾。
    客户端收到 "data: [DONE]\n\n" 表示流结束。

    示例输出：
        data: 你\n\n
        data: 好\n\n
        data: ！\n\n
        data: [DONE]\n\n
    """
    session_id = await _get_or_create_session(request.session_id, db)
    history = await _load_history(session_id, db)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": request.message})

    client = get_llm_client()

    async def generate():
        collected = []
        # stream=True 告诉 LLM：不要等全部生成完，有一点就发一点
        stream = await client.chat.completions.create(
            model=get_model_name(),
            messages=messages,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                collected.append(delta)
                # SSE 格式：每个 token 单独推送
                yield f"data: {json.dumps(delta, ensure_ascii=False)}\n\n"

        # 流结束后保存完整对话记录
        full_reply = "".join(collected)
        db.add(Message(session_id=session_id, role="user", content=request.message))
        db.add(Message(session_id=session_id, role="assistant", content=full_reply))
        await db.commit()

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

- [ ] **步骤 4：更新 `main.py`，注册 chat router**

```python
# main.py（完整替换）
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from src.api.chat import router as chat_router
from src.api.health import router as health_router
from src.config import settings
from src.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"正在启动 {settings.app_name} v{settings.app_version} ...")
    await create_tables()
    logger.info("数据库表初始化完成，服务已就绪。")
    yield
    logger.info("服务正在关闭，正在清理资源...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI 私教 · 学习规划 · 任务执行 Agent",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
```

- [ ] **步骤 5：运行测试，确认通过**

```bash
conda run -n 13 pytest tests/test_chat_api.py -v
```

预期：
```
PASSED tests/test_chat_api.py::test_chat_returns_reply
PASSED tests/test_chat_api.py::test_chat_creates_new_session_when_no_session_id
PASSED tests/test_chat_api.py::test_chat_reuses_existing_session
PASSED tests/test_chat_api.py::test_chat_empty_message_returns_422
```

- [ ] **步骤 6：运行全量测试，确认无回归**

```bash
conda run -n 13 pytest -v
```

预期：所有已有测试（10 个）+ 新测试（6 个）= 16 个全部通过

- [ ] **步骤 7：提交**

```bash
git add src/api/chat.py src/schemas/ main.py tests/test_chat_api.py
git commit -m "feat: 实现 POST /chat 接口，支持普通回复和流式回复"
```

---

## 任务 5：真实 API 冒烟测试

**目的：** 用真实 API Key 跑一次，确认整个链路通了。

> 前提：在 `.env` 中填入真实的 `DEEPSEEK_API_KEY` 或 `OPENAI_API_KEY`。

- [ ] **步骤 1：启动服务**

```bash
conda run -n 13 python main.py
```

- [ ] **步骤 2：在另一个终端测试普通回复**

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "用一句话解释什么是 LLM"}' | python -m json.tool
```

预期（内容因模型而异）：
```json
{
    "reply": "LLM（大型语言模型）是一种通过海量文本训练的 AI 模型，能理解和生成自然语言。",
    "session_id": 1
}
```

- [ ] **步骤 3：测试流式回复**

```bash
curl -s -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "用一句话解释什么是 Agent"}' \
  --no-buffer
```

预期：看到文字逐块打印，最后一行是 `data: [DONE]`

- [ ] **步骤 4：测试多轮对话（验证历史记忆）**

```bash
# 第一轮
SESSION_ID=$(curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "我叫小明，我想学 Python"}' | python -c "import sys,json; print(json.load(sys.stdin)['session_id'])")

echo "Session ID: $SESSION_ID"

# 第二轮：问 AI 还记得名字吗
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"我叫什么名字？\", \"session_id\": $SESSION_ID}" | python -m json.tool
```

预期：AI 回复中包含"小明"（说明历史消息加载成功）

- [ ] **步骤 5：关闭服务并提交**

```bash
# Ctrl+C 关闭服务
git add .
git commit -m "chore: 阶段1冒烟测试通过"
```

---

## 自检

### 需求覆盖

| 路线图需求 | 是否覆盖 | 位置 |
|-----------|---------|------|
| POST /chat 调用 LLM | ✅ | `src/api/chat.py::chat()` |
| 流式响应 | ✅ | `src/api/chat.py::chat_stream()` |
| 消息历史保存到数据库 | ✅ | `Message` 模型 + `db.add(Message(...))` |
| DeepSeek / OpenAI 可切换 | ✅ | `src/llm/client.py` |
| 多轮对话历史加载 | ✅ | `_load_history()` |

### 占位符检查

无。

### 类型一致性

- `_get_or_create_session` 返回 `int`，在 `chat()` 和 `chat_stream()` 中均作为 `session_id: int` 传入 `Message(session_id=...)` ✅
- `_load_history` 返回 `list[dict]`，用 `messages.extend(history)` 拼入列表 ✅
- `ChatResponse(reply=reply, session_id=session_id)` 中 `reply: str`、`session_id: int` 均与 Schema 定义一致 ✅
