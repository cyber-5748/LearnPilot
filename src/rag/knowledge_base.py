# ============================================================
# 阶段10：RAG 知识库
# ============================================================
#
# 核心概念：
#
#   1. 向量（Vector）
#      把一段文字转换成一组数字（比如 [0.12, -0.34, 0.87, ...]）
#      语义相近的文字，转出来的向量在空间上也相近
#
#   2. 向量数据库（ChromaDB）
#      专门存储和搜索向量的数据库
#      给一个查询向量，它能快速找出最相似的几条记录
#
#   3. RAG 的两个阶段
#      【建库阶段】文档 → 切片 → 转向量 → 存入 ChromaDB（只做一次）
#      【查询阶段】用户问题 → 转向量 → 搜索 → 取出相关片段 → 塞进 Prompt
#
# ChromaDB 默认使用本地小模型做向量转换，第一次运行会自动下载（约 80MB）
# ============================================================

from dataclasses import dataclass
from pathlib import Path
import chromadb
from chromadb.errors import InvalidArgumentError
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction


@dataclass
class SearchResult:
    text: str          # chunk 原文
    source: str        # 来源文件名（从 metadata["source"] 取）
    score: float       # 相似度分数（1 - distance）
    metadata: dict     # 完整元数据
    doc_id: str        # 文档 ID

# 知识库存储位置（持久化到本地文件夹）
CHROMA_DIR   = "./data/chroma_db"
COLLECTION   = "learnpilot_knowledge"
KNOWLEDGE_DIR = Path("./data/knowledge")

# 延迟初始化：import 时不创建 ChromaDB 连接，首次使用时才初始化
_client = None
_ef     = None
_collection = None


def _get_collection():
    """首次调用时初始化 ChromaDB 客户端和集合，后续直接返回缓存。"""
    global _client, _ef, _collection
    if _collection is not None:
        return _collection
    try:
        Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
        _ef     = DefaultEmbeddingFunction()
        _collection = _client.get_or_create_collection(
            name=COLLECTION,
            embedding_function=_ef,
        )
    except Exception as e:
        print(f"[RAG] ChromaDB 初始化失败：{e}")
        raise
    return _collection


def get_collection():
    """公共接口：获取 ChromaDB 集合（延迟初始化）。"""
    return _get_collection()


def add_document(doc_id: str, text: str, metadata: dict | None = None) -> None:
    """
    向知识库添加一条文档。

    ChromaDB 会自动：
      1. 调用 embedding_function 把 text 转成向量
      2. 把 (id, 向量, 原文, metadata) 存入数据库
    """
    _get_collection().upsert(   # upsert = 有则更新，无则插入
        ids=[doc_id],
        documents=[text],
        metadatas=[metadata or {}],
    )


def _deduplicate(results: list[SearchResult], similarity_threshold: float = 0.7) -> list[SearchResult]:
    """
    对搜索结果去重：Jaccard 字符级相似度超过阈值时，只保留 score 更高的那条。
    输入应已按 score 降序排列。
    """
    kept: list[SearchResult] = []
    for r in results:
        r_chars = set(r.text)
        is_dup = False
        for k in kept:
            k_chars = set(k.text)
            intersection = len(r_chars & k_chars)
            union = len(r_chars | k_chars)
            if union > 0 and intersection / union >= similarity_threshold:
                is_dup = True
                break
        if not is_dup:
            kept.append(r)
    return kept


def search_detailed(query: str, n_results: int = 3, where: dict | None = None,
                    similarity_threshold: float = 0.7) -> list[SearchResult]:
    """
    检索最相关的文档片段，返回包含完整元数据的 SearchResult 列表。

    参数：
      - where: ChromaDB 过滤条件，如 {"source": "book.epub"}
    """
    count = _get_collection().count()
    if count == 0:
        return []

    try:
        # 多取一些候选，去重后再截取 n_results 条
        fetch_n = min(n_results * 3, count)
        results = _get_collection().query(
            query_texts=[query],
            n_results=fetch_n,
            include=["documents", "distances", "metadatas"],
            **({"where": where} if where else {}),
        )
    except InvalidArgumentError as e:
        if where:
            print(f"[RAG] search_by_source 过滤查询失败：{e}，降级为全库搜索")
            return search_detailed(query, n_results, where=None,
                                   similarity_threshold=similarity_threshold)
        return []

    docs = results["documents"][0] if results["documents"] else []
    dists = results["distances"][0] if results["distances"] else []
    metas = results["metadatas"][0] if results["metadatas"] else []
    ids = results["ids"][0] if results["ids"] else []

    candidates = [
        SearchResult(
            text=doc,
            source=meta.get("source", ""),
            score=round(1 - dist, 4),
            metadata=meta,
            doc_id=doc_id,
        )
        for doc, dist, meta, doc_id in zip(docs, dists, metas, ids)
    ]

    # 去重后截取 n_results 条
    deduped = _deduplicate(candidates, similarity_threshold)
    return deduped[:n_results]


def search(query: str, n_results: int = 3) -> list[str]:
    """
    根据查询语句检索最相关的文档片段。
    返回纯文本列表（向后兼容）。
    """
    return [r.text for r in search_detailed(query, n_results)]


def search_by_source(query: str, source: str, n_results: int = 5) -> list[str]:
    """根据查询语句检索指定来源（书籍文件名）的文档片段。"""
    return [r.text for r in search_detailed(query, n_results, where={"source": source})]


def load_knowledge_dir() -> int:
    """
    扫描 knowledge/ 文件夹，把所有 .md 文件按段落切片后存入知识库。
    返回成功导入的片段数量。
    """
    if not KNOWLEDGE_DIR.exists():
        print(f"知识库目录 {KNOWLEDGE_DIR} 不存在，跳过")
        return 0

    count = 0
    for md_file in KNOWLEDGE_DIR.glob("*.md"):
        text = md_file.read_text(encoding="utf-8")

        # 简单切片：按空行分段（每段作为一个独立的检索单元）
        chunks = [c.strip() for c in text.split("\n\n") if c.strip()]

        for i, chunk in enumerate(chunks):
            doc_id = f"{md_file.stem}_{i}"
            add_document(
                doc_id=doc_id,
                text=chunk,
                metadata={"source": md_file.name, "chunk": i},
            )
            count += 1

        print(f"  已导入：{md_file.name}（{len(chunks)} 个片段）")

    return count


def get_collection_size() -> int:
    """返回知识库中的文档数量。"""
    return _get_collection().count()
