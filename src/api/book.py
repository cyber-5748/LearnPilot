"""
书籍上传与解析 API。

支持格式：txt、md、epub
流程：上传文件 → 解析提取文本和目录 → 切片存入 RAG 知识库 → 记录元数据到 SQLite

两个用途：
  1. 存入向量数据库，供对话 RAG 检索
  2. 创建学习计划时可选择书籍，计划和课件将严格参考书的知识结构
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from src.rag.parsers import parse_file, SUPPORTED_EXTENSIONS
from src.rag.knowledge_base import add_document, get_collection
from src.storage_plans import save_book, list_books, get_book, delete_book

router = APIRouter()

UPLOAD_DIR = Path("./data/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/books/upload")
async def upload_book(file: UploadFile = File(...)):
    """
    上传并解析文件，自动存入 RAG 知识库。
    支持 .txt / .md / .epub
    """
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式：{ext}（仅支持 txt / md / epub）"
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件过大，最大支持 50MB")

    # 保存到 uploads 目录（同名加序号）
    save_path = UPLOAD_DIR / filename
    counter = 1
    while save_path.exists():
        stem = Path(filename).stem
        save_path = UPLOAD_DIR / f"{stem}_{counter}{ext}"
        counter += 1
    save_path.write_bytes(content)

    # 解析文件（提取文本 + 切片 + 目录）
    try:
        parsed = parse_file(save_path)
    except Exception as e:
        save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"文件解析失败：{str(e)}")

    chunks = parsed["chunks"]
    book_title = parsed["title"]
    toc_text = parsed.get("toc_text", "")

    # 存入 RAG 知识库（每个 chunk 带 source 标记，便于按书检索）
    successful_ids = []
    try:
        for i, chunk in enumerate(chunks):
            doc_id = f"book_{save_path.stem}_{i}"
            add_document(
                doc_id=doc_id,
                text=chunk,
                metadata={
                    "source": save_path.name,
                    "type": "book",
                    "chunk_index": i,
                },
            )
            successful_ids.append(doc_id)
    except Exception:
        if successful_ids:
            try:
                get_collection().delete(ids=successful_ids)
            except Exception:
                pass
        save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="知识库写入失败，已回滚")

    # 记录到 SQLite（含目录文本）
    book_id = save_book(
        title=book_title,
        filename=save_path.name,
        file_type=ext.lstrip("."),
        file_size=len(content),
        chunk_count=len(chunks),
        toc_text=toc_text,
    )

    return {
        "book_id": book_id,
        "title": book_title,
        "filename": save_path.name,
        "file_type": ext.lstrip("."),
        "file_size": len(content),
        "chunk_count": len(chunks),
        "has_toc": bool(toc_text),
    }


@router.get("/books")
def get_books():
    """获取所有已上传的书籍列表。"""
    return list_books()


@router.get("/books/{book_id}")
def get_book_detail(book_id: int):
    """获取单本书籍的详细信息（含目录）。"""
    data = get_book(book_id)
    if not data:
        raise HTTPException(status_code=404, detail="书籍不存在")
    return data


@router.delete("/books/{book_id}")
def delete_book_api(book_id: int):
    """删除书籍：同时清理文件、RAG 向量和数据库记录。"""
    data = get_book(book_id)
    if not data:
        raise HTTPException(status_code=404, detail="书籍不存在")

    # 删除上传的文件
    file_path = UPLOAD_DIR / data["filename"]
    if file_path.exists():
        file_path.unlink()

    # 删除 RAG 知识库中该书的所有 chunks
    warning = ""
    try:
        existing = get_collection().get(where={"source": data["filename"]})
        if existing and existing["ids"]:
            get_collection().delete(ids=existing["ids"])
    except Exception as e:
        print(f"[RAG] 删除书籍向量失败：{e}")
        warning = "RAG 知识库清理未完成，部分向量可能残留"

    delete_book(book_id)
    return {"ok": True, "warning": warning}


def clean_orphan_vectors() -> dict:
    """
    清理 ChromaDB 中的孤儿书籍向量。
    扫描 type="book" 的所有 chunks，删除 books 表中已不存在的条目。
    """
    try:
        col = get_collection()
        book_entries = col.get(where={"type": "book"})
    except Exception as e:
        print(f"[RAG] 孤儿清理查询失败：{e}")
        return {"deleted": 0, "error": str(e)}

    if not book_entries or not book_entries["ids"]:
        return {"deleted": 0}

    # 获取 books 表中所有有效的 filename
    valid_filenames = {b["filename"] for b in list_books()}

    # 找出孤儿 ID
    orphan_ids = []
    for doc_id, meta in zip(book_entries["ids"], book_entries["metadatas"]):
        if meta.get("source") not in valid_filenames:
            orphan_ids.append(doc_id)

    if orphan_ids:
        col.delete(ids=orphan_ids)
        print(f"[RAG] 已清理 {len(orphan_ids)} 条孤儿向量")

    return {"deleted": len(orphan_ids)}


@router.post("/books/clean-orphans")
def clean_orphans_api():
    """手动触发清理 ChromaDB 中的孤儿书籍向量。"""
    return clean_orphan_vectors()
