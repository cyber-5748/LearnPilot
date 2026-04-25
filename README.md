# LearnPilot - AI 驱动的个人学习私教

LearnPilot 是一个基于 LangChain / LangGraph 的 AI 学习系统，能够为任何零基础用户生成个性化学习大纲，拆解为可执行的章节任务，自动生成课件与示例代码，并通过作业系统验证学习效果，实现 **"从零到一完整引领一个人学会一门知识"** 的闭环。

---

## 核心功能

### 1. 智能学习大纲生成

用户输入学习目标（如"学会 Python"），系统自动生成完整的分阶段学习大纲：

- 需求解析：从自然语言中提取学习目标、当前水平、时间预算、学习目的
- 大纲生成：分 3-5 个递进阶段，每阶段包含目标、知识点、里程碑
- 个性化调整：根据用户基础和用途定制内容深度与侧重点

### 2. 章节任务拆解

将大纲中的每个阶段进一步拆解为具体的学习任务：

- 每个阶段拆解为 5-10 个具体课时（Lesson）
- 每课时包含：学习目标、知识点列表、预计时长
- 课时之间有明确的前置依赖关系
- 支持用户标记完成进度，系统追踪学习状态

### 3. 课件与示例代码生成

针对每个课时，AI 自动生成教学内容：

- 概念讲解：用通俗易懂的语言解释核心概念
- 示例代码：针对编程类课题，生成可运行的示例代码并逐行注释
- 类比教学：用生活中的例子解释抽象概念
- 知识关联：指出本课内容与前后课时的关系

### 4. 作业与学习效果验证

每课时结束后，系统生成作业来验证学习效果：

- 选择题：检验概念理解
- 编程题：检验动手能力（附带测试用例自动评判）
- 开放题：检验综合运用能力（AI 评阅并给反馈）
- 成绩追踪：记录每次作业分数，生成学习报告
- 薄弱点分析：根据错题自动识别需要加强的知识点

### 5. 书籍上传与解析

支持用户上传自己的学习资料，系统自动解析并据此生成学习计划：

- 文件上传：当前支持纯文本格式（.txt / .md），后续接入 OCR 模型支持 PDF、图片等
- 智能分块：按章节/段落自动切分，保留结构层级关系
- 内容归纳：对每个章节提取核心知识点、关键概念、难度评级
- 目录提取：从书籍内容中识别出章节大纲结构
- 知识入库：切片后存入 ChromaDB，后续聊天和课件生成都能检索到书中内容
- 基于书籍的学习计划：以书籍目录为骨架，自动生成与书籍章节对齐的学习计划

两种学习模式：

| 模式 | 触发方式 | 大纲来源 |
|------|---------|---------|
| 自由模式 | 用户输入"我想学 Python" | AI 自主生成大纲 |
| 书籍模式 | 用户上传《Python 编程》 | 从书籍目录提取大纲 |

### 6. 智能聊天辅导

在学习过程中随时与 AI 对话：

- 针对当前课时内容答疑
- 结合本地知识库（RAG）和网络搜索提供准确回答
- 多轮对话记忆，理解上下文
- SSE 流式输出，实时显示回复

---

## 技术架构

### 技术栈

| 层次 | 技术 | 用途 |
|------|------|------|
| Web 框架 | FastAPI | HTTP API + SSE 流式输出 |
| AI 编排 | LangGraph | 多步骤 Agent 工作流 |
| LLM 调用 | LangChain / OpenAI SDK | 统一的 LLM 接口 |
| 向量数据库 | ChromaDB | RAG 本地知识库 |
| 网络搜索 | Tavily | 实时信息检索 |
| 数据库 | SQLite | 学习进度、计划、作业数据持久化 |
| 文件解析 | 纯文本解析（后续接入 OCR） | 书籍上传与内容提取 |
| 前端 | 原生 HTML/CSS/JS | 单页应用，内嵌于 FastAPI |

### 项目结构

