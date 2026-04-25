"""
RAG 知识库：基于 ChromaDB 的向量存储和检索。

ChromaDB 默认使用本地小模型做向量转换，首次运行会自动下载（约 80MB）。
"""

from pathlib import Path
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

# 知识库存储位置（持久化到本地文件夹）
CHROMA_DIR   = "./chroma_db"
COLLECTION   = "learnpilot_knowledge"
KNOWLEDGE_DIR = Path("./knowledge")

# 初始化 ChromaDB 客户端（PersistentClient 会把数据存到磁盘）
_client = chromadb.PersistentClient(path=CHROMA_DIR)
_ef     = DefaultEmbeddingFunction()

# 获取或创建集合（类似数据库里的"表"）
_collection = _client.get_or_create_collection(
    name=COLLECTION,
    embedding_function=_ef,
)


def add_document(doc_id: str, text: str, metadata: dict | None = None) -> None:
    """
    向知识库添加一条文档。

    ChromaDB 会自动：
      1. 调用 embedding_function 把 text 转成向量
      2. 把 (id, 向量, 原文, metadata) 存入数据库
    """
    _collection.upsert(   # upsert = 有则更新，无则插入
        ids=[doc_id],
        documents=[text],
        metadatas=[metadata or {}],
    )


def search(query: str, n_results: int = 3) -> list[str]:
    """
    根据查询语句检索最相关的文档片段。

    ChromaDB 会自动：
      1. 把 query 转成向量
      2. 计算与库中所有向量的相似度
      3. 返回最相近的 n_results 条
    """
    count = _collection.count()
    if count == 0:
        return []

    results = _collection.query(
        query_texts=[query],
        n_results=min(n_results, count),
    )
    # results["documents"] 是一个二维列表，第一维是查询数量（我们只有1个查询）
    return results["documents"][0]


def search_by_source(query: str, source: str, n_results: int = 5) -> list[str]:
    """根据查询语句检索指定来源（书籍文件名）的文档片段。"""
    count = _collection.count()
    if count == 0:
        return []

    try:
        results = _collection.query(
            query_texts=[query],
            n_results=min(n_results, count),
            where={"source": source},
        )
        return results["documents"][0] if results["documents"][0] else []
    except Exception:
        return search(query, n_results)


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
    return _collection.count()
