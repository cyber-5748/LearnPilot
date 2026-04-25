"""
学习计划生成的 LangGraph 工作流。

两个节点：
  parse_requirements  ← 从自然语言中提取结构化需求
  generate_plan       ← 根据需求生成完整学习计划

图结构：
  START → parse_requirements → generate_plan → END
"""

from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from src.agent.utils import llm_json
from src.schemas.plan import LearningRequirements, LearningPlan


# ── State ────────────────────────────────────────────────────

class PlanState(TypedDict):
    user_input:   str   # 用户的原始自然语言输入
    requirements: dict  # 解析后的需求（LearningRequirements 的字典形式）
    plan:         dict  # 生成的学习计划（LearningPlan 的字典形式）
    book_toc:     str   # 可选：参考书籍的目录结构


# ── 节点1：需求解析 ───────────────────────────────────────────

def parse_requirements_node(state: PlanState) -> dict:
    """
    从用户的一句话需求中，提取结构化的学习需求。

    例如：
      输入："零基础，2个月学AI Agent，每天1.5小时，用于求职"
      输出：{level: "零基础", goal: "学习AI Agent开发", total_weeks: 8,
              daily_hours: 1.5, purpose: "求职"}
    """
    print(f"[计划] 解析需求：{state['user_input']}")
    prompt = f"""请从下面这段话中提取用户的学习需求：

"{state['user_input']}"

注意：
- total_weeks 从时长描述中换算（2个月=8周，1个月=4周，100天≈14周）
- 如果用户没有说明某项信息，根据上下文合理推断
- purpose 如果没说就填"综合提升"
- 全部使用中文"""

    data = llm_json(prompt, LearningRequirements)
    print(f"[计划] 需求解析完成：{data}")
    return {"requirements": data}


# ── 节点2：计划生成 ───────────────────────────────────────────

def generate_plan_node(state: PlanState) -> dict:
    """
    根据解析出的需求，生成完整的、个性化的学习计划。
    """
    req = state["requirements"]
    book_toc = state.get("book_toc", "")
    print(f"[计划] 生成计划，目标：{req.get('goal')}，共{req.get('total_weeks')}周" +
          (f"，参考书籍目录" if book_toc else ""))

    book_section = ""
    if book_toc:
        book_section = f"""
【参考书籍目录结构】
以下是用户上传的学习书籍目录，你必须严格参考这本书的知识结构来组织学习阶段：
- phases 的划分应该对应书籍的章节分组
- 每个阶段的 topics 应该来自书籍对应章节的内容
- 学习顺序应该尊重书籍的编排顺序

{book_toc}
"""

    prompt = f"""请根据以下学习需求，生成一份详细的个性化学习计划：

学习需求：
- 当前水平：{req.get('level')}
- 学习目标：{req.get('goal')}
- 学习周期：{req.get('total_weeks')} 周
- 每天时长：{req.get('daily_hours')} 小时
- 学习用途：{req.get('purpose')}
{book_section}
要求：
- phases 包含 3-5 个循序渐进的阶段，时间划分合理
- 每个阶段的 topics 要具体（不要泛泛而谈）
- daily_plan 要结合每天 {req.get('daily_hours')} 小时的实际情况安排
- milestone 要具体可验证（能做什么，而不是"学会了"）
- tips 要针对 {req.get('level')} 基础、{req.get('purpose')} 用途给出个性化建议
- total_hours 计算：{req.get('total_weeks')} 周 × 7天 × {req.get('daily_hours')} 小时，取整
- 全部使用中文"""

    data = llm_json(prompt, LearningPlan)
    print(f"[计划] 生成完成：{data.get('title')}")
    return {"plan": data}


# ── 构建图 ────────────────────────────────────────────────────

def build_plan_graph():
    graph = StateGraph(PlanState)
    graph.add_node("parse_requirements", parse_requirements_node)
    graph.add_node("generate_plan",      generate_plan_node)
    graph.add_edge(START,                "parse_requirements")
    graph.add_edge("parse_requirements", "generate_plan")
    graph.add_edge("generate_plan",      END)
    return graph.compile()


plan_graph = build_plan_graph()
