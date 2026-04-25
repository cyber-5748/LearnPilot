"""
课件生成的 LangGraph 工作流。

为单个课时生成完整教学内容：概念讲解 + 示例代码 + 类比 + 要点总结。

图结构：
  START → search_references → generate_content → END

  search_references  — RAG 本地知识库 + Tavily 网络搜索，收集参考资料
  generate_content   — 基于课时信息 + 参考资料，让 LLM 生成完整课件
"""

from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from src.agent.utils import llm_json
from src.rag.knowledge_base import search as kb_search, search_by_source as kb_search_by_source
from src.tools.search import web_search
from src.schemas.lesson import LessonContent


# ── State ────────────────────────────────────────────────────

class LessonState(TypedDict):
    plan_title:    str         # 计划标题（提供大背景）
    plan_level:    str         # 用户起始水平
    lesson:        dict        # 课时信息（来自 syllabus：title, objectives, topics 等）
    references:    list[str]   # 检索到的参考资料
    content:       dict        # 最终输出：LessonContent 字典
    book_filename: str         # 可选：关联书籍文件名，用于 RAG 过滤


# ── 节点1：检索参考资料 ──────────────────────────────────────

def search_references_node(state: LessonState) -> dict:
    """
    用课时标题和知识点作为查询词，从本地知识库和网络搜索中收集参考资料。
    如果计划关联了书籍，优先从该书籍中检索内容。
    """
    lesson = state["lesson"]
    query = f"{lesson['title']} {' '.join(lesson.get('topics', []))}"
    book_filename = state.get("book_filename", "")

    all_refs = []

    # 如果有关联书籍，优先从书中检索
    if book_filename:
        book_chunks = kb_search_by_source(query, source=book_filename, n_results=5)
        if book_chunks:
            all_refs.append("【参考书籍内容（课件必须严格基于此内容）】\n" + "\n\n".join(book_chunks))
        print(f"[课件] 从书籍检索：{len(book_chunks)} 条")

    # 通用本地 RAG（去除与书籍检索重复的内容）
    local_chunks = kb_search(query, n_results=3)
    if local_chunks and book_filename:
        book_prefixes = {chunk[:50] for chunk in book_chunks}
        local_chunks = [c for c in local_chunks if c[:50] not in book_prefixes]
    if local_chunks:
        all_refs.append("【本地知识库】\n" + "\n\n".join(local_chunks))

    # 网络搜索
    web_chunks = web_search(query, max_results=2)
    if web_chunks:
        all_refs.append("【网络搜索】\n" + "\n\n".join(web_chunks))

    print(f"[课件] 检索参考资料：本地 {len(local_chunks)} 条，网络 {len(web_chunks)} 条")
    return {"references": all_refs}


# ── 节点2：生成课件内容 ──────────────────────────────────────

def generate_content_node(state: LessonState) -> dict:
    """基于课时信息和参考资料，生成完整的教学内容。"""
    lesson = state["lesson"]
    refs = state.get("references", [])

    book_filename = state.get("book_filename", "")
    ref_section = ""
    if refs:
        ref_section = (
            "\n\n【参考资料（基于实时检索，内容可直接引用）】\n"
            + "\n\n---\n\n".join(refs)
        )

    prompt = f"""请为以下课时生成完整的教学内容：

课时信息：
- 课时编号：{lesson['lesson_index']}
- 课时标题：{lesson['title']}
- 学习目标：{', '.join(lesson.get('objectives', []))}
- 核心知识点：{', '.join(lesson.get('topics', []))}
- 预计时长：{lesson.get('duration_min', 60)} 分钟

学习计划背景：
- 计划名称：{state['plan_title']}
- 学员水平：{state['plan_level']}
{ref_section}

要求：
- explanation 用 Markdown 格式，包含小标题（##）、段落、列表，内容要通俗易懂
- explanation 要覆盖所有核心知识点，对 {state['plan_level']} 水平的学员要从基础讲起
{"- 课件内容必须严格基于参考书籍的内容来编写，保持与书籍知识体系一致" if book_filename else ""}
- code_examples 针对��程类知识点给出可运行的示例��码，非编程类课时可为空列表
- code_examples 的 explanation 要逐行或逐段解释代码含义
- analogies 用生活中的例子解释抽象概念，让零基础也能理解
- key_takeaways 用一句话概括本课最核心的知识点
- next_hint 预告后续内容，激发学习兴趣
- 全部使用中文"""

    print(f"[课件] 生成课时 {lesson['lesson_index']}：{lesson['title']}")
    data = llm_json(prompt, LessonContent)
    print(f"[课件] 课时 {lesson['lesson_index']} 生成完成")
    return {"content": data}


# ── 构建图 ────────────────────────────────────────────────────

def build_lesson_graph():
    graph = StateGraph(LessonState)
    graph.add_node("search_references", search_references_node)
    graph.add_node("generate_content",  generate_content_node)
    graph.add_edge(START,               "search_references")
    graph.add_edge("search_references", "generate_content")
    graph.add_edge("generate_content",  END)
    return graph.compile()


lesson_graph = build_lesson_graph()
