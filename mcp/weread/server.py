"""MCP Server: 微信读书 (WeRead) API 桥接层。

将微信读书 Agent API Gateway 的能力暴露为标准 MCP 工具，
供 AI 客户端（如 Codex）直接调用。

使用方式：
    export WEREAD_API_KEY=wrk-xxxx
    python server.py
    # 或指定 .env 文件路径
    WEREAD_API_KEY=wrk-xxxx python server.py
"""

import os
import sys
from typing import Any

from mcp.server import FastMCP
from dotenv import load_dotenv

from weread_client import WeReadClient

# ---- MCP 服务初始化 ----

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

api_key = os.environ.get("WEREAD_API_KEY")
if not api_key:
    print("错误: 未设置 WEREAD_API_KEY 环境变量。", file=sys.stderr)
    print("请通过 export WEREAD_API_KEY=wrk-xxxx 设置。", file=sys.stderr)
    sys.exit(1)

client = WeReadClient(api_key=api_key)

mcp = FastMCP(
    "WeRead",
    instructions="微信读书 (WeRead) API 桥接 — 搜索书籍、管理书架、查看笔记划线、浏览书评、阅读统计、发现推荐好书",
)


# ---- 工具函数 ----

def _format_timestamp(ts: int | None) -> str | None:
    """将 Unix 时间戳（秒）转为 YYYY-MM-DD 格式。"""
    if ts is None or ts == 0:
        return None
    from datetime import datetime, timezone

    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


# ---- 工具注册 ----

@mcp.tool(
    description="通用: 调用微信读书 Agent API Gateway 的任意接口。"
    "适用于工具列表未覆盖的接口。参数必须平铺在顶层。"
)
def weread_gateway_call(
    api_name: str,
    kwargs_json: str | None = None,
) -> str:
    """通用网关调用。

    Args:
        api_name: 接口名称，如 /store/search, /readdata/detail。
        kwargs_json: 业务参数字符串（JSON 对象），平铺传入。
    """
    import json

    kwargs: dict[str, Any] = {}
    if kwargs_json:
        kwargs = json.loads(kwargs_json)
    result = client.call(api_name, **kwargs)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(description="搜索: 在微信读书书城中搜索书籍、作者、文章等。")
def weread_search(
    keyword: str,
    scope: int | None = None,
    max_idx: int | None = None,
    count: int | None = None,
) -> str:
    """搜索微信读书内容。

    Args:
        keyword: 搜索关键词。
        scope: 搜索范围。0=全部, 10=电子书, 16=网文, 14=听书, 6=作者, 12=全文, 13=书单, 2=公众号, 4=文章。
        max_idx: 翻页偏移。
        count: 每页数量。
    """
    import json

    result = client.search(
        keyword=keyword,
        scope=scope,
        max_idx=max_idx,
        count=count,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(description="书架: 获取当前用户的微信读书书架列表。")
def weread_get_shelf() -> str:
    """获取用户书架，包含电子书、专辑/有声书和文章收藏入口。"""
    import json

    result = client.get_shelf()
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(description="书籍信息: 获取书籍基本信息。")
def weread_get_book_info(book_id: str) -> str:
    """获取书籍的详细信息。

    Args:
        book_id: 书籍唯一标识。
    """
    import json

    result = client.get_book_info(book_id=book_id)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(description="章节: 获取书籍的章节目录。")
def weread_get_chapters(book_id: str) -> str:
    """获取书籍的章节目录。

    Args:
        book_id: 书籍唯一标识。
    """
    import json

    result = client.get_chapters(book_id=book_id)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(description="阅读进度: 获取某本书的阅读进度。")
def weread_get_reading_progress(book_id: str) -> str:
    """获取某本书的阅读进度和累计时长。

    Args:
        book_id: 书籍唯一标识。
    """
    import json

    result = client.get_reading_progress(book_id=book_id)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(
    description="阅读统计: 获取个人阅读时长、天数、排行和偏好分析。"
    "mode 支持: weekly(本周), monthly(本月), annually(本年), overall(总计)。"
)
def weread_get_reading_stats(
    mode: str = "monthly",
    base_time: int | None = None,
) -> str:
    """获取阅读统计详情。

    Args:
        mode: 统计维度。weekly=本周, monthly=本月, annually=本年, overall=总计。
        base_time: 基准时间戳（Unix 秒）。0=当前周期。传历史时间戳可查看该周期数据。
    """
    import json

    result = client.get_reading_stats(mode=mode, base_time=base_time)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(description="笔记概览: 列出所有有笔记/划线的书籍。")
def weread_list_notebooks(
    count: int | None = None,
    last_sort: int | None = None,
) -> str:
    """获取有笔记的书籍概览（笔记本列表）。

    Args:
        count: 每页数量，默认 20。
        last_sort: 翻页游标（上一页最后一条的 sort 值）。
    """
    import json

    result = client.list_notebooks(count=count, last_sort=last_sort)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(description="划线: 获取某本书的所有划线内容。")
def weread_get_bookmarks(book_id: str) -> str:
    """获取单本书的划线内容列表。

    Args:
        book_id: 书籍唯一标识。
    """
    import json

    result = client.get_bookmarks(book_id=book_id)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(description="热门划线: 获取某本书的 Popular Highlights（热门划线）。")
def weread_get_best_bookmarks(
    book_id: str,
    chapter_uid: int | None = None,
) -> str:
    """获取书籍热门划线，包含划线原文和划线人数。

    Args:
        book_id: 书籍唯一标识。
        chapter_uid: 章节 UID。0=全部章节，默认全部。
    """
    import json

    result = client.get_best_bookmarks(
        book_id=book_id,
        chapter_uid=chapter_uid,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(description="个人想法: 获取某本书的个人想法与点评。")
def weread_get_my_reviews(
    book_id: str,
    synckey: int | None = None,
    count: int | None = None,
) -> str:
    """获取当前用户在指定书籍上的所有个人想法与点评。

    Args:
        book_id: 书籍 ID。
        synckey: 翻页游标，默认 0。
        count: 每页数量，默认 20。
    """
    import json

    result = client.get_my_reviews(
        book_id=book_id,
        synckey=synckey,
        count=count,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(description="公开点评: 获取某本书的公开点评列表。")
def weread_get_reviews(
    book_id: str,
    review_list_type: int | None = None,
    count: int | None = None,
    max_idx: int | None = None,
    synckey: int | None = None,
) -> str:
    """获取书籍公开点评。

    Args:
        book_id: 书籍 ID。
        review_list_type: 筛选类型。0=全部, 1=推荐, 2=不行, 3=最新, 4=一般。
        count: 每页数量，默认 20。
        max_idx: 翻页偏移。
        synckey: 翻页游标。
    """
    import json

    result = client.get_reviews(
        book_id=book_id,
        review_list_type=review_list_type,
        count=count,
        max_idx=max_idx,
        synckey=synckey,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(description="推荐: 获取个性化推荐（为你推荐）。")
def weread_get_recommend(
    count: int | None = None,
    max_idx: int | None = None,
) -> str:
    """获取基于用户阅读记录的个性化推荐。

    Args:
        count: 每页数量，默认 12。
        max_idx: 翻页偏移。
    """
    import json

    result = client.get_recommend(count=count, max_idx=max_idx)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ---- 入口 ----

def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
