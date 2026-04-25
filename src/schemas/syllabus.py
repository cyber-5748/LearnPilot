from pydantic import BaseModel, Field


class Lesson(BaseModel):
    """一个具体的课时。"""
    lesson_index: int       = Field(..., description="课时全局编号，从1开始连续递增")
    title:        str       = Field(..., description="课时标题，例如：变量与数据类型")
    objectives:   list[str] = Field(..., description="学习目标，2-3条，以'能够'开头")
    topics:       list[str] = Field(..., description="核心知识点，3-5个")
    duration_min: int       = Field(..., description="预计学习时长（分钟）")
    prerequisites: list[int] = Field(default_factory=list, description="前置课时编号列表，空表示无前置")


class PhaseSyllabus(BaseModel):
    """一个阶段拆解后的课时列表。"""
    phase:   int           = Field(..., description="阶段编号，与大纲中的 phase 对应")
    title:   str           = Field(..., description="阶段标题，与大纲一致")
    lessons: list[Lesson]  = Field(..., description="本阶段的课时列表，5-10个")


class Syllabus(BaseModel):
    """完整的章节拆解结果：所有阶段的课时列表。"""
    plan_title:    str                = Field(..., description="关联的学习计划标题")
    total_lessons: int                = Field(..., description="课时总数")
    phases:        list[PhaseSyllabus] = Field(..., description="按阶段组织的课时列表")
