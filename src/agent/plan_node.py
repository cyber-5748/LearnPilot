# ============================================================
# 阶段9：结构化输出节点
# ============================================================
#
# 核心技巧：如何让 LLM 输出合法 JSON
#
#   第一步：用 response_format={"type": "json_object"}
#           告诉 API "我要 JSON 格式的输出"
#
#   第二步：在 Prompt 里贴上 JSON Schema
#           告诉 LLM "JSON 里要有哪些字段、什么类型"
#
#   第三步：用 json.loads() 把字符串解析成 Python 字典
#
#   第四步：用 LearningPlan(**data) 验证结构是否正确
#           如果 LLM 漏了某个字段，这里会报错，方便排查
# ============================================================

import json
from openai import OpenAI
from src.config import settings
from src.schemas.plan import LearningPlan


def generate_plan_node(topic: str) -> LearningPlan:
    """
    根据主题生成结构化学习计划。

    这不是 LangGraph 节点（不接收 State），
    而是一个普通函数，直接被 API 接口调用。
    目的是单独展示"结构化输出"这个概念。
    """

    # 把 Pydantic 模型转成 JSON Schema 字符串，贴进 Prompt
    # model_json_schema() 会自动生成描述字段名、类型、说明的 JSON
    schema_str = json.dumps(LearningPlan.model_json_schema(), ensure_ascii=False, indent=2)

    prompt = f"""你是一个学习计划设计师。
请为用户生成一份关于「{topic}」的学习计划。

【重要】你必须严格按照下面的 JSON 格式输出，不要输出任何其他内容：

{schema_str}

要求：
- steps 包含 3 到 5 个步骤
- 每个步骤的 exercise 要具体可操作
- total_hours 等于所有步骤 hours 的总和
- 使用中文"""

    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": "你只输出合法的 JSON，不输出任何解释文字、不加 markdown 代码块。"},
            {"role": "user",   "content": prompt},
        ],
    )

    raw = response.choices[0].message.content.strip()

    # 有些模型会用 ```json ... ``` 包裹，去掉这层包装
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw_json = raw.strip()

    # 解析 JSON 字符串 → Python 字典 → Pydantic 模型（同时验证结构）
    data = json.loads(raw_json)
    plan = LearningPlan(**data)

    return plan
