"""Agent 模块的公共工具函数。"""

import json

from openai import OpenAI

from src.config import settings


def llm_json(prompt: str, schema: type) -> dict:
    """调用 LLM，要求严格按照 schema 输出 JSON，返回解析后的字典。"""
    schema_str = json.dumps(schema.model_json_schema(), ensure_ascii=False, indent=2)
    system = (
        "你只输出合法的 JSON，严格符合下面的 Schema，不输出任何解释文字，不加 markdown 代码块。\n\n"
        f"Schema：\n{schema_str}"
    )
    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
    resp   = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
    )
    raw = resp.choices[0].message.content.strip()
    # 去掉可能的 ```json ``` 包装
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())
