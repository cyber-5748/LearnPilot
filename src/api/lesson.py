from fastapi import APIRouter, HTTPException

from src.agent.lesson_graph import lesson_graph
from src.schemas.lesson import LessonContent
from src.storage_plans import get_plan, get_syllabus, get_lesson_content, save_lesson_content, get_book

router = APIRouter()


def _find_lesson(syllabus: dict, lesson_index: int) -> dict | None:
    """从 syllabus 结构中找到指定编号的课时。"""
    for phase in syllabus.get("phases", []):
        for lesson in phase.get("lessons", []):
            if lesson["lesson_index"] == lesson_index:
                return lesson
    return None


@router.post("/plans/{plan_id}/lessons/{lesson_index}/generate", response_model=LessonContent)
def generate_lesson(plan_id: int, lesson_index: int):
    """为指定课时生成教学内容。有缓存则直接返回，无缓存则调用 LLM 生成。"""
    # 1. 检查缓存
    cached = get_lesson_content(plan_id, lesson_index)
    if cached:
        return LessonContent(**cached["content"])

    # 2. 加载大纲和章节拆解
    plan_data = get_plan(plan_id)
    if not plan_data:
        raise HTTPException(status_code=404, detail="计划不存在")

    syllabus_data = get_syllabus(plan_id)
    if not syllabus_data:
        raise HTTPException(status_code=404, detail="该计划尚未拆解章节，请先拆解")

    lesson = _find_lesson(syllabus_data["syllabus"], lesson_index)
    if not lesson:
        raise HTTPException(status_code=404, detail=f"课时 {lesson_index} 不存在")

    # 3. 调用 LangGraph 生成课件（如果关联了书籍，传入文件名用于 RAG 过滤）
    plan = plan_data["plan"]
    book_filename = ""
    book_id = plan_data.get("book_id")
    if book_id:
        book_data = get_book(book_id)
        if book_data:
            book_filename = book_data.get("filename", "")

    try:
        result = lesson_graph.invoke({
            "plan_title": plan.get("title", ""),
            "plan_level": plan.get("level", "零基础"),
            "lesson": lesson,
            "references": [],
            "content": {},
            "book_filename": book_filename,
        })
        content = LessonContent(**result["content"])
        save_lesson_content(plan_id, lesson_index, content.model_dump())
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"课件生成失败：{str(e)}")


@router.get("/plans/{plan_id}/lessons/{lesson_index}")
def get_lesson(plan_id: int, lesson_index: int):
    """获取已生成的课件内容。"""
    data = get_lesson_content(plan_id, lesson_index)
    if not data:
        raise HTTPException(status_code=404, detail="该课时尚未生成课件")
    return data