```
LearnPilot/
├── main.py                          # 应用入口
├── pyproject.toml                   # 项目依赖
├── .env.example                     # 环境变量模板
│
├── src/
│   ├── config.py                    # 全局配置（从 .env 加载）
│   │
│   ├── agent/                       # LangGraph Agent 工作流
│   │   ├── state.py                 # Agent 状态定义
│   │   ├── graph.py                 # 聊天 Agent 图（意图识别→RAG→搜索→LLM）
│   │   ├── nodes.py                 # 聊天 Agent 节点
│   │   ├── plan_graph.py            # 大纲生成 Agent 图
│   │   ├── book_graph.py            # [待开发] 书籍解析 Agent 图
│   │   ├── syllabus_graph.py        # [待开发] 章节拆解 Agent 图
│   │   ├── lesson_graph.py          # [待开发] 课件生成 Agent 图
│   │   ├── homework_graph.py        # [待开发] 作业生成与评判 Agent 图
│   │   └── report_graph.py          # [待开发] 学习报告生成 Agent 图
│   │
│   ├── api/                         # FastAPI 路由
│   │   ├── ui.py                    # 前端 HTML 页面
│   │   ├── chat.py                  # 聊天接口（流式 + 非流式）
│   │   ├── plan.py                  # 学习大纲接口
│   │   ├── book.py                  # [待开发] 书籍上传与解析接口
│   │   ├── syllabus.py              # [待开发] 章节任务接口
│   │   ├── lesson.py                # [待开发] 课件接口
│   │   ├── homework.py              # [待开发] 作业接口
│   │   └── report.py               # [待开发] 学习报告接口
│   │
│   ├── schemas/                     # Pydantic 数据模型
│   │   ├── plan.py                  # 学习大纲模型
│   │   ├── book.py                  # [待开发] 书籍/章节模型
│   │   ├── syllabus.py              # [待开发] 章节/课时模型
│   │   ├── lesson.py                # [待开发] 课件内容模型
│   │   ├── homework.py              # [待开发] 作业/评判模型
│   │   └── report.py               # [待开发] 学习报告模型
│   │
│   ├── rag/                         # RAG 知识检索
│   │   └── knowledge_base.py        # ChromaDB 向量知识库
│   │
│   ├── parsers/                     # 文件解析器
│   │   ├── base.py                  # [待开发] 解析器基类
│   │   ├── text_parser.py           # [待开发] 纯文本解析（txt/md）
│   │   └── ocr_parser.py            # [待期] OCR 解析（PDF/图片）
│   │
│   ├── tools/                       # Agent 工具
│   │   ├── search.py                # Tavily 网络搜索
│   │   └── code_runner.py           # [待开发] 代码执行沙箱
│   │
│   ├── storage_plans.py             # 计划 + 会话持久化
│   │
│   └── models/                      # SQLAlchemy ORM 模型（备用）
│       └── ...
│
├── knowledge/                       # RAG 知识库源文件（.md）
│   ├── python_basics.md
│   ├── fastapi_guide.md
│   └── langgraph_guide.md
│
├── scripts/
│   └── build_knowledge.py           # 知识库构建脚本
│
└── learn/                           # 教学用示例脚本
    ├── 01_hello_llm.py
    ├── 02_conversation.py
    ├── 03_streaming.py
    └── 04_tools.py
```

### LangGraph 工作流设计

系统包含 7 条独立的 LangGraph 工作流，各司其职：

#### 工作流 1：聊天 Agent（已实现）

```
START → classify_intent → [学习] → retrieve_context → web_search → call_llm_learn → END
                        → [闲聊] → call_llm_chat → END
```

- 意图识别区分"学习提问"和"日常闲聊"
- 学习路径：先从本地知识库检索，再搜网络，最后融合回答
- 支持 Checkpointer 持久化多轮对话记忆

#### 工作流 2：大纲生成 Agent（已实现）

```
START → parse_requirements → generate_plan → END
```

- 从自然语言中提取结构化学习需求
- 根据需求生成 3-5 个阶段的学习大纲

#### 工作流 3：书籍解析 Agent（待开发）

```
START → read_file → split_chunks → extract_toc → summarize_chapters → index_to_rag → END
```

