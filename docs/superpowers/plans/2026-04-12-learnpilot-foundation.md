# LearnPilot — Plan 1: Foundation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up a runnable FastAPI server with SQLAlchemy async models, Pydantic-based config, and Docker — the stable base every future plan builds on.

**Architecture:** A thin FastAPI app wired to a SQLite database via SQLAlchemy 2.0 async. Configuration is loaded from `.env` through `pydantic-settings`. Three core DB tables (`user_profiles`, `learning_sessions`, `progress`) are defined now so later plans can write to them without migrations. Tables are created on startup via `Base.metadata.create_all`.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0 (async/aiosqlite), Pydantic v2, pydantic-settings, Loguru, pytest-asyncio, HTTPX, Docker

---

## File Map

```
LearnPilot/
├── pyproject.toml                        CREATE  — deps, pytest config, build system
├── .env.example                          CREATE  — template for all required env vars
├── .env                                  CREATE  — local secrets (git-ignored)
├── .gitignore                            CREATE  — exclude .env, __pycache__, *.db, chroma_data
├── Dockerfile                            CREATE  — production container
├── docker-compose.yml                    CREATE  — local dev orchestration
├── main.py                               CREATE  — FastAPI app factory + lifespan
├── src/
│   ├── __init__.py                       CREATE  — package marker
│   ├── config.py                         CREATE  — Settings (pydantic-settings), singleton `settings`
│   ├── database.py                       CREATE  — async engine, session factory, create_tables()
│   ├── models/
│   │   ├── __init__.py                   CREATE  — re-exports all models (required for metadata)
│   │   ├── base.py                       CREATE  — DeclarativeBase + TimestampMixin
│   │   ├── user_profile.py               CREATE  — UserProfile table
│   │   ├── learning_session.py           CREATE  — LearningSession table
│   │   └── progress.py                  CREATE  — Progress table
│   └── api/
│       ├── __init__.py                   CREATE  — package marker
│       └── health.py                     CREATE  — GET /health router
└── tests/
    ├── __init__.py                       CREATE  — package marker
    ├── conftest.py                       CREATE  — test DB fixture, async test client
    ├── test_health.py                    CREATE  — health endpoint tests
    └── test_models.py                    CREATE  — ORM CRUD tests
```

---

## Task 1: Project Bootstrap

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `.env`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "learnpilot"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.29.0",
    "sqlalchemy>=2.0.0",
    "aiosqlite>=0.20.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.2.0",
    "python-dotenv>=1.0.0",
    "loguru>=0.7.0",
    "tenacity>=8.2.0",
    "langgraph>=0.1.0",
    "langchain-core>=0.2.0",
    "langchain-openai>=0.1.0",
    "langchain-community>=0.2.0",
    "tavily-python>=0.3.0",
    "chromadb>=0.5.0",
    "openai>=1.30.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",
    "pytest-cov>=5.0.0",
]

