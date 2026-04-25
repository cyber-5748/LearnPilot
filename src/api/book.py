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
from src.rag.knowledge_base import add_document, _collection
from src.storage_plans import save_book, list_books, get_book, delete_book

router = APIRouter()

UPLOAD_DIR = Path("./uploads")
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
    try:
        existing = _collection.get(where={"source": data["filename"]})
        if existing and existing["ids"]:
            _collection.delete(ids=existing["ids"])
    except Exception:
        pass

    delete_book(book_id)
    return {"ok": True}
