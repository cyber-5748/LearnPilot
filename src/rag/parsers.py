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


# ── 切片 ─────────────────────────────────────────────────────
#
# 切片策略：
#   - 以段落（双换行）为基本单元拼接，直到接近 max_len
#   - 切片边界对齐到最近的句子结束符（。！？.!?\n），避免句中截断
#   - 相邻 chunk 的重叠取前一个 chunk 末尾的 N 个完整句子，而非硬截字符
#   - 同时返回每个 chunk 在原文中的字符起止位置（char_start/char_end）

_SENTENCE_ENDS = re.compile(r"[。！？.!?\n]")


def _find_sentence_boundary(text: str, max_pos: int) -> int:
    """从 max_pos 向左搜索最近的句子结束符，返回切分位置（含结束符）。"""
    for i in range(min(max_pos, len(text)) - 1, max(max_pos - 200, 0) - 1, -1):
        if _SENTENCE_ENDS.match(text[i]):
            return i + 1
    return max_pos


def _get_tail_sentences(text: str, count: int = 2) -> str:
    """取 text 末尾的 count 个完整句子作为重叠部分。"""
    parts = _SENTENCE_ENDS.split(text.rstrip())
    # 过滤空串
    parts = [p for p in parts if p.strip()]
    if not parts:
        return ""
    tail = parts[-count:] if len(parts) >= count else parts
    return "".join(tail).strip()


