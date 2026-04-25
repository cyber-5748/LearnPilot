"""
文件解析器：支持 txt、md、epub 三种格式。

解析流程：
  1. 根据文件后缀选择解析器
  2. 提取纯文本内容
  3. 按段落切分为 chunks（每个 chunk 是一个独立检索单元）
  4. 提取目录结构（TOC），供学习计划参考
"""

import re
from pathlib import Path

from bs4 import BeautifulSoup
from ebooklib import epub, ITEM_DOCUMENT


# ── 切片 ─────────────────────────────────────────────────────

def _split_chunks(text: str, max_len: int = 800, overlap: int = 100) -> list[str]:
    """
    按段落切片，保证每个 chunk 不超过 max_len 字符。
    相邻 chunk 之间有 overlap 字符的重叠，避免语义断裂。
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 > max_len and current:
            chunks.append(current.strip())
            current = current[-overlap:] + "\n\n" + para if overlap else para
        else:
            current = current + "\n\n" + para if current else para

    if current.strip():
        chunks.append(current.strip())

    return chunks


# ── 目录提取 ─────────────────────────────────────────────────

def _extract_toc_from_text(text: str) -> list[dict]:
    """
    从纯文本/Markdown 中提取标题行作为目录。
    识别 Markdown 标题（# ## ###）和常见的中文章节模式。
    返回 [{level, title}] 列表。
    """
    toc = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Markdown 标题
        md_match = re.match(r"^(#{1,4})\s+(.+)", line)
        if md_match:
            toc.append({"level": len(md_match.group(1)), "title": md_match.group(2).strip()})
            continue
        # 中文章节模式：第X章、第X节、第X部分
        cn_match = re.match(r"^第[一二三四五六七八九十\d]+[章节部分篇]\s*[:：]?\s*(.+)", line)
        if cn_match:
            if "章" in line or "部分" in line or "篇" in line:
                toc.append({"level": 1, "title": line})
            else:
                toc.append({"level": 2, "title": line})
            continue
        # 数字编号模式：1. xxx、1.1 xxx
        num_match = re.match(r"^(\d+(?:\.\d+)*)[.\s、]\s*(.+)", line)
        if num_match:
            depth = num_match.group(1).count(".") + 1
            if depth <= 3 and len(line) < 80:
                toc.append({"level": depth, "title": line})
    return toc


def _extract_toc_from_epub(book) -> list[dict]:
    """从 EPUB 的 toc 元数据中提取目录结构。"""
    toc = []

    def _walk_toc(items, level=1):
        for item in items:
            if isinstance(item, tuple):
                # (Section, [children])
                section, children = item
                toc.append({"level": level, "title": section.title})
                _walk_toc(children, level + 1)
            else:
                toc.append({"level": level, "title": item.title})

    _walk_toc(book.toc)
    return toc


def _toc_to_text(toc: list[dict]) -> str:
    """将 TOC 列表转为可读的缩进文本，用于注入 prompt。"""
    lines = []
    for item in toc:
        indent = "  " * (item["level"] - 1)
        lines.append(f"{indent}- {item['title']}")
    return "\n".join(lines)


# ── TXT 解析 ─────────────────────────────────────────────────

def parse_txt(file_path: str | Path, encoding: str = "utf-8") -> dict:
    """解析纯文本文件，返回 {title, content, chunks, toc, toc_text}。"""
    path = Path(file_path)
    text = path.read_text(encoding=encoding)
    toc = _extract_toc_from_text(text)
    return {
        "title": path.stem,
        "content": text,
        "chunks": _split_chunks(text),
        "toc": toc,
        "toc_text": _toc_to_text(toc),
    }


# ── Markdown 解析 ────────────────────────────────────────────

def parse_md(file_path: str | Path, encoding: str = "utf-8") -> dict:
    """解析 Markdown 文件，返回 {title, content, chunks, toc, toc_text}。"""
    path = Path(file_path)
    text = path.read_text(encoding=encoding)

    title = path.stem
    first_heading = re.search(r"^#\s+(.+)", text, re.MULTILINE)
    if first_heading:
        title = first_heading.group(1).strip()

    toc = _extract_toc_from_text(text)
    return {
        "title": title,
        "content": text,
        "chunks": _split_chunks(text),
        "toc": toc,
        "toc_text": _toc_to_text(toc),
    }


# ── EPUB 解析 ────────────────────────────────────────────────

def parse_epub(file_path: str | Path) -> dict:
    """解析 EPUB 电子书，提取所有章节的纯文本。"""
    path = Path(file_path)
    book = epub.read_epub(str(path))

    title = path.stem
    dc_title = book.get_metadata("DC", "title")
    if dc_title:
        title = dc_title[0][0]

    # 从 EPUB toc 元数据提取目录
    toc = _extract_toc_from_epub(book)
    # 如果 EPUB 没有 toc 元数据，回退到正文标题提取
    all_text = []
    for item in book.get_items_of_type(ITEM_DOCUMENT):
        html = item.get_content().decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n\n")
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if text:
            all_text.append(text)

    content = "\n\n".join(all_text)
    if not toc:
        toc = _extract_toc_from_text(content)

    return {
        "title": title,
        "content": content,
        "chunks": _split_chunks(content),
        "toc": toc,
        "toc_text": _toc_to_text(toc),
    }


# ── 统一入口 ─────────────────────────────────────────────────

SUPPORTED_EXTENSIONS = {".txt", ".md", ".epub"}

def parse_file(file_path: str | Path) -> dict:
    """
    根据文件后缀自动选择解析器。
    返回 {title, content, chunks, toc, toc_text}。
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".txt":
        return parse_txt(path)
    elif ext == ".md":
        return parse_md(path)
    elif ext == ".epub":
        return parse_epub(path)
    else:
        raise ValueError(f"不支持的文件格式：{ext}（支持 txt/md/epub）")
