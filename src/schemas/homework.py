from pydantic import BaseModel, Field


class Question(BaseModel):
    """一道作业题目。"""
    index:    int       = Field(..., description="题目编号，从1开始")
    type:     str       = Field(..., description="题目类型：choice / coding / open")
    question: str       = Field(..., description="题目描述")
    options:  list[str] = Field(default_factory=list, description="选择题选项（A/B/C/D），仅 choice 类型有")
    answer:   str       = Field(..., description="标准答案：choice 填选项字母，coding 填参考代码，open 填参考要点")
    points:   int       = Field(..., description="分值")


class Homework(BaseModel):
    """一个课时的作业。"""
    lesson_index: int             = Field(..., description="关联的课时编号")
    title:        str             = Field(..., description="作业标题")
    total_points: int             = Field(..., description="总分")
    questions:    list[Question]  = Field(..., description="题目列表，4-6题")


class AnswerItem(BaseModel):
    """用户提交的单题答案。"""
    index:       int  = Field(..., description="题目编号")
    user_answer: str  = Field(..., description="用户的答案")


class GradedItem(BaseModel):
    """单题评判结果。"""
    index:       int  = Field(..., description="题目编号")
    user_answer: str  = Field(..., description="用户答案")
    is_correct:  bool = Field(..., description="是否正确")
    score:       int  = Field(..., description="得分")
    feedback:    str  = Field(..., description="评语和解析")


class SubmissionResult(BaseModel):
    """完整的作业评判结果。"""
    lesson_index: int              = Field(..., description="课时编号")
    total_score:  int              = Field(..., description="总得分")
    max_score:    int              = Field(..., description="满分")
    passed:       bool             = Field(..., description="是否通过（>=80%）")
    items:        list[GradedItem] = Field(..., description="逐题评判结果")
    weak_points:  list[str]        = Field(..., description="薄弱知识点，根据错题分析")
    summary:      str              = Field(..., description="整体评价与学习建议")
