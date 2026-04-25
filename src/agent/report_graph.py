"""
学习报告的 LangGraph 工作流。

聚合所有课时的作业成绩，让 LLM 生成综合学习分析。

图结构：
  START → analyze_scores → END

  analyze_scores — 基于成绩数据，LLM 分析薄弱点、优势、建议
"""

import json
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from openai import OpenAI

from src.config import settings
from src.schemas.report import LearningReport


# ── State ────────────────────────────────────────────────────

class ReportState(TypedDict):
    plan_title:     str         # 计划标题
    plan_level:     str         # 用户水平
    total_lessons:  int         # 总课时数
    submissions:    list[dict]  # 各课时提交数据
    syllabus:       dict        # 大纲信息
    report:         dict        # 输出：LearningReport 字典


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


# ── 节点：分析成绩 ──────────────────────────────────────────

def analyze_scores_node(state: ReportState) -> dict:
    """聚合成绩数据，让 LLM 生成综合分析报告。"""
    subs = state["submissions"]
    syllabus = state.get("syllabus", {})

    # 构建课时标题映射
    title_map = {}
    for phase in syllabus.get("phases", []):
        for lesson in phase.get("lessons", []):
            title_map[lesson["lesson_index"]] = lesson["title"]

    # 构建成绩摘要
    scores_text = ""
    all_weak = []
    total_score = 0
    total_max = 0
    passed_count = 0
    lessons_data = []

    for sub in subs:
        idx = sub["lesson_index"]
        title = title_map.get(idx, f"课时{idx}")
        s, m = sub["score"], sub["max_score"]
        is_passed = s >= m * 0.8
        total_score += s
        total_max += m
        if is_passed:
            passed_count += 1

        lessons_data.append({
            "lesson_index": idx, "title": title,
            "score": s, "max_score": m, "passed": is_passed,
        })

        scores_text += f"- 课时{idx}「{title}」：{s}/{m}（{'通过' if is_passed else '未通过'}）\n"

        # 收集薄弱知识点
        result = sub.get("result", {})
        weak = result.get("weak_points", [])
        all_weak.extend(weak)

    total_lessons = state["total_lessons"]
    completed = len(subs)
    score_pct = round(total_score / total_max * 100) if total_max > 0 else 0

    # 去重薄弱知识点
    unique_weak = list(dict.fromkeys(all_weak))

    prompt = f"""请根据以下学习成绩数据，生成一份综合学习报告：

计划标题：{state['plan_title']}
学员水平：{state['plan_level']}
总课时数：{total_lessons}
已完成作业：{completed} 课时
已通过：{passed_count} 课时
总得分：{total_score}/{total_max}（{score_pct}%）

各课时成绩：
{scores_text}

已识别的薄弱知识点：
{chr(10).join('- ' + w for w in unique_weak) if unique_weak else '- 暂无'}

要求：
- plan_title、total_lessons、completed、passed、total_score、total_max、score_pct 直接填入上面的数据
- lessons 直接填入各课时的成绩数据
- weak_points：汇总并精炼薄弱知识点（去重合并，最多 8 个）
- strengths：从通过的课时中总结掌握较好的知识领域（3-5 个）
- suggestions：给出具体、可执行的学习建议（3-5 条），针对薄弱环节
- summary：200字左右的整体评价，包括学习态度评价、知识掌握程度、下一步建议
- 语气鼓励为主，客观指出不足
- 全部使用中文"""

    print(f"[报告] 生成学习报告：{state['plan_title']}")
    data = _llm_json(prompt, LearningReport)

    # 用实际数据覆盖（防止 LLM 编造数据）
    data["plan_title"] = state["plan_title"]
    data["total_lessons"] = total_lessons
    data["completed"] = completed
    data["passed"] = passed_count
    data["total_score"] = total_score
    data["total_max"] = total_max
    data["score_pct"] = score_pct
    data["lessons"] = lessons_data

    print(f"[报告] 报告生成完成")
    return {"report": data}


# ── 构建图 ────────────────────────────────────────────────────

def build_report_graph():
    graph = StateGraph(ReportState)
    graph.add_node("analyze_scores", analyze_scores_node)
    graph.add_edge(START, "analyze_scores")
    graph.add_edge("analyze_scores", END)
    return graph.compile()


report_graph = build_report_graph()
