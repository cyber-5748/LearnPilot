from fastapi import APIRouter, HTTPException

from src.agent.syllabus_graph import syllabus_graph
from src.schemas.syllabus import Syllabus
from src.storage_plans import get_plan, get_syllabus, save_syllabus, delete_syllabus, get_book

router = APIRouter()


@router.post("/plans/{plan_id}/syllabus", response_model=Syllabus)
def create_syllabus(plan_id: int):
    """根据已有的学习大纲，生成章节拆解。"""
    plan_data = get_plan(plan_id)
    if not plan_data:
        raise HTTPException(status_code=404, detail="计划不存在")

    # 如果计划关联了书籍，获取目录结构
    book_toc = ""
    book_id = plan_data.get("book_id")
    if book_id:
        book_data = get_book(book_id)
        if book_data:
            book_toc = book_data.get("toc_text", "")

    try:
        result = syllabus_graph.invoke({
            "plan": plan_data["plan"],
            "phases": [],
            "syllabus": {},
            "book_toc": book_toc,
        })
        syllabus = Syllabus(**result["syllabus"])
        save_syllabus(plan_id=plan_id, syllabus_dict=syllabus.model_dump())
        return syllabus
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"章节拆解失败：{str(e)}")


@router.get("/plans/{plan_id}/syllabus")
def get_syllabus_api(plan_id: int):
    """获取已有的章节拆解结果。"""
    data = get_syllabus(plan_id)
    if not data:
        raise HTTPException(status_code=404, detail="该计划尚未拆解章节")
    return data


@router.delete("/plans/{plan_id}/syllabus")
def delete_syllabus_api(plan_id: int):
    """删除章节拆解（可重新生成）。"""
    if not delete_syllabus(plan_id):
        raise HTTPException(status_code=404, detail="该计划没有章节拆解")
    return {"ok": True}