def _split_chunks(text: str, max_len: int = 800, overlap: int = 100,
                  sentence_overlap_count: int = 2) -> list[str]:
    """
    按段落切片，保证每个 chunk 不超过 max_len 字符。
    切片边界对齐到句子末尾，重叠取末尾完整句子。
    overlap 参数保留用于向后兼容，实际由 sentence_overlap_count 控制。
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 > max_len and current:
            # 在 max_len 附近找句子边界
            if len(current) > max_len:
                boundary = _find_sentence_boundary(current, max_len)
                chunks.append(current[:boundary].strip())
                remainder = current[boundary:].strip()
            else:
                chunks.append(current.strip())
                remainder = ""

            # 用末尾完整句子作为重叠
            prev_text = chunks[-1]
            overlap_text = _get_tail_sentences(prev_text, sentence_overlap_count)
            if remainder:
                current = overlap_text + "\n\n" + remainder + "\n\n" + para if overlap_text else remainder + "\n\n" + para
            else:
                current = overlap_text + "\n\n" + para if overlap_text else para
        else:
            current = current + "\n\n" + para if current else para

    if current.strip():
        chunks.append(current.strip())

    return chunks


def _split_chunks_with_meta(text: str, max_len: int = 800,
                            sentence_overlap_count: int = 2) -> tuple[list[str], list[dict]]:
    """
    切片并记录每个 chunk 在原文中的字符位置。
    返回 (chunks, chunks_meta)，chunks_meta 中每项为 {chunk_index, char_start, char_end}。
    """
    chunks = _split_chunks(text, max_len=max_len, sentence_overlap_count=sentence_overlap_count)
    meta = []
    search_start = 0
    for i, chunk in enumerate(chunks):
        # 取 chunk 去掉重叠后的核心部分来定位
        # 用前 80 字符作为定位锚点
        anchor = chunk[:80]
        pos = text.find(anchor, search_start)
        if pos == -1:
            pos = search_start
        char_start = pos
        char_end = min(pos + len(chunk), len(text))
        meta.append({"chunk_index": i, "char_start": char_start, "char_end": char_end})
        search_start = pos + 1
    return chunks, meta


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


def _extract_toc_positions(text: str, toc: list[dict]) -> list[dict]:
    """
    为每个 TOC 条目定位它在原文中的字符位置。
    返回 [{level, title, char_pos}]，char_pos 是标题行在 text 中的起始位置。
    """
    result = []
    search_start = 0
    for item in toc:
        pos = text.find(item["title"], search_start)
        if pos != -1:
            result.append({**item, "char_pos": pos})
            search_start = pos + 1
        else:
            # 回退到全文搜索
            pos = text.find(item["title"])
            result.append({**item, "char_pos": pos if pos != -1 else -1})
    return [r for r in result if r["char_pos"] != -1]


def _assign_chapter_to_meta(chunks_meta: list[dict], toc_positions: list[dict]) -> None:
    """根据 TOC 位置信息，为每个 chunk_meta 添加 chapter_title 字段。"""
    # 只取顶级章节（level 1）作为章节划分
    chapters = [t for t in toc_positions if t["level"] <= 2]
    for meta in chunks_meta:
        chapter_title = ""
        for ch in reversed(chapters):
            if meta["char_start"] >= ch["char_pos"]:
                chapter_title = ch["title"]
                break
        meta["chapter_title"] = chapter_title


def _build_chapter_chunks(chunks: list[str], chunks_meta: list[dict]) -> list[dict]:
    """从 chunks 和 chunks_meta 构建 chapter_chunks 列表。"""
    chapter_map: dict[str, list[str]] = {}
    order = []
    for chunk, meta in zip(chunks, chunks_meta):
        title = meta.get("chapter_title", "")
        if title not in chapter_map:
            chapter_map[title] = []
            order.append(title)
        chapter_map[title].append(chunk)
    return [{"chapter_title": t, "chunks": chapter_map[t]} for t in order]


# ── TXT 解析 ─────────────────────────────────────────────────

def parse_txt(file_path: str | Path, encoding: str = "utf-8") -> dict:
    """解析纯文本文件，返回 {title, content, chunks, chunks_meta, chapter_chunks, toc, toc_text}。"""
    path = Path(file_path)
    text = path.read_text(encoding=encoding)
    toc = _extract_toc_from_text(text)
    chunks, chunks_meta = _split_chunks_with_meta(text)
    toc_positions = _extract_toc_positions(text, toc)
    _assign_chapter_to_meta(chunks_meta, toc_positions)
    return {
        "title": path.stem,
        "content": text,
        "chunks": chunks,
        "chunks_meta": chunks_meta,
        "chapter_chunks": _build_chapter_chunks(chunks, chunks_meta),
        "toc": toc,
        "toc_text": _toc_to_text(toc),
    }


# ── Markdown 解析 ────────────────────────────────────────────

def parse_md(file_path: str | Path, encoding: str = "utf-8") -> dict:
    """解析 Markdown 文件，返回 {title, content, chunks, chunks_meta, chapter_chunks, toc, toc_text}。"""
    path = Path(file_path)
    text = path.read_text(encoding=encoding)

    title = path.stem
    first_heading = re.search(r"^#\s+(.+)", text, re.MULTILINE)
    if first_heading:
        title = first_heading.group(1).strip()

    toc = _extract_toc_from_text(text)
    chunks, chunks_meta = _split_chunks_with_meta(text)
    toc_positions = _extract_toc_positions(text, toc)
    _assign_chapter_to_meta(chunks_meta, toc_positions)
    return {
        "title": title,
        "content": text,
        "chunks": chunks,
        "chunks_meta": chunks_meta,
        "chapter_chunks": _build_chapter_chunks(chunks, chunks_meta),
        "toc": toc,
        "toc_text": _toc_to_text(toc),
    }


# ── EPUB 解析 ────────────────────────────────────────────────

def _build_epub_toc_href_map(book_toc) -> dict[str, str]:
    """从 EPUB toc 构建 href → chapter_title 的映射。"""
    href_map = {}

    def _walk(items):
        for item in items:
            if isinstance(item, tuple):
                section, children = item
                # href 可能含锚点 "ch01.xhtml#sec1"，取文件名部分
                href = section.href.split("#")[0] if hasattr(section, "href") else ""
                if href:
                    href_map.setdefault(href, section.title)
                _walk(children)
            else:
                href = item.href.split("#")[0] if hasattr(item, "href") else ""
                if href:
                    href_map.setdefault(href, item.title)

    _walk(book_toc)
    return href_map


def parse_epub(file_path: str | Path) -> dict:
    """解析 EPUB 电子书，逐章节提取文本并切片，保留章节归属信息。"""
    try:
        from bs4 import BeautifulSoup
        from ebooklib import epub, ITEM_DOCUMENT
    except ImportError:
        raise ImportError("epub 解析需要安装 ebooklib 和 beautifulsoup4，请运行 pip install ebooklib beautifulsoup4")

    path = Path(file_path)
    book = epub.read_epub(str(path))

    title = path.stem
    dc_title = book.get_metadata("DC", "title")
    if dc_title:
        title = dc_title[0][0]

    # 从 EPUB toc 元数据提取目录
    toc = _extract_toc_from_epub(book)
    href_map = _build_epub_toc_href_map(book.toc)

    # 逐章节处理：提取文本、切片、记录章节归属
    all_text_parts = []
    chapter_chunks_list = []
    all_chunks = []
    all_chunks_meta = []
    content_offset = 0  # 在拼接后的 content 中的偏移

    for item in book.get_items_of_type(ITEM_DOCUMENT):
        html = item.get_content().decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n\n")
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if not text:
            continue

        # 确定章节标题：优先从 toc href 映射，其次从 HTML 标题标签
        item_href = item.get_name().split("/")[-1] if hasattr(item, "get_name") else ""
        chapter_title = href_map.get(item_href, "")
        if not chapter_title:
            heading = soup.find(re.compile(r"^h[1-3]$"))
            if heading:
                chapter_title = heading.get_text(strip=True)

        # 对该章节单独切片
        ch_chunks = _split_chunks(text)
        ch_meta = []
        search_start = 0
        for i, chunk in enumerate(ch_chunks):
            anchor = chunk[:80]
            pos = text.find(anchor, search_start)
            if pos == -1:
                pos = search_start
            global_start = content_offset + pos
            global_end = min(content_offset + pos + len(chunk), content_offset + len(text))
            ch_meta.append({
                "chunk_index": len(all_chunks) + i,
                "char_start": global_start,
                "char_end": global_end,
                "chapter_title": chapter_title,
            })
            search_start = pos + 1

        all_chunks.extend(ch_chunks)
        all_chunks_meta.extend(ch_meta)
        if ch_chunks:
            chapter_chunks_list.append({"chapter_title": chapter_title, "chunks": ch_chunks})

        all_text_parts.append(text)
        content_offset += len(text) + 2  # +2 for "\n\n" separator

    content = "\n\n".join(all_text_parts)
    if not toc:
        toc = _extract_toc_from_text(content)

    return {
        "title": title,
        "content": content,
        "chunks": all_chunks,
        "chunks_meta": all_chunks_meta,
        "chapter_chunks": chapter_chunks_list,
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
