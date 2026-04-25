from pydantic import BaseModel, Field


class LearningRequirements(BaseModel):
    """从用户自然语言中解析出的学习需求。"""
    level:       str   = Field(..., description="当前基础：零基础 / 初级 / 中级 / 高级")
    goal:        str   = Field(..., description="学习目标，一句话概括")
    total_weeks: int   = Field(..., description="计划学习的总周数")
    daily_hours: float = Field(..., description="每天投入的学习时长（小时）")
    purpose:     str   = Field(..., description="学习用途，例如：求职 / 做项目 / 兴趣爱好")


class LearningPhase(BaseModel):
    """学习计划中的一个阶段。"""
    phase:      int        = Field(..., description="阶段编号，从1开始")
    title:      str        = Field(..., description="阶段标题，例如：Python 基础入门")
    weeks:      str        = Field(..., description="时间范围，例如：第1-2周")
    goal:       str        = Field(..., description="本阶段结束时能达到的能力目标")
    topics:     list[str]  = Field(..., description="本阶段要掌握的核心知识点，3-6个")
    daily_plan: str        = Field(..., description="每日学习安排建议，例如：前45分钟学新概念，后45分钟做练习")
    milestone:  str        = Field(..., description="阶段里程碑：完成后能独立做什么事")


class LearningPlan(BaseModel):
    """完整的个性化学习计划。"""
    title:        str               = Field(..., description="计划标题")
    summary:      str               = Field(..., description="一句话总结这份计划的特点")
    level:        str               = Field(..., description="起始水平")
    total_weeks:  int               = Field(..., description="总周数")
    daily_hours:  float             = Field(..., description="每日学习时长（小时）")
    total_hours:  int               = Field(..., description="总学习时长（小时），等于 total_weeks × 7 × daily_hours 取整")
    phases:       list[LearningPhase] = Field(..., description="学习阶段列表，3-5个阶段")
    tips:         list[str]         = Field(..., description="针对该用户情况的个性化学习建议，3-5条")