| 节点 | 职责 |
|------|------|
| read_file | 读取上传文件，调用对应解析器（文本/OCR）提取纯文本 |
| split_chunks | 按章节/段落智能分块，保留层级结构（标题→小节→段落） |
| extract_toc | LLM 从内容中识别书籍目录结构，输出结构化章节树 |
| summarize_chapters | 对每个章节提取核心知识点、关键概念、难度评级 |
| index_to_rag | 将所有切片存入 ChromaDB，元数据标记 book_id + chapter_index |

文件解析器设计（可扩展）：

```python
# src/parsers/base.py
class BaseParser:
    """解析器基类，所有格式的解析器都继承它。"""
    def parse(self, file_path: str) -> str:
        """输入文件路径，输出纯文本。"""
        raise NotImplementedError

# src/parsers/text_parser.py — 当前实现
class TextParser(BaseParser):
    """处理 .txt / .md 文件，直接读取文本内容。"""
    def parse(self, file_path: str) -> str:
        return Path(file_path).read_text(encoding="utf-8")

# src/parsers/ocr_parser.py — 后续接入
class OcrParser(BaseParser):
    """处理 PDF / 图片文件，调用 OCR 模型提取文本。"""
    def parse(self, file_path: str) -> str:
        # 后续接入 OCR 模型（如 PaddleOCR / Tesseract / 云端 API）
        ...
```

#### 工作流 4：章节拆解 Agent（待开发）

```
START → load_plan → expand_phase → generate_lessons → validate_sequence → END
```

| 节点 | 职责 |
|------|------|
| load_plan | 加载已生成的学习大纲 |
| expand_phase | 将每个阶段展开为具体课时列表 |
| generate_lessons | 为每个课时填充学习目标、知识点、预计时长 |
| validate_sequence | 校验课时之间的前置依赖关系是否合理 |

#### 工作流 5：课件生成 Agent（待开发）

```
START → load_lesson → search_references → generate_explanation → generate_code_examples → assemble_courseware → END
```

| 节点 | 职责 |
|------|------|
| load_lesson | 加载课时信息（目标、知识点） |
| search_references | RAG + 网络搜索获取参考资料 |
| generate_explanation | 生成概念讲解（类比 + 通俗语言） |
| generate_code_examples | 生成带注释的示例代码 |
| assemble_courseware | 组装为完整课件 |

#### 工作流 6：作业评判 Agent（待开发）

```
START → load_lesson_context → generate_homework → END  （生成阶段）

START → load_submission → [选择题] → auto_grade → END  （评判阶段）
                        → [编程题] → run_tests → auto_grade → END
                        → [开放题] → ai_review → END
```

| 节点 | 职责 |
|------|------|
| load_lesson_context | 加载课时内容作为出题上下文 |
| generate_homework | 根据知识点生成选择题 + 编程题 + 开放题 |
| auto_grade | 选择题自动判分 |
| run_tests | 编程题运行测试用例判定 |
| ai_review | 开放题由 AI 评阅并给出反馈 |

#### 工作流 7：学习报告 Agent（待开发）

```
START → check_existing_report → [有报告] → return_cached → END
                               → [无报告 / 用户要求更新] → collect_progress → analyze_weak_points → generate_report → save_report → END
```

| 节点 | 职责 |
|------|------|
| check_existing_report | 查询 SQLite 是否已有该计划的学习报告；有则返回缓存报告 + `has_update` 标记（对比报告生成时间与最新提交时间，判断是否有新进度） |
| collect_progress | 汇总所有课时的完成状态、作业分数、尝试次数 |
| analyze_weak_points | 从全部 submissions 中聚合错题，按知识点统计错误率，识别薄弱领域 |
| generate_report | LLM 综合以上数据，生成结构化学习报告（总评、各阶段分析、薄弱点、改进建议） |
| save_report | 将报告存入 SQLite，记录生成时间戳 |

交互流程：

