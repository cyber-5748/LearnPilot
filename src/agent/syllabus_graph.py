"""
章节拆解的 LangGraph 工作流。

将学习大纲中的每个阶段拆解为具体的课时列表。

图结构：
  START → expand_phases → validate_sequence → END

  expand_phases   — 遍历大纲中的每个阶段，让 LLM 拆解为 5-10 个具体课时
  validate_sequence — 校验课时编号连续性和前置依赖合理性，必要时修正
"""

import json
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from openai import OpenAI

from src.config import settings
from src.schemas.syllabus import PhaseSyllabus, Syllabus


# ── State ────────────────────────────────────────────────────

class SyllabusState(TypedDict):
    plan:     dict        # 完整的学习大纲（LearningPlan 字典）
    phases:   list[dict]  # 拆解结果：每阶段的课时列表
    syllabus: dict        # 最终输出：Syllabus 字典
    book_toc: str         # 可选：参考书籍的目录结构


# ── 工具函数 ──────────────────────────────────────────────────

def _llm_json(prompt: str, schema: type) -> dict:
    """调用 LLM，要求严格按照 schema 输出 JSON。"""
    schema_str = json.dumps(schema.model_json_schema(), ensure_ascii=False, indent=2)
    system = (
        "你只输出合法的 JSON，严格符合下面的 Schema，不输出任何解释文字，不加 markdown 代码块。\n\n"
        f"Schema：\n{schema_str}"
    )
    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
    resp = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
    )
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ── 节点1：阶段展开 ─────────────────────────────────────────

def expand_phases_node(state: SyllabusState) -> dict:
    """
    遍历大纲中的每个阶段，逐阶段调用 LLM 拆解为具体课时。

    为什么逐阶段调用而不是一次性拆解全部？
    - 单次请求的输出量可控，LLM 不容易丢字段
    - 可以在 prompt 中传入前面阶段已生成的课时，保证编号连续
    """
    plan = state["plan"]
    book_toc = state.get("book_toc", "")
    all_phases = []
    lesson_counter = 1  # 全局课时编号计数器

    for phase in plan["phases"]:
        print(f"[章节拆解] 展开阶段 {phase['phase']}：{phase['title']}")

        # 构建前序课时摘要，让 LLM 知道编号从几开始
        prev_summary = ""
        if all_phases:
            prev_lessons = []
            for p in all_phases:
                for l in p["lessons"]:
                    prev_lessons.append(f"  课时{l['lesson_index']}: {l['title']}")
            prev_summary = "已有课时（编号已占用）：\n" + "\n".join(prev_lessons) + "\n\n"

        book_section = ""
        if book_toc:
            book_section = f"""
【参考书籍目录】
课时拆解必须严格参考以下书籍目录结构，每个课时应对应书中的具体章节或小节：

{book_toc}

"""

        prompt = f"""{prev_summary}{book_section}请将下面这个学习阶段拆解为具体的课时列表：

阶段信息：
- 阶段编号：{phase['phase']}
- 阶段标题：{phase['title']}
- 阶段目标：{phase['goal']}
- 核心知识点：{', '.join(phase['topics'])}
- 时间范围：{phase['weeks']}
- 每日安排：{phase['daily_plan']}
- 里程碑：{phase['milestone']}

所属计划整体信息：
- 计划标题：{plan['title']}
- 起始水平：{plan['level']}
- 每日学习时长：{plan['daily_hours']} 小时

要求：
- 拆解为 5-10 个具体课时
- lesson_index 从 {lesson_counter} 开始连续递增
- 每个课时的 duration_min 应该合理（通常 30-90 分钟），总时长要匹配阶段的时间范围
- objectives 以"能够…"开头，具体可验证
- topics 要比阶段级别更细粒度{'，且应对应书籍中的具体小节内容' if book_toc else ''}
- prerequisites 填写前置课时的 lesson_index，第一课时填空列表
- 同一阶段内课时通常顺序依赖，但并行的知识点可以没有依赖
- 全部使用中文"""

        data = _llm_json(prompt, PhaseSyllabus)
        all_phases.append(data)

        # 更新全局计数器
        if data["lessons"]:
            lesson_counter = max(l["lesson_index"] for l in data["lessons"]) + 1

        print(f"[章节拆解] 阶段 {phase['phase']} 拆解完成，{len(data['lessons'])} 个课时")

    return {"phases": all_phases}


# ── 节点2：校验与修正 ───────────────────────────────────────

def validate_sequence_node(state: SyllabusState) -> dict:
    """
    校验课时编号的连续性和前置依赖的合理性。
    不再调用 LLM，纯 Python 逻辑修正。
    """
    phases = state["phases"]
    all_lesson_ids = set()
    corrected_phases = []

    # 第一遍：强制编号连续
    counter = 1
    id_remap = {}  # 旧编号 → 新编号

    for phase in phases:
        corrected_lessons = []
        for lesson in phase["lessons"]:
            old_id = lesson["lesson_index"]
            id_remap[old_id] = counter
            lesson["lesson_index"] = counter
            all_lesson_ids.add(counter)
            corrected_lessons.append(lesson)
            counter += 1
        phase["lessons"] = corrected_lessons
        corrected_phases.append(phase)

    # 第二遍：修正 prerequisites 中的引用
    for phase in corrected_phases:
        for lesson in phase["lessons"]:
            new_prereqs = []
            for pre in lesson.get("prerequisites", []):
                remapped = id_remap.get(pre, pre)
                # 前置课时必须存在且编号小于自己
                if remapped in all_lesson_ids and remapped < lesson["lesson_index"]:
                    new_prereqs.append(remapped)
            lesson["prerequisites"] = new_prereqs

    total = sum(len(p["lessons"]) for p in corrected_phases)
    plan_title = state["plan"].get("title", "")

    syllabus = {
        "plan_title": plan_title,
        "total_lessons": total,
        "phases": corrected_phases,
    }

    print(f"[章节拆解] 校验完成，共 {total} 个课时")
    return {"syllabus": syllabus}


# ── 构建图 ────────────────────────────────────────────────────

def build_syllabus_graph():
    graph = StateGraph(SyllabusState)
    graph.add_node("expand_phases",     expand_phases_node)
    graph.add_node("validate_sequence", validate_sequence_node)
    graph.add_edge(START,               "expand_phases")
    graph.add_edge("expand_phases",     "validate_sequence")
    graph.add_edge("validate_sequence", END)
    return graph.compile()


syllabus_graph = build_syllabus_graph()
