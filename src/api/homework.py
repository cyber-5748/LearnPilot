from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.agent.homework_graph import generate_graph, grade_graph
from src.schemas.homework import Homework, AnswerItem, SubmissionResult
from src.storage_plans import (
    get_plan, get_syllabus, get_lesson_content,
    get_homework, save_homework,
    save_submission, get_latest_submission,
)

router = APIRouter()


def _find_lesson(syllabus: dict, lesson_index: int) -> dict | None:
    for phase in syllabus.get("phases", []):
        for lesson in phase.get("lessons", []):
            if lesson["lesson_index"] == lesson_index:
                return lesson
    return None


@router.post("/plans/{plan_id}/lessons/{lesson_index}/homework/generate", response_model=Homework)
def generate_homework(plan_id: int, lesson_index: int):
    """为指定课时生成作业。有缓存则直接返回。"""
    # 1. 检查缓存
    cached = get_homework(plan_id, lesson_index)
    if cached:
        return Homework(**cached["homework"])

    # 2. 加载上下文
    plan_data = get_plan(plan_id)
    if not plan_data:
        raise HTTPException(status_code=404, detail="计划不存在")

    syllabus_data = get_syllabus(plan_id)
    if not syllabus_data:
        raise HTTPException(status_code=404, detail="该计划尚未拆解章节")

    lesson = _find_lesson(syllabus_data["syllabus"], lesson_index)
    if not lesson:
        raise HTTPException(status_code=404, detail=f"课时 {lesson_index} 不存在")

    content_data = get_lesson_content(plan_id, lesson_index)
    if not content_data:
        raise HTTPException(status_code=404, detail="该课时尚未生成课件，请先生成课件")

    # 3. 调用 LangGraph 生成作业
    plan = plan_data["plan"]
    try:
        result = generate_graph.invoke({
            "plan_title": plan.get("title", ""),
            "plan_level": plan.get("level", "零基础"),
            "lesson": lesson,
            "lesson_content": content_data["content"],
            "homework": {},
        })
        hw = Homework(**result["homework"])
        save_homework(plan_id, lesson_index, hw.model_dump())
        return hw
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"作业生成失败：{str(e)}")


class SubmitRequest(BaseModel):
    answers: list[AnswerItem]


@router.post("/plans/{plan_id}/lessons/{lesson_index}/homework/submit", response_model=SubmissionResult)
def submit_homework(plan_id: int, lesson_index: int, req: SubmitRequest):
    """提交作业答案并获取批改结果。"""
    cached = get_homework(plan_id, lesson_index)
    if not cached:
        raise HTTPException(status_code=404, detail="该课时尚未生成作业")

    homework_dict = cached["homework"]

    try:
        result = grade_graph.invoke({
            "homework": homework_dict,
            "answers": [a.model_dump() for a in req.answers],
            "result": {},
        })
        sr = SubmissionResult(**result["result"])
        save_submission(
            plan_id, lesson_index,
            [a.model_dump() for a in req.answers],
            sr.model_dump(),
            sr.total_score, sr.max_score,
        )
        return sr
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"作业批改失败：{str(e)}")


@router.get("/plans/{plan_id}/lessons/{lesson_index}/homework")
def get_homework_api(plan_id: int, lesson_index: int):
    """获取已生成的作业题目。"""
    data = get_homework(plan_id, lesson_index)
    if not data:
        raise HTTPException(status_code=404, detail="该课时尚未生成作业")
    return data


@router.get("/plans/{plan_id}/lessons/{lesson_index}/homework/result")
def get_homework_result(plan_id: int, lesson_index: int):
    """获取最近一次作业批改结果。"""
    data = get_latest_submission(plan_id, lesson_index)
    if not data:
        raise HTTPException(status_code=404, detail="尚未提交过作业")
    return data
