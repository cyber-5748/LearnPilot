"""
学习计划 + 会话名称的 SQLite 持久化。
"""

import sqlite3
import json
from datetime import datetime

DB_PATH = "./memory.db"


def _conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_tables():
    """建表（如果不存在）。程序启动时调用一次。"""
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT    NOT NULL,
                user_input TEXT    NOT NULL,
                plan_json  TEXT    NOT NULL,
                created_at TEXT    NOT NULL,
                pinned     INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_names (
                session_id TEXT PRIMARY KEY,
                name       TEXT NOT NULL,
                pinned     INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS syllabi (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id         INTEGER NOT NULL UNIQUE,
                syllabus_json   TEXT    NOT NULL,
                created_at      TEXT    NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS lesson_contents (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id         INTEGER NOT NULL,
                lesson_index    INTEGER NOT NULL,
                content_json    TEXT    NOT NULL,
                created_at      TEXT    NOT NULL,
                UNIQUE(plan_id, lesson_index)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS homeworks (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id         INTEGER NOT NULL,
                lesson_index    INTEGER NOT NULL,
                homework_json   TEXT    NOT NULL,
                created_at      TEXT    NOT NULL,
                UNIQUE(plan_id, lesson_index)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id         INTEGER NOT NULL,
                lesson_index    INTEGER NOT NULL,
                answers_json    TEXT    NOT NULL,
                result_json     TEXT    NOT NULL,
                score           INTEGER NOT NULL,
                max_score       INTEGER NOT NULL,
                submitted_at    TEXT    NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id         INTEGER NOT NULL UNIQUE,
                report_json     TEXT    NOT NULL,
                created_at      TEXT    NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                title           TEXT    NOT NULL,
                filename        TEXT    NOT NULL,
                file_type       TEXT    NOT NULL,
                file_size       INTEGER NOT NULL,
                chunk_count     INTEGER NOT NULL DEFAULT 0,
                toc_text        TEXT    NOT NULL DEFAULT '',
                created_at      TEXT    NOT NULL
            )
        """)
        # 给旧版表补上新增列（已有则跳过）
        plan_cols = [r[1] for r in conn.execute("PRAGMA table_info(plans)").fetchall()]
        if "pinned" not in plan_cols:
            conn.execute("ALTER TABLE plans ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0")
        if "book_id" not in plan_cols:
            conn.execute("ALTER TABLE plans ADD COLUMN book_id INTEGER")

        book_cols = [r[1] for r in conn.execute("PRAGMA table_info(books)").fetchall()]
        if book_cols and "toc_text" not in book_cols:
            conn.execute("ALTER TABLE books ADD COLUMN toc_text TEXT NOT NULL DEFAULT ''")
        conn.commit()


# ── 学习计划 ──────────────────────────────────────────────────

def save_plan(title: str, user_input: str, plan_dict: dict, book_id: int | None = None) -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO plans (title, user_input, plan_json, created_at, book_id) VALUES (?, ?, ?, ?, ?)",
            (title, user_input, json.dumps(plan_dict, ensure_ascii=False),
             datetime.now().strftime("%Y-%m-%d %H:%M"), book_id)
        )
        conn.commit()
        return cur.lastrowid


def list_plans() -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT id, title, user_input, created_at, pinned FROM plans ORDER BY pinned DESC, id DESC"
        ).fetchall()
    return [{"id": r[0], "title": r[1], "user_input": r[2], "created_at": r[3], "pinned": bool(r[4])} for r in rows]


def get_plan(plan_id: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT id, title, user_input, plan_json, created_at, book_id FROM plans WHERE id = ?",
            (plan_id,)
        ).fetchone()
    if not row:
        return None
    return {"id": row[0], "title": row[1], "user_input": row[2], "plan": json.loads(row[3]),
            "created_at": row[4], "book_id": row[5]}


def rename_plan(plan_id: int, new_title: str) -> bool:
    with _conn() as conn:
        cur = conn.execute("UPDATE plans SET title = ? WHERE id = ?", (new_title, plan_id))
        conn.commit()
    return cur.rowcount > 0


def delete_plan(plan_id: int) -> bool:
    with _conn() as conn:
        cur = conn.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
        conn.commit()
    return cur.rowcount > 0


def pin_plan(plan_id: int, pinned: bool) -> bool:
    with _conn() as conn:
        cur = conn.execute("UPDATE plans SET pinned = ? WHERE id = ?", (1 if pinned else 0, plan_id))
        conn.commit()
    return cur.rowcount > 0


# ── 会话名称 ──────────────────────────────────────────────────

def set_session_name(session_id: str, name: str):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO session_names (session_id, name) VALUES (?, ?) "
            "ON CONFLICT(session_id) DO UPDATE SET name = excluded.name",
            (session_id, name)
        )
        conn.commit()


def delete_session_name(session_id: str):
    with _conn() as conn:
        conn.execute("DELETE FROM session_names WHERE session_id = ?", (session_id,))
        conn.commit()


def get_session_names() -> dict[str, dict]:
    """返回 {session_id: {name, pinned}} 的字典，供 list_sessions 合并使用。"""
    with _conn() as conn:
        rows = conn.execute("SELECT session_id, name, pinned FROM session_names").fetchall()
    return {r[0]: {"name": r[1], "pinned": bool(r[2])} for r in rows}


def pin_session(session_id: str, pinned: bool):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO session_names (session_id, name, pinned) VALUES (?, '', ?) "
            "ON CONFLICT(session_id) DO UPDATE SET pinned = excluded.pinned",
            (session_id, 1 if pinned else 0)
        )
        conn.commit()


# ── 章节拆解 ──────────────────────────────────────────────────

def save_syllabus(plan_id: int, syllabus_dict: dict) -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO syllabi (plan_id, syllabus_json, created_at) VALUES (?, ?, ?) "
            "ON CONFLICT(plan_id) DO UPDATE SET syllabus_json = excluded.syllabus_json, created_at = excluded.created_at",
            (plan_id, json.dumps(syllabus_dict, ensure_ascii=False),
             datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()
        return cur.lastrowid


def get_syllabus(plan_id: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT id, plan_id, syllabus_json, created_at FROM syllabi WHERE plan_id = ?",
            (plan_id,)
        ).fetchone()
    if not row:
        return None
    return {"id": row[0], "plan_id": row[1], "syllabus": json.loads(row[2]), "created_at": row[3]}


def delete_syllabus(plan_id: int) -> bool:
    with _conn() as conn:
        cur = conn.execute("DELETE FROM syllabi WHERE plan_id = ?", (plan_id,))
        conn.commit()
    return cur.rowcount > 0


# ── 课件内容 ──────────────────────────────────────────────────

def save_lesson_content(plan_id: int, lesson_index: int, content_dict: dict) -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO lesson_contents (plan_id, lesson_index, content_json, created_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(plan_id, lesson_index) DO UPDATE SET content_json = excluded.content_json, created_at = excluded.created_at",
            (plan_id, lesson_index, json.dumps(content_dict, ensure_ascii=False),
             datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()
        return cur.lastrowid


def get_lesson_content(plan_id: int, lesson_index: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT id, content_json, created_at FROM lesson_contents WHERE plan_id = ? AND lesson_index = ?",
            (plan_id, lesson_index)
        ).fetchone()
    if not row:
        return None
    return {"id": row[0], "content": json.loads(row[1]), "created_at": row[2]}


# ── 作业 ─────────────────────────────────────────────────────

def save_homework(plan_id: int, lesson_index: int, homework_dict: dict) -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO homeworks (plan_id, lesson_index, homework_json, created_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(plan_id, lesson_index) DO UPDATE SET homework_json = excluded.homework_json, created_at = excluded.created_at",
            (plan_id, lesson_index, json.dumps(homework_dict, ensure_ascii=False),
             datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()
        return cur.lastrowid


def get_homework(plan_id: int, lesson_index: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT id, homework_json, created_at FROM homeworks WHERE plan_id = ? AND lesson_index = ?",
            (plan_id, lesson_index)
        ).fetchone()
    if not row:
        return None
    return {"id": row[0], "homework": json.loads(row[1]), "created_at": row[2]}


def save_submission(plan_id: int, lesson_index: int, answers: list, result_dict: dict, score: int, max_score: int) -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO submissions (plan_id, lesson_index, answers_json, result_json, score, max_score, submitted_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (plan_id, lesson_index,
             json.dumps(answers, ensure_ascii=False),
             json.dumps(result_dict, ensure_ascii=False),
             score, max_score,
             datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()
        return cur.lastrowid


def get_plan_progress(plan_id: int) -> dict:
    """
    返回某个计划下所有课时的进度信息。
    {lesson_index: {has_content, has_homework, best_score, max_score, passed}}
    """
    with _conn() as conn:
        # 已生成课件的课时
        content_rows = conn.execute(
            "SELECT lesson_index FROM lesson_contents WHERE plan_id = ?", (plan_id,)
        ).fetchall()
        content_set = {r[0] for r in content_rows}

        # 已生成作业的课时
        hw_rows = conn.execute(
            "SELECT lesson_index FROM homeworks WHERE plan_id = ?", (plan_id,)
        ).fetchall()
        hw_set = {r[0] for r in hw_rows}

        # 每课时的最佳提交（取最高分）
        sub_rows = conn.execute(
            "SELECT lesson_index, MAX(score) as best, max_score "
            "FROM submissions WHERE plan_id = ? GROUP BY lesson_index",
            (plan_id,)
        ).fetchall()
        sub_map = {r[0]: {"best_score": r[1], "max_score": r[2]} for r in sub_rows}

    all_indices = content_set | hw_set | set(sub_map.keys())
    progress = {}
    for idx in all_indices:
        sub = sub_map.get(idx)
        best = sub["best_score"] if sub else None
        mx = sub["max_score"] if sub else None
        passed = (best >= mx * 0.8) if best is not None and mx else False
        progress[idx] = {
            "has_content": idx in content_set,
            "has_homework": idx in hw_set,
            "best_score": best,
            "max_score": mx,
            "passed": passed,
        }
    return progress


def get_all_submissions(plan_id: int) -> list[dict]:
    """获取某计划下所有课时的最近一次提交结果（用于学习报告）。"""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT s.lesson_index, s.score, s.max_score, s.result_json, s.submitted_at "
            "FROM submissions s "
            "INNER JOIN ("
            "  SELECT lesson_index, MAX(id) as max_id FROM submissions WHERE plan_id = ? GROUP BY lesson_index"
            ") latest ON s.id = latest.max_id "
            "ORDER BY s.lesson_index",
            (plan_id,)
        ).fetchall()
    return [
        {
            "lesson_index": r[0], "score": r[1], "max_score": r[2],
            "result": json.loads(r[3]), "submitted_at": r[4],
        }
        for r in rows
    ]


def get_latest_submission(plan_id: int, lesson_index: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT id, answers_json, result_json, score, max_score, submitted_at "
            "FROM submissions WHERE plan_id = ? AND lesson_index = ? ORDER BY id DESC LIMIT 1",
            (plan_id, lesson_index)
        ).fetchone()
    if not row:
        return None
    return {
        "id": row[0], "answers": json.loads(row[1]), "result": json.loads(row[2]),
        "score": row[3], "max_score": row[4], "submitted_at": row[5],
    }


# ── 学习报告 ─────────────────────────────────────────────────

def save_report(plan_id: int, report_dict: dict) -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO reports (plan_id, report_json, created_at) VALUES (?, ?, ?) "
            "ON CONFLICT(plan_id) DO UPDATE SET report_json = excluded.report_json, created_at = excluded.created_at",
            (plan_id, json.dumps(report_dict, ensure_ascii=False),
             datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()
        return cur.lastrowid


def get_report(plan_id: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT id, report_json, created_at FROM reports WHERE plan_id = ?",
            (plan_id,)
        ).fetchone()
    if not row:
        return None
    return {"id": row[0], "report": json.loads(row[1]), "created_at": row[2]}


# ── 书籍资料 ────────────────────────────────────────────────

def save_book(title: str, filename: str, file_type: str, file_size: int, chunk_count: int, toc_text: str = "") -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO books (title, filename, file_type, file_size, chunk_count, toc_text, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, filename, file_type, file_size, chunk_count, toc_text,
             datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()
        return cur.lastrowid


def list_books() -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT id, title, filename, file_type, file_size, chunk_count, created_at "
            "FROM books ORDER BY id DESC"
        ).fetchall()
    return [
        {"id": r[0], "title": r[1], "filename": r[2], "file_type": r[3],
         "file_size": r[4], "chunk_count": r[5], "created_at": r[6]}
        for r in rows
    ]


def get_book(book_id: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT id, title, filename, file_type, file_size, chunk_count, toc_text, created_at "
            "FROM books WHERE id = ?", (book_id,)
        ).fetchone()
    if not row:
        return None
    return {"id": row[0], "title": row[1], "filename": row[2], "file_type": row[3],
            "file_size": row[4], "chunk_count": row[5], "toc_text": row[6], "created_at": row[7]}


def delete_book(book_id: int) -> bool:
    with _conn() as conn:
        cur = conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
    return cur.rowcount > 0
