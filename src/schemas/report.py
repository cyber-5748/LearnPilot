from pydantic import BaseModel, Field


class LessonScore(BaseModel):
    """单课时成绩摘要。"""
    lesson_index: int = Field(..., description="课时编号")
    title:        str = Field(..., description="课时标题")
    score:        int = Field(..., description="得分")
    max_score:    int = Field(..., description="满分")
    passed:       bool = Field(..., description="是否通过")


class LearningReport(BaseModel):
    """学习报告。"""
    plan_title:     str             = Field(..., description="计划标题")
    total_lessons:  int             = Field(..., description="总课时数")
    completed:      int             = Field(..., description="已完成作业的课时数")
    passed:         int             = Field(..., description="已通过的课时数")
    total_score:    int             = Field(..., description="总得分")
    total_max:      int             = Field(..., description="总满分")
    score_pct:      int             = Field(..., description="得分率（百分比）")
    lessons:        list[LessonScore] = Field(..., description="各课时成绩")
    weak_points:    list[str]       = Field(..., description="薄弱知识点汇总")
    strengths:      list[str]       = Field(..., description="掌握较好的知识点")
    suggestions:    list[str]       = Field(..., description="学习建议，3-5条")
    summary:        str             = Field(..., description="整体评价，200字左右")
