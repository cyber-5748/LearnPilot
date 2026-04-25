# ============================================================
# Tavily 网络搜索工具
# ============================================================
#
# Tavily 是专门为 AI Agent 设计的搜索 API：
#   - 返回结构化的搜索结果（不是原始 HTML）
#   - 自动提取正文，去掉广告和导航栏
#   - 支持设置搜索深度和结果数量
# ============================================================

from tavily import TavilyClient
from src.config import settings


def web_search(query: str, max_results: int = 3) -> list[str]:
    """
    用 Tavily 搜索网络，返回相关内容片段列表。

    没有配置 API Key 时，直接返回空列表，不报错，
    这样即使 Key 未配置，程序也能正常运行（只是没有网络搜索结果）。
    """
    if not settings.tavily_api_key:
        print("[WebSearch] 未配置 TAVILY_API_KEY，跳过网络搜索")
        return []

    try:
        client  = TavilyClient(api_key=settings.tavily_api_key)
        results = client.search(
            query=query,
            max_results=max_results,
            search_depth="basic",   # basic（快）或 advanced（慢但更准）
        )

        # 提取每条结果的 content 字段（Tavily 已经帮我们提取好正文了）
        contents = []
        for r in results.get("results", []):
            title   = r.get("title", "")
            content = r.get("content", "")
            url     = r.get("url", "")
            contents.append(f"【{title}】\n{content}\n来源：{url}")

        print(f"[WebSearch] 搜索「{query}」，得到 {len(contents)} 条结果")
        return contents

    except Exception as e:
        print(f"[WebSearch] 搜索失败：{e}")
        return []
