from pydantic import BaseModel, Field


class CodeExample(BaseModel):
    """一个示例代码块。"""
    title:       str = Field(..., description="示例标题，例如：用 for 循环遍历列表")
    language:    str = Field(..., description="编程语言，例如：python")
    code:        str = Field(..., description="完整的可运行代码")
    explanation: str = Field(..., description="代码逐行解释，用通俗语言")


class LessonContent(BaseModel):
    """一个课时的完整教学内容。"""
    lesson_index:   int             = Field(..., description="课时编号")
    title:          str             = Field(..., description="课时标题")
    explanation:    str             = Field(..., description="核心概念讲解，使用 Markdown 格式，包含小标题和段落")
    code_examples:  list[CodeExample] = Field(default_factory=list, description="示例代码列表，0-3个，非编程类课时可为空")
    analogies:      list[str]       = Field(..., description="生活类比，用日常例子解释抽象概念，1-3个")
    key_takeaways:  list[str]       = Field(..., description="核心要点总结，3-5条，用一句话概括")
    next_hint:      str             = Field(..., description="预告下一课时的内容，引导学习兴趣")