```
用户点击"学习报告"
       ↓
  查询是否存在历史报告？
       ↓
  ┌─ 有历史报告 ──────────────────────────────────┐
  │  展示报告内容                                   │
  │  对比：报告生成时间 vs 最新学习进度时间          │
  │       ↓                                        │
  │  有新进度？ → 显示提示横幅：                     │
  │  "自上次报告后你又完成了 N 个课时，是否更新？"   │
  │       ↓                                        │
  │  [更新报告] 按钮 → 重新生成                     │
  │  [暂不更新] 按钮 → 继续查看当前报告             │
  │                                                │
  │  无新进度？ → 直接展示，不显示更新提示           │
  └────────────────────────────────────────────────┘
  ┌─ 无历史报告 ──────────────────────────────────┐
  │  检查是否有足够的学习数据（至少完成 1 个课时）   │
  │  有 → 自动生成报告                              │
  │  无 → 提示"请先完成至少一个课时的学习"          │
  └────────────────────────────────────────────────┘
```

### 数据模型设计

#### 学习大纲（Plan） - 已实现

```
Plan
├── title: str              # 计划标题
├── summary: str            # 一句话总结
├── level: str              # 起始水平
├── total_weeks: int        # 总周数
├── daily_hours: float      # 每日学习时长
├── total_hours: int        # 总学习时长
├── phases[]                # 学习阶段列表
│   ├── phase: int          # 阶段编号
│   ├── title: str          # 阶段标题
│   ├── weeks: str          # 时间范围
│   ├── goal: str           # 阶段目标
│   ├── topics: list[str]   # 核心知识点
│   ├── daily_plan: str     # 每日安排
│   └── milestone: str      # 里程碑
└── tips: list[str]         # 个性化建议
```

#### 书籍资料（Book） - 待开发

```
Book
├── id: int                 # 书籍 ID
├── filename: str           # 原始文件名
├── title: str              # 书籍标题（LLM 从内容中提取）
├── file_type: str          # txt / md / pdf（后续扩展）
├── total_chunks: int       # 切片总数
├── toc: BookTOC            # 目录结构
│   └── chapters[]
│       ├── index: int      # 章节序号
│       ├── title: str      # 章节标题
│       ├── summary: str    # 章节摘要
│       ├── key_concepts: list[str]  # 核心概念
│       ├── difficulty: str # easy / medium / hard
│       └── chunk_ids: list[str]     # 关联的 ChromaDB 切片 ID
├── plan_id: int | None     # 关联生成的学习计划（生成后回填）
└── created_at: str
```

#### 章节课时（Syllabus） - 待开发

```
Syllabus
├── plan_id: int            # 关联的大纲 ID
├── phase_index: int        # 所属阶段编号
└── lessons[]               # 课时列表
    ├── lesson_id: int      # 课时编号
    ├── title: str          # 课时标题
    ├── objectives: list[str]  # 学习目标
    ├── topics: list[str]   # 知识点
    ├── duration_min: int   # 预计时长（分钟）
    ├── prerequisites: list[int]  # 前置课时 ID
    └── status: str         # not_started / in_progress / completed
```

#### 课件（Lesson Content） - 待开发

```
LessonContent
├── lesson_id: int          # 关联课时 ID
├── explanation: str        # 概念讲解（Markdown）
├── code_examples[]         # 示例代码
│   ├── title: str          # 示例标题
│   ├── language: str       # 编程语言
│   ├── code: str           # 代码
│   └── explanation: str    # 逐行注释
├── analogies: list[str]    # 生活类比
└── key_takeaways: list[str]  # 核心要点
```

#### 作业（Homework） - 待开发

```
Homework
├── lesson_id: int          # 关联课时 ID
├── questions[]             # 题目列表
│   ├── type: str           # choice / coding / open
│   ├── question: str       # 题目描述
│   ├── options: list[str]  # 选择题选项（仅 choice）
│   ├── answer: str         # 标准答案
│   ├── test_cases: list    # 测试用例（仅 coding）
│   └── points: int         # 分值
│
Submission
├── homework_id: int        # 关联作业 ID
├── answers[]               # 用户提交
│   ├── question_index: int
│   ├── user_answer: str
│   ├── is_correct: bool
│   ├── score: int
│   └── feedback: str       # AI 反馈
├── total_score: int        # 总分
└── weak_points: list[str]  # 薄弱知识点
```

#### 学习报告（LearningReport） - 待开发

