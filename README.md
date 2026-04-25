# LearnPilot - AI 驱动的个人学习私教

LearnPilot 是一个基于 LangGraph 的 AI 学习系统。输入一个学习目标（或上传一本书），系统自动生成学习计划、拆解章节、生成课件、出作业、批改评分，完整引领一个人从零学会一门知识。

## 核心功能

**学习计划生成** — 输入"零基础，2个月学 Python"，AI 自动生成分阶段学习大纲

**书籍驱动学习** — 上传 txt/md/epub 格式的书籍，系统提取目录结构，生成与书籍章节对齐的学习计划和课件

**章节拆解** — 每个阶段自动拆解为 5-10 个具体课时，含学习目标、知识点、预计时长

**课件生成** — 针对每个课时生成教学内容：概念讲解 + 示例代码 + 生活类比 + 要点总结

**作业系统** — 选择题 + 编程题 + 开放题，AI 自动评判并分析薄弱知识点

**学习报告** — 汇总所有课时成绩，生成综合分析报告（支持缓存，有新进度时提示更新）

**AI 对话** — 随时提问，支持 RAG 知识库检索 + 网络搜索，多轮对话记忆

## 快速开始

### 1. 安装依赖

```bash
pip install -e .
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入 LLM API Key：

```
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3
LLM_MODEL=deepseek-v3.2
```

支持任何 OpenAI 兼容接口（火山引擎、DeepSeek、智谱、Moonshot 等）。

### 3. 启动

```bash
python main.py
```

打开 `http://localhost:8000` 即可使用。

### Docker 部署

```bash
docker compose up -d
```

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI + SSE 流式输出 |
| AI 编排 | LangGraph（7 条独立工作流） |
| LLM | OpenAI 兼容接口 |
| 向量数据库 | ChromaDB |
| 网络搜索 | Tavily |
| 数据持久化 | SQLite |
| 前端 | 单页应用（内嵌于 FastAPI） |

## 项目结构

```
LearnPilot/
├── main.py                      # 应用入口
├── src/
│   ├── config.py                # 全局配置
│   ├── storage_plans.py         # SQLite 持久化
│   │
│   ├── agent/                   # LangGraph 工作流
│   │   ├── graph.py             # 聊天 Agent（意图识别→RAG→LLM）
│   │   ├── plan_graph.py        # 学习计划生成
│   │   ├── syllabus_graph.py    # 章节拆解
│   │   ├── lesson_graph.py      # 课件生成
│   │   ├── homework_graph.py    # 作业生成与评判
│   │   └── report_graph.py      # 学习报告生成
│   │
│   ├── api/                     # FastAPI 路由
│   │   ├── ui.py                # 前端页面
│   │   ├── chat.py              # 聊天接口
│   │   ├── plan.py              # 学习计划接口
│   │   ├── syllabus.py          # 章节拆解接口
│   │   ├── lesson.py            # 课件接口
│   │   ├── homework.py          # 作业接口
│   │   └── book.py              # 书籍上传接口
│   │
│   ├── schemas/                 # Pydantic 数据模型
│   ├── rag/                     # RAG 向量知识库 + 文件解析器
│   └── tools/                   # Tavily 网络搜索
│
├── .env.example                 # 环境变量模板
├── Dockerfile
└── docker-compose.yml
```

## 工作流

系统包含 7 条 LangGraph 工作流：

```
1. 聊天      START → 意图识别 → [学习]RAG+搜索→LLM / [闲聊]LLM → END
2. 计划生成   START → 需求解析 → 生成计划 → END
3. 章节拆解   START → 逐阶段展开课时 → 校验编号连续性 → END
4. 课件生成   START → RAG检索参考资料 → 生成教学内容 → END
5. 作业生成   START → 加载课件 → 生成题目 → END
6. 作业评判   START → 逐题批改 → 汇总分数+薄弱点 → END
7. 学习报告   START → 聚合成绩 → 生成综合分析 → END
```

## 书籍模式

上传书籍后，创建学习计划时选择"参考书籍"：

- 学习计划的阶段划分对应书籍章节分组
- 课时拆解对应书中具体小节
- 课件生成优先从书籍内容中检索，严格基于书籍知识体系
- 书籍内容同时存入向量库，对话时也可检索

支持格式：`.txt` `.md` `.epub`

## 环境变量

| 变量 | 说明 | 必填 |
|------|------|------|
| `LLM_API_KEY` | LLM API 密钥 | 是 |
| `LLM_BASE_URL` | LLM API 地址 | 是 |
| `LLM_MODEL` | 模型名称 | 是 |
| `TAVILY_API_KEY` | Tavily 搜索密钥（不填则跳过网络搜索） | 否 |

## License

MIT
