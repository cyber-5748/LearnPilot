"""
作业系统的 LangGraph 工作流。

包含两个独立的图：
  1. 出题图：generate_graph — 根据课件内容生成 4-6 道作业题
     START → generate_questions → END

  2. 批改图：grade_graph — 根据标准答案批改用户提交的答案
     START → grade_answers → END
"""

from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from src.agent.utils import llm_json
from src.schemas.homework import Homework, SubmissionResult


# ── State ────────────────────────────────────────────────────

class GenerateState(TypedDict):
    plan_title:    str    # 计划标题
    plan_level:    str    # 用户水平
    lesson:        dict   # 课时信息（title, objectives, topics）
    lesson_content: dict  # 课件内容（explanation, code_examples 等）
    homework:      dict   # 输出：Homework 字典


class GradeState(TypedDict):
    homework:   dict       # 作业题目（Homework 字典）
    answers:    list[dict] # 用户提交的答案（AnswerItem 列表）
    result:     dict       # 输出：SubmissionResult 字典


# ══════════════════════════════════════════════════════════════
# 出题图
# ══════════════════════════════════════════════════════════════

def generate_questions_node(state: GenerateState) -> dict:
    """根据课件内容生成作业题目。"""
    lesson = state["lesson"]
    content = state.get("lesson_content", {})

    # 提取课件中的代码示例摘要
    code_summary = ""
    examples = content.get("code_examples", [])
    if examples:
        code_summary = "\n\n课件中的代码示例：\n"
        for ex in examples:
            code_summary += f"- {ex.get('title', '')}: {ex.get('language', '')} 代码\n"

    prompt = f"""请为以下课时生成一套作业题目：

课时信息：
- 课时编号：{lesson['lesson_index']}
- 课时标题：{lesson['title']}
- 学习目标：{', '.join(lesson.get('objectives', []))}
- 核心知识点：{', '.join(lesson.get('topics', []))}

学习计划背景：
- 计划名称：{state['plan_title']}
- 学员水平：{state['plan_level']}
{code_summary}

要求：
- 生成 4-6 道题，总分 100 分
- 题目类型混合搭配：
  - choice（选择题）：2-3 道，每道 10-15 分，options 填 4 个选项（A/B/C/D），answer 填正确选项字母
  - coding（编程题）：1-2 道，每道 15-25 分（仅编程类课程），answer 填参考代码
  - open（开放题）：1-2 道，每道 15-20 分，answer 填参考要点
- index 从 1 开始连续递增
- 题目难度递进：先易后难
- 紧扣课件中的核心知识点，不超出课时范围
- 选择题的干扰项要有迷惑性但不模棱两可
- 全部使用中文"""

    print(f"[作业] 生成课时 {lesson['lesson_index']} 的作业题目")
    data = llm_json(prompt, Homework)
    print(f"[作业] 课时 {lesson['lesson_index']} 作业生成完成，{len(data.get('questions', []))} 道题")
    return {"homework": data}


# ══════════════════════════════════════════════════════════════
# 批改图
# ══════════════════════════════════════════════════════════════

def grade_answers_node(state: GradeState) -> dict:
    """批改用户提交的答案，生成评分和反馈。"""
    homework = state["homework"]
    answers = state["answers"]

    # 构建题目+答案对照表
    questions_text = ""
    for q in homework.get("questions", []):
        questions_text += f"\n题目 {q['index']}（{q['type']}，{q['points']} 分）：{q['question']}\n"
        if q.get("options"):
            for opt in q["options"]:
                questions_text += f"  {opt}\n"
        questions_text += f"标准答案：{q['answer']}\n"

    answers_text = ""
    for a in answers:
        answers_text += f"题目 {a['index']}，用户答案：{a['user_answer']}\n"

    prompt = f"""请批改以下作业，逐题评分并给出反馈：

作业标题：{homework.get('title', '')}
课时编号：{homework.get('lesson_index', 0)}
满分：{homework.get('total_points', 100)}

题目与标准答案：
{questions_text}

用户提交的答案：
{answers_text}

评分规则：
- choice 类型：答案完全匹配标准答案才得分，否则 0 分
- coding 类型：根据代码逻辑正确性、关键步骤是否体现给分（可部分给分）
- open 类型：根据答案是否覆盖关键要点给分（可部分给分）
- is_correct 字段：得满分为 true，否则为 false
- feedback 要解释为什么对/错，给出知识点提示
- weak_points 列出用户答错的题涉及的知识点
- passed：总得分 >= 满分的 80% 为通过
- summary：整体评价，鼓励为主，指出薄弱环节并给出学习建议
- 全部使用中文"""

    print(f"[作业] 批改课时 {homework.get('lesson_index', '?')} 的作业")
    data = llm_json(prompt, SubmissionResult)
    print(f"[作业] 批改完成，得分：{data.get('total_score', 0)}/{data.get('max_score', 100)}")
    return {"result": data}


# ── 构建图 ────────────────────────────────────────────────────

def build_generate_graph():
    graph = StateGraph(GenerateState)
    graph.add_node("generate_questions", generate_questions_node)
    graph.add_edge(START, "generate_questions")
    graph.add_edge("generate_questions", END)
    return graph.compile()


def build_grade_graph():
    graph = StateGraph(GradeState)
    graph.add_node("grade_answers", grade_answers_node)
    graph.add_edge(START, "grade_answers")
    graph.add_edge("grade_answers", END)
    return graph.compile()


generate_graph = build_generate_graph()
grade_graph = build_grade_graph()
