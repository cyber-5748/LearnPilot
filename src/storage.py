# ============================================================
# 阶段 6：对话历史存储（JSON 文件版）
# ============================================================
#
# 知识点：
#   - 用 JSON 文件保存对话历史，不需要数据库
#   - 每个 session_id 对应一个 .json 文件
#   - json.dump()  → Python 对象 → 写入文件
#   - json.load()  → 读取文件 → Python 对象
# ============================================================

import json
import os
from pathlib import Path

# 所有对话文件存放在这个目录
HISTORY_DIR = Path("./data/chat_history")
HISTORY_DIR.mkdir(exist_ok=True)   # 目录不存在就自动创建


def load_history(session_id: str) -> list[dict]:
    """读取某个会话的历史消息，文件不存在则返回空列表。"""
    file = HISTORY_DIR / f"{session_id}.json"
    if not file.exists():
        return []
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(session_id: str, messages: list[dict]) -> None:
    """把消息列表写入对应的 JSON 文件。"""
    file = HISTORY_DIR / f"{session_id}.json"
    with open(file, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