```
LearningReport
├── id: int                      # 报告 ID
├── plan_id: int                 # 关联的学习计划
├── generated_at: str            # 报告生成时间
├── data_snapshot_at: str        # 报告依据的最新学习数据时间
├── overall_progress: float      # 总体完成率（0.0 ~ 1.0）
├── overall_score: float         # 综合评分
├── summary: str                 # AI 生成的总评（一段话）
├── phase_reports[]              # 各阶段分析
│   ├── phase_index: int
│   ├── title: str
│   ├── completion_rate: float   # 该阶段完成率
│   ├── avg_score: float         # 该阶段平均作业分数
│   ├── strong_topics: list[str] # 掌握较好的知识点
│   └── weak_topics: list[str]   # 薄弱知识点
├── weak_point_analysis[]        # 薄弱点详细分析
│   ├── topic: str               # 知识点名称
│   ├── error_rate: float        # 错误率
│   ├── related_lessons: list[int]  # 涉及的课时
│   └── suggestion: str          # AI 给出的针对性改进建议
├── recommendations: list[str]   # 下一步学习建议
└── is_stale: bool               # 是否有更新的学习数据（运行时计算，不存库）
```

---

## 三层记忆架构

要实现"引领学习"的闭环，系统需要三层记忆协作：

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: SQLite — 结构化学习状态（进度、分数、弱点）       │
│  "用户学到哪了、学得怎么样"                                │
├─────────────────────────────────────────────────────────┤
│  Layer 2: LangGraph Checkpointer — 对话记忆               │
│  "用户刚才问了什么、聊到哪了"                              │
├─────────────────────────────────────────────────────────┤
│  Layer 3: ChromaDB — 课件语义索引                          │
│  "生成的课件内容，供聊天 Agent RAG 检索"                   │
└─────────────────────────────────────────────────────────┘
```

**核心设计决策**：SQLite 是学习进度的唯一真相源（source of truth），Checkpointer 只管对话，ChromaDB 只管检索。三者通过 `plan_id` + `lesson_id` 关联。

### 数据库表设计

```sql
-- 已有
plans              (id, title, user_input, plan_json, ...)

-- 新增：上传的书籍
books              (id, filename, title, file_type,
                    total_chunks,
                    toc_json,        -- 目录结构 JSON（章节标题、摘要、核心概念）
                    plan_id,         -- 关联的学习计划 ID（生成后回填）
                    created_at)

-- 新增：章节拆解结果
syllabi            (id, plan_id, phase_index, lessons_json, created_at)

-- 新增：每个课时的学习状态
lesson_progress    (id, plan_id, lesson_index,
                    status,          -- not_started / in_progress / completed
                    started_at, completed_at,
                    homework_score,  -- 最近一次作业分数
                    attempts)        -- 作业尝试次数

-- 新增：生成的课件缓存（避免重复调用 LLM）
lesson_contents    (id, plan_id, lesson_index,
                    content_json,    -- 完整课件 JSON
                    created_at)

-- 新增：作业题目缓存
homeworks          (id, plan_id, lesson_index,
                    questions_json,  -- 题目列表 JSON
                    created_at)

-- 新增：用户提交记录
submissions        (id, homework_id,
                    answers_json,    -- 用户答案
                    score, max_score,
                    feedback_json,   -- AI 评语 + 薄弱点
                    submitted_at)

-- 新增：学习报告（每个计划可有多份历史报告）
learning_reports   (id, plan_id,
                    report_json,         -- 完整报告 JSON（LearningReport）
                    data_snapshot_at,    -- 报告依据的最新学习数据时间
                    generated_at)
```

### Agent 工作流中的记忆注入

核心问题：**每个 Agent 怎么知道用户的学习状态？**

答案：在 Agent 执行前，API 层从 SQLite 加载相关上下文，注入到 LangGraph State 中。

```python
# 课件生成 Agent 的 State — 注入学习上下文
class LessonState(TypedDict):
    plan_id:      int           # 哪个计划
    lesson_index: int           # 哪个课时
    plan_context: dict          # ← 从 SQLite 加载：大纲信息
    syllabus:     dict          # ← 从 SQLite 加载：章节结构
    prev_lessons: list[str]     # ← 从 SQLite 加载：前置课时的要点摘要
    weak_points:  list[str]     # ← 从 SQLite 加载：用户薄弱点
    content:      dict          # → 输出：生成的课件