[tool.hatch.build.targets.wheel]
packages = ["src"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create `.gitignore`**

```gitignore
.env
__pycache__/
*.pyc
*.db
chroma_data/
.pytest_cache/
.coverage
dist/
*.egg-info/
```

- [ ] **Step 3: Create `.env.example`**

```dotenv
# App
DEBUG=false

# LLM — fill in at least one
OPENAI_API_KEY=sk-...
# DEEPSEEK_API_KEY=sk-...

# Search
TAVILY_API_KEY=tvly-...
```

- [ ] **Step 4: Create `.env` (your real secrets — never commit)**

Copy `.env.example` to `.env` and fill in your real keys. Leave values blank for now if you don't have them; the app will still start.

```bash
cp .env.example .env
```

- [ ] **Step 5: Install dependencies**

```bash
pip install -e ".[dev]"
```

Expected: no errors, packages install successfully.

- [ ] **Step 6: Commit**

```bash
git init
git add pyproject.toml .gitignore .env.example
git commit -m "chore: project bootstrap — pyproject.toml, gitignore"
```

---

## Task 2: Configuration Module

**Files:**
- Create: `src/__init__.py`
- Create: `src/config.py`

- [ ] **Step 1: Write the failing test**

Create `tests/__init__.py` (empty), then `tests/test_config.py`:

```python
# tests/test_config.py
from src.config import settings


def test_settings_has_app_name():
    assert settings.app_name == "LearnPilot"


def test_settings_has_version():
    assert settings.app_version == "0.1.0"


def test_database_url_is_sqlite():
    assert "sqlite" in settings.database_url
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'src'`

- [ ] **Step 3: Create `src/__init__.py`** (empty file)

- [ ] **Step 4: Create `src/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "LearnPilot"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./learnpilot.db"

    # LLM — OpenAI-compatible
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # Search
    tavily_api_key: str = ""

    # Vector store
    chroma_persist_dir: str = "./chroma_data"


settings = Settings()
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_config.py -v
```

Expected:
```
PASSED tests/test_config.py::test_settings_has_app_name
PASSED tests/test_config.py::test_settings_has_version
PASSED tests/test_config.py::test_database_url_is_sqlite
```

- [ ] **Step 6: Commit**

```bash
git add src/__init__.py src/config.py tests/__init__.py tests/test_config.py
git commit -m "feat: add Settings config via pydantic-settings"
```

---

## Task 3: Database Engine

**Files:**
- Create: `src/database.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_database.py`:

```python
# tests/test_database.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_tables_does_not_raise():
    from src.database import create_tables
    # Should complete without error
    await create_tables()


@pytest.mark.asyncio
async def test_get_db_yields_async_session():
    from src.database import get_db
    session_gen = get_db()
    session = await session_gen.__anext__()
    assert isinstance(session, AsyncSession)
    await session_gen.aclose()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_database.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.database'`

- [ ] **Step 3: Create `src/database.py`**

```python
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings

engine = create_async_engine(settings.database_url, echo=settings.debug)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def create_tables() -> None:
    # Import here to register all models with Base.metadata before create_all
    import src.models  # noqa: F401
    from src.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

- [ ] **Step 4: Create `src/models/__init__.py`** (placeholder — will be filled in Task 4)

```python
# populated in Task 4 after models are defined
```

- [ ] **Step 5: Create `src/models/base.py`**

```python
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
```

- [ ] **Step 6: Run test to verify it passes**

```bash
pytest tests/test_database.py -v
```

Expected:
```
PASSED tests/test_database.py::test_create_tables_does_not_raise
PASSED tests/test_database.py::test_get_db_yields_async_session
```

- [ ] **Step 7: Commit**

```bash
git add src/database.py src/models/__init__.py src/models/base.py tests/test_database.py
git commit -m "feat: add async SQLAlchemy engine and session factory"
```

---

## Task 4: Database Models

**Files:**
- Create: `src/models/user_profile.py`
- Create: `src/models/learning_session.py`
- Create: `src/models/progress.py`
- Modify: `src/models/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/conftest.py`:

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.models.base import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db() -> AsyncSession:
    engine = create_async_engine(TEST_DATABASE_URL)
    # Import models so they register with Base.metadata
    import src.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()
```

Create `tests/test_models.py`:

```python
# tests/test_models.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user_profile import UserProfile
from src.models.learning_session import LearningSession
from src.models.progress import Progress


@pytest.mark.asyncio
async def test_create_user_profile(test_db: AsyncSession):
    profile = UserProfile(
        name="Alice",
        goal="Learn AI Agent development",
        current_level="intermediate",
        daily_minutes=90,
    )
    test_db.add(profile)
    await test_db.commit()
    await test_db.refresh(profile)
    assert profile.id is not None
    assert profile.name == "Alice"
    assert profile.created_at is not None


@pytest.mark.asyncio
async def test_create_learning_session(test_db: AsyncSession):
    profile = UserProfile(name="Bob", goal="Learn Python")
    test_db.add(profile)
    await test_db.commit()
    await test_db.refresh(profile)

    session = LearningSession(
        user_profile_id=profile.id,
        intent="create_plan",
        state_json='{"step": 1}',
        status="active",
    )
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)
    assert session.id is not None
    assert session.user_profile_id == profile.id


@pytest.mark.asyncio
async def test_create_progress(test_db: AsyncSession):
    profile = UserProfile(name="Carol", goal="Study Math")
    test_db.add(profile)
    await test_db.commit()
    await test_db.refresh(profile)

    prog = Progress(
        user_profile_id=profile.id,
        topic="Linear Algebra",
        status="in_progress",
        score=75,
        notes="Completed chapter 1",
    )
    test_db.add(prog)
    await test_db.commit()
    await test_db.refresh(prog)
    assert prog.id is not None
    assert prog.score == 75
    assert prog.topic == "Linear Algebra"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_models.py -v
```

Expected: `ImportError` — models not yet defined.

- [ ] **Step 3: Create `src/models/user_profile.py`**

```python
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), default="learner")
    goal: Mapped[str] = mapped_column(Text, default="")
    current_level: Mapped[str] = mapped_column(String(50), default="beginner")
    daily_minutes: Mapped[int] = mapped_column(Integer, default=90)
```

- [ ] **Step 4: Create `src/models/learning_session.py`**

```python
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class LearningSession(Base, TimestampMixin):
    __tablename__ = "learning_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profiles.id"))
    intent: Mapped[str] = mapped_column(String(50), default="unknown")
    state_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(
        String(20), default="active"
    )  # active | completed | error
```

- [ ] **Step 5: Create `src/models/progress.py`**

```python
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class Progress(Base, TimestampMixin):
    __tablename__ = "progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profiles.id"))
    topic: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(
        String(20), default="not_started"
    )  # not_started | in_progress | completed
    score: Mapped[int] = mapped_column(Integer, default=0)  # 0–100
    notes: Mapped[str] = mapped_column(Text, default="")
```

- [ ] **Step 6: Update `src/models/__init__.py`** to import all models (required so `Base.metadata` is fully populated)

```python
from src.models.user_profile import UserProfile
from src.models.learning_session import LearningSession
from src.models.progress import Progress

__all__ = ["UserProfile", "LearningSession", "Progress"]
```

- [ ] **Step 7: Run test to verify it passes**

```bash
pytest tests/test_models.py -v
```

Expected:
```
PASSED tests/test_models.py::test_create_user_profile
PASSED tests/test_models.py::test_create_learning_session
PASSED tests/test_models.py::test_create_progress
```

- [ ] **Step 8: Commit**

```bash
git add src/models/ tests/conftest.py tests/test_models.py
git commit -m "feat: add UserProfile, LearningSession, Progress ORM models"
```

---

## Task 5: FastAPI App + Health Endpoint

**Files:**
- Create: `src/api/__init__.py`
- Create: `src/api/health.py`
- Create: `main.py`
- Create: `tests/test_health.py`

- [ ] **Step 1: Write the failing test**

Add an `async_client` fixture to `tests/conftest.py` (append below the existing `test_db` fixture):

```python
# append to tests/conftest.py
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def async_client(test_db: AsyncSession):
    from main import app
    from src.database import get_db

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
```

Create `tests/test_health.py`:

```python
# tests/test_health.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_body(async_client: AsyncClient):
    response = await async_client.get("/health")
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert data["app_name"] == "LearnPilot"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_health.py -v
```

Expected: `ModuleNotFoundError: No module named 'main'`

- [ ] **Step 3: Create `src/api/__init__.py`** (empty)

- [ ] **Step 4: Create `src/api/health.py`**

```python
from fastapi import APIRouter
from pydantic import BaseModel

from src.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    app_name: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        app_name=settings.app_name,
    )
```

- [ ] **Step 5: Create `main.py`**

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from src.config import settings
from src.database import create_tables
from src.api.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    await create_tables()
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(health_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
```

- [ ] **Step 6: Run test to verify it passes**

```bash
pytest tests/test_health.py -v
```

Expected:
```
PASSED tests/test_health.py::test_health_returns_200
PASSED tests/test_health.py::test_health_response_body
```

- [ ] **Step 7: Run full test suite**

```bash
pytest -v
```

Expected: all tests in `test_config.py`, `test_database.py`, `test_models.py`, `test_health.py` pass.

- [ ] **Step 8: Commit**

```bash
git add src/api/ main.py tests/conftest.py tests/test_health.py
git commit -m "feat: add FastAPI app with /health endpoint"
```

---

## Task 6: Smoke Test — Local Run

**Files:** none (verification only)

- [ ] **Step 1: Start the server**

```bash
python main.py
```

Expected output (Loguru):
```
INFO | Starting LearnPilot v0.1.0
INFO | Application startup complete.
```

- [ ] **Step 2: Hit the health endpoint in a second terminal**

```bash
curl http://localhost:8000/health
```

Expected:
```json
{"status":"ok","version":"0.1.0","app_name":"LearnPilot"}
```

- [ ] **Step 3: Stop the server** (`Ctrl+C`) and verify shutdown log appears:

```
INFO | Shutting down
```

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "chore: verify local smoke test passes"
```

---

## Task 7: Docker

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`

- [ ] **Step 1: Create `Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .

EXPOSE 8000
CMD ["python", "main.py"]
```

- [ ] **Step 2: Create `docker-compose.yml`**

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./learnpilot.db:/app/learnpilot.db
      - ./chroma_data:/app/chroma_data
    env_file:
      - .env
    restart: unless-stopped
```

- [ ] **Step 3: Build the image**

```bash
docker build -t learnpilot:dev .
```

Expected: `Successfully built ...` (no errors)

- [ ] **Step 4: Run tests inside the container**

```bash
docker run --rm learnpilot:dev pytest -v
```

Expected: all tests pass inside the container.

- [ ] **Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml
git commit -m "chore: add Dockerfile and docker-compose for local dev"
```

---

## Self-Review

### Spec Coverage

| Requirement | Covered? | Where |
|-------------|----------|-------|
| Python 3.11 | Yes | `pyproject.toml` |
| FastAPI | Yes | `main.py`, `src/api/health.py` |
| SQLite storage | Yes | `src/database.py` + models |
| Pydantic v2 | Yes | `src/config.py`, health response |
| Loguru | Yes | `main.py` lifespan logs |
| Docker | Yes | `Dockerfile`, `docker-compose.yml` |
| All env vars templated | Yes | `.env.example` |
| DB schema for sessions/progress | Yes | all three model files |

### Placeholder Scan

None found — all steps contain complete code.

### Type Consistency

- `UserProfile` used as foreign key target in `LearningSession` and `Progress` via `user_profiles.id` — consistent with `UserProfile.__tablename__ = "user_profiles"`.
- `get_db` defined in `src/database.py`, referenced by name in `conftest.py` via `app.dependency_overrides[get_db]` — consistent.
- `settings.app_version` used in health response and lifespan log — both pull from same `Settings` singleton.

---

## Roadmap (Plans 2–6)

| Plan | Subsystem | Deliverable |
|------|-----------|-------------|
| **Plan 2** | LangGraph Agent Core | Intent classifier routes to stub handlers; state machine runs end-to-end |
| **Plan 3** | Learning Plan Generator | User submits goal → gets structured day-by-day plan stored in DB |
| **Plan 4** | Knowledge Retrieval | Agent searches Tavily + Chroma, returns cited explanation |
| **Plan 5** | Quiz Engine | Full quiz session: generate → user answers → grade → weak points recorded |
| **Plan 6** | Memory & Reflection | Cross-session continuity, reflection nodes, progress summary endpoint |
