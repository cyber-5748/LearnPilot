from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.agent.plan_graph import plan_graph
from src.agent.report_graph import report_graph
from src.schemas.plan import LearningPlan
from src.schemas.report import LearningReport
from src.storage_plans import (
    save_plan, list_plans, get_plan, rename_plan, delete_plan, pin_plan,
    get_plan_progress, get_all_submissions, get_syllabus,
    get_report as get_cached_report, save_report, get_book,
)

router = APIRouter()


class PlanRequest(BaseModel):
    user_input: str = Field(..., min_length=5, max_length=200)
    book_id: int | None = Field(None, description="关联书籍 ID，计划将参考书籍结构")


class RenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)


@router.post("/plan")
def create_plan(request: PlanRequest):
    try:
        # 如果指定了书籍，获取目录结构注入到计划生成中
        book_toc = ""
        if request.book_id:
            book_data = get_book(request.book_id)
            if book_data:
                book_toc = book_data.get("toc_text", "")

        result = plan_graph.invoke({
            "user_input": request.user_input,
            "requirements": {},
            "plan": {},
            "book_toc": book_toc,
        })
        plan = LearningPlan(**result["plan"])
        plan_id = save_plan(
            title=plan.title,
            user_input=request.user_input,
            plan_dict=plan.model_dump(),
            book_id=request.book_id,
        )
        return {"plan_id": plan_id, **plan.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败：{str(e)}")


@router.get("/plans")
def get_plans():
    return list_plans()


@router.get("/plans/{plan_id}")
def get_plan_detail(plan_id: int):
    data = get_plan(plan_id)
    if not data:
        raise HTTPException(status_code=404, detail="计划不存在")
    return data


@router.patch("/plans/{plan_id}/rename")
def rename_plan_api(plan_id: int, body: RenameRequest):
    if not rename_plan(plan_id, body.title):
        raise HTTPException(status_code=404, detail="计划不存在")
    return {"ok": True}


@router.patch("/plans/{plan_id}/pin")
def pin_plan_api(plan_id: int, pinned: bool = True):
    if not pin_plan(plan_id, pinned):
        raise HTTPException(status_code=404, detail="计划不存在")
    return {"ok": True}


@router.get("/plans/{plan_id}/report")
def get_report(plan_id: int, refresh: bool = False):
    """
    获取学习报告。

    逻辑：
    1. 查缓存 → 有缓存则对比最新提交时间，判断是否有新进度
    2. 有缓存且 refresh=False → 返回缓存报告 + has_update 标记
    3. 无缓存 或 refresh=True → 重新生成并存库
    """
    plan_data = get_plan(plan_id)
    if not plan_data:
        raise HTTPException(status_code=404, detail="计划不存在")

    subs = get_all_submissions(plan_id)
    if not subs:
        raise HTTPException(status_code=400, detail="尚未提交过任何作业，无法生成报告")

    # 查缓存
    cached = get_cached_report(plan_id)

    if cached and not refresh:
        # 对比：报告生成时间 vs 最新提交时间
        report_time = cached["created_at"]
        latest_submit = max(s["submitted_at"] for s in subs)
        has_update = latest_submit > report_time
        new_submissions = sum(1 for s in subs if s["submitted_at"] > report_time) if has_update else 0
        return {
            "report": cached["report"],
            "generated_at": report_time,
            "has_update": has_update,
            "new_submissions": new_submissions,
            "from_cache": True,
        }

    # 无缓存 或 用户要求刷新 → 重新生成
    syllabus_data = get_syllabus(plan_id)
    syllabus = syllabus_data["syllabus"] if syllabus_data else {}
    total_lessons = syllabus.get("total_lessons", 0)

    plan = plan_data["plan"]
    try:
        result = report_graph.invoke({
            "plan_title": plan.get("title", ""),
            "plan_level": plan.get("level", "零基础"),
            "total_lessons": total_lessons,
            "submissions": subs,
            "syllabus": syllabus,
            "report": {},
        })
        report = result["report"]
        save_report(plan_id, report)
        return {
            "report": report,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "has_update": False,
            "new_submissions": 0,
            "from_cache": False,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败：{str(e)}")


@router.get("/plans/{plan_id}/progress")
def get_progress(plan_id: int):
    """获取计划下所有课时的学习进度。"""
    data = get_plan(plan_id)
    if not data:
        raise HTTPException(status_code=404, detail="计划不存在")
    return get_plan_progress(plan_id)


@router.delete("/plans/{plan_id}")
def delete_plan_api(plan_id: int):
    if not delete_plan(plan_id):
        raise HTTPException(status_code=404, detail="计划不存在")
    return {"ok": True}