# 聊天 Agent 的 State — 升级后增加学习上下文
class AgentState(TypedDict):
    session_id:      str
    user_message:    str
    messages:        Annotated[list[dict], operator.add]
    intent:          str
    context:         list[str]       # RAG 检索结果
    web_results:     list[str]       # 网络搜索结果
    # ↓ 新增：学习上下文（从 SQLite 注入）
    current_lesson:  dict | None     # 当前正在学的课时内容
    learning_stage:  str             # "阶段1-课时3" 之类的定位
    weak_points:     list[str]       # 用户薄弱点，回答时针对性强化
    reply:           str
```

**注入时机**：API 层在调用 Agent 之前，从 SQLite 查询并组装上下文：

```python
# api/lesson.py 伪代码
@router.post("/lesson/{plan_id}/{lesson_index}/generate")
def generate_lesson(plan_id: int, lesson_index: int):
    # 1. 先查缓存
    cached = get_lesson_content(plan_id, lesson_index)
    if cached:
        return cached

    # 2. 从 SQLite 加载上下文
    plan = get_plan(plan_id)
    syllabus = get_syllabus(plan_id)
    weak = get_weak_points(plan_id)

    # 3. 注入 State，调用 LangGraph Agent
    result = lesson_graph.invoke({
        "plan_id": plan_id,
        "lesson_index": lesson_index,
        "plan_context": plan,
        "syllabus": syllabus,
        "weak_points": weak,
    })

    # 4. 缓存结果到 SQLite + 索引到 ChromaDB（让聊天 Agent 能检索到）
    save_lesson_content(plan_id, lesson_index, result["content"])
    index_to_chromadb(result["content"])

    return result["content"]
```

### 记忆流转全景

```
上传书籍 → [SQLite: books] + [ChromaDB: 书籍切片（带 book_id + chapter 元数据）]
   ↓                              ↓
提取目录 → 自动生成学习计划    聊天/课件生成 ← RAG 检索书籍原文
   ↓
生成大纲 → [SQLite: plans]
              ↓
拆解章节 → [SQLite: syllabi]
              ↓
生成课件 → [SQLite: lesson_contents] + [ChromaDB: 课件索引]
              ↓                              ↓
用户学习 → [SQLite: lesson_progress]    聊天答疑 ← RAG 检索课件
              ↓
生成作业 → [SQLite: homeworks]
              ↓
提交评判 → [SQLite: submissions]
              ↓
薄弱分析 → [SQLite: submissions.feedback_json]
              ↓
下一课件生成时 ← 读取薄弱点，针对性强化讲解
              ↓
查看报告 → [SQLite: learning_reports]
              ↓
           有缓存？→ 展示 + 检查 data_snapshot_at < 最新 submitted_at？
              ↓                    ↓
           有新进度 → 用户点"更新报告" → 重新生成 → 覆盖写入
           无新进度 → 直接展示
```

**核心循环**：作业暴露薄弱点 → 薄弱点影响后续课件生成 + 聊天回答 → 形成自适应学习。
**报告机制**：报告按需生成 + 缓存，仅在用户主动请求更新时重新生成，避免浪费 LLM 调用。

---

## 用户交互设计

用户始终在**一个界面**里操作，侧边栏是导航，主区域根据状态自动切换：

```
┌──────────┬──────────────────────────────────────────┐
│ 侧边栏    │  主内容区                                 │
│          │                                          │
│ ▸ 大纲    │  ┌─ 状态机（4种视图自动切换）──────────┐   │
│   阶段1   │  │                                    │   │
│    课时1 ✓│  │  📋 课时列表视图（选择要学的课时）   │   │
│    课时2 ◉│  │       ↓ 点击某课时                  │   │
│    课时3  │  │  📖 课件阅读视图（学习内容）         │   │
│    课时4  │  │       ↓ 点击"开始测验"              │   │
│   阶段2   │  │  📝 作业视图（答题 + 即时反馈）     │   │
│    ...    │  │       ↓ 提交后                      │   │
│          │  │  📊 结果视图（分数 + 薄弱点 + 建议） │   │
│ ▸ 聊天    │  │                                    │   │
│          │  └────────────────────────────────────┘   │
│ ▸ 报告    │                                          │
│          │  💬 聊天面板（随时可展开，带当前课时上下文）│
└──────────┴──────────────────────────────────────────┘

✓ = 已完成   ◉ = 进行中   空 = 未开始
```

交互细节：

1. **用户生成大纲后** → 自动触发章节拆解 → 侧边栏出现课时树
2. **点击某课时** → 检查 `lesson_contents` 缓存 → 没有则调用课件生成 Agent → 显示课件
3. **课件底部有"开始测验"按钮** → 检查 `homeworks` 缓存 → 没有则生成 → 进入答题
4. **提交作业** → AI 评判 → 显示分数和反馈 → >=80分自动标记完成，<80分建议复习
5. **随时打开聊天** → 聊天 Agent 自动注入当前课时的课件内容作为上下文
6. **点击侧边栏"报告"** → 查询 `learning_reports` 缓存：
   - 有缓存且无新进度 → 直接展示报告
   - 有缓存但有新进度 → 展示报告 + 顶部横幅："自上次报告后你又完成了 N 个课时" + `[更新报告]` / `[暂不更新]` 按钮
   - 无缓存且已有学习数据 → 自动生成首份报告
   - 无缓存且无学习数据 → 提示"请先完成至少一个课时"

---

## 用户学习流程

```
        ┌── 自由模式：用户输入学习目标 ──┐
        │                                │
        │   [大纲生成 Agent]              │
        │                                │
        ├── 书籍模式：用户上传书籍 ──────┤
        │                                │
        │   [书籍解析 Agent]              │
        │    ↓ 提取目录 → 生成大纲       │
        │                                │
        └────────┬───────────────────────┘
                 ↓
  生成分阶段学习计划（两种模式输出相同结构）
                 ↓
  [章节拆解 Agent]  →  拆解为具体课时任务
       ↓
  ┌──────────────────── 学习循环 ────────────────────┐
  │                                                   │
  │  [课件生成 Agent]  →  生成本课教学内容             │
  │       ↓                                           │
  │  用户阅读课件、运行示例代码                        │
  │       ↓                                           │
  │  [聊天 Agent]  ←→  随时提问答疑                   │
  │       ↓                                           │
  │  [作业评判 Agent]  →  生成作业 → 用户提交 → 评分  │
  │       ↓                                           │
  │  通过 → 进入下一课时                               │
  │  未通过 → 薄弱点分析 → 针对性复习                  │
  │                                                   │
  │  [学习报告 Agent]  ←  用户随时可查看               │
  │       ↓                                           │
  │  有历史报告？                                      │
  │    有 → 展示报告 → 有新进度？→ 提示用户更新        │
  │    无 → 自动生成首份报告                           │
  │                                                   │
  └───────────────────────────────────────────────────┘
       ↓
  全部课时完成 → 生成最终学习报告
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -e .
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

### 3. 构建知识库

```bash
python scripts/build_knowledge.py
```

### 4. 启动服务

```bash
python main.py
```

访问 `http://localhost:8000` 进入学习界面。

---

## 当前进度

- [x] LLM 基础调用（OpenAI 兼容接口）
- [x] 多轮对话 + 会话持久化（LangGraph Checkpointer）
- [x] 意图识别（学习 / 闲聊分流）
- [x] RAG 本地知识库（ChromaDB）
- [x] 网络搜索增强（Tavily）
- [x] SSE 流式聊天输出
- [x] 学习大纲生成（需求解析 + 计划生成两步 Agent）
- [x] 前端界面（聊天 + 计划表单 + 历史管理）
- [ ] 书籍上传与解析（纯文本 txt/md）
- [ ] 书籍目录提取 + 基于书籍的学习计划生成
- [ ] 章节任务拆解
- [ ] 课件与示例代码生成
- [ ] 作业系统（出题 + 自动评判）
- [ ] 学习进度追踪
- [ ] 学习报告（缓存优先 + 用户主动更新）
- [ ] 薄弱点分析
- [ ] OCR 解析器（PDF / 图片格式书籍）
