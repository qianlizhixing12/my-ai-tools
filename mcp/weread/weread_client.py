"""微信读书 Agent API Gateway 客户端封装。"""

import os
from pathlib import Path
from typing import Any

import httpx

class WeReadClient:
    """封装对微信读书 Agent API Gateway 的 HTTP 调用。"""

    BASE_URL = "https://i.weread.qq.com/api/agent/gateway"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("WEREAD_API_KEY")
        if not self.api_key:
            raise ValueError(
                "WEREAD_API_KEY 未设置。请通过环境变量 WEREAD_API_KEY 设置，"
                "或创建 .env 文件写入 WEREAD_API_KEY=wrk-xxxx"
            )
        self._version = "1.0.3"

    def call(self, api_name: str, **kwargs: Any) -> dict[str, Any]:
        """调用 WeRead Gateway API。

        Args:
            api_name: 接口名称，如 /store/search, /readdata/detail 等。
            **kwargs: 接口的业务参数，平铺在 body 顶层。

        Returns:
            解析后的 JSON 回包（dict）。

        Raises:
            httpx.HTTPError: 网络/HTTP 层错误。
            ValueError: 接口返回 errcode 非 0 时抛出。

        Note:
            参数必须平铺在 body 顶层，不要包在 params/data/body 等对象中。
        """
        body: dict[str, Any] = {
            "api_name": api_name,
            "skill_version": self._version,
            **kwargs,
        }

        with httpx.Client() as client:
            resp = client.post(
                self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=30.0,
            )
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()

        errcode = data.get("errcode", 0)
        if errcode not in (0, None):
            errmsg = data.get("errmsg", "未知错误")
            raise ValueError(f"WeRead API 错误 (errcode={errcode}): {errmsg}")

        if "upgrade_info" in data:
            data["_upgrade_warning"] = data["upgrade_info"].get(
                "message", "有版本更新，请升级。"
            )

        return data

    # ---- 通用查询 ----

    def list_apis(self) -> dict[str, Any]:
        """列出所有可用接口及参数定义。"""
        return self.call("/_list")

    # ---- 搜索 ----

    def search(
        self,
        keyword: str,
        scope: int | None = None,
        max_idx: int | None = None,
        count: int | None = None,
    ) -> dict[str, Any]:
        """搜索书籍 / 作者 / 文章等。"""
        params: dict[str, Any] = {"keyword": keyword}
        if scope is not None:
            params["scope"] = scope
        if max_idx is not None:
            params["maxIdx"] = max_idx
        if count is not None:
            params["count"] = count
        return self.call("/store/search", **params)

    # ---- 书架 ----

    def get_shelf(self) -> dict[str, Any]:
        """获取用户书架列表。"""
        return self.call("/shelf/sync")

    # ---- 书籍信息 ----

    def get_book_info(self, book_id: str) -> dict[str, Any]:
        """获取书籍基本信息。"""
        return self.call("/book/info", bookId=book_id)

    def get_chapters(self, book_id: str) -> dict[str, Any]:
        """获取章节目录。"""
        return self.call("/book/chapterinfo", bookId=book_id)

    def get_reading_progress(self, book_id: str) -> dict[str, Any]:
        """获取阅读进度。"""
        return self.call("/book/getprogress", bookId=book_id)

    # ---- 阅读统计 ----

    def get_reading_stats(
        self,
        mode: str = "monthly",
        base_time: int | None = None,
    ) -> dict[str, Any]:
        """获取阅读统计详情。

        Args:
            mode: 统计维度。weekly=本周, monthly=本月, annually=本年, overall=总计。
            base_time: 基准时间戳（Unix 秒）。0=当前周期。
        """
        params: dict[str, Any] = {"mode": mode}
        if base_time is not None:
            params["baseTime"] = base_time
        return self.call("/readdata/detail", **params)

    # ---- 笔记/划线 ----

    def list_notebooks(
        self,
        count: int | None = None,
        last_sort: int | None = None,
    ) -> dict[str, Any]:
        """列出有笔记的书籍概览。"""
        params: dict[str, Any] = {}
        if count is not None:
            params["count"] = count
        if last_sort is not None:
            params["lastSort"] = last_sort
        return self.call("/user/notebooks", **params)

    def get_bookmarks(self, book_id: str) -> dict[str, Any]:
        """获取单本书的划线内容列表。"""
        return self.call("/book/bookmarklist", bookId=book_id)

    def get_best_bookmarks(
        self,
        book_id: str,
        chapter_uid: int | None = None,
    ) -> dict[str, Any]:
        """获取书籍热门划线（Popular Highlights）。"""
        params: dict[str, Any] = {"bookId": book_id}
        if chapter_uid is not None:
            params["chapterUid"] = chapter_uid
        return self.call("/book/bestbookmarks", **params)

    def get_chapter_underlines(
        self, book_id: str, chapter_uid: int
    ) -> dict[str, Any]:
        """获取章节划线热度统计（不含划线文本）。"""
        return self.call(
            "/book/underlines",
            bookId=book_id,
            chapterUid=chapter_uid,
        )

    def get_read_reviews(
        self,
        book_id: str,
        chapter_uid: int,
        reviews: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """获取划线下的想法/评论。"""
        return self.call(
            "/book/readreviews",
            bookId=book_id,
            chapterUid=chapter_uid,
            reviews=reviews,
        )

    def get_my_reviews(
        self,
        book_id: str,
        synckey: int | None = None,
        count: int | None = None,
    ) -> dict[str, Any]:
        """获取单本书的个人想法与点评。"""
        params: dict[str, Any] = {"bookid": book_id}
        if synckey is not None:
            params["synckey"] = synckey
        if count is not None:
            params["count"] = count
        return self.call("/review/list/mine", **params)

    def get_single_review(
        self,
        review_id: str,
        comments_count: int | None = None,
        likes_count: int | None = None,
    ) -> dict[str, Any]:
        """获取单条想法详情。"""
        params: dict[str, Any] = {"reviewId": review_id}
        if comments_count is not None:
            params["commentsCount"] = comments_count
        if likes_count is not None:
            params["likesCount"] = likes_count
        return self.call("/review/single", **params)

    # ---- 点评 ----

    def get_reviews(
        self,
        book_id: str,
        review_list_type: int | None = None,
        count: int | None = None,
        max_idx: int | None = None,
        synckey: int | None = None,
    ) -> dict[str, Any]:
        """获取书籍公开点评。"""
        params: dict[str, Any] = {"bookId": book_id}
        if review_list_type is not None:
            params["reviewListType"] = review_list_type
        if count is not None:
            params["count"] = count
        if max_idx is not None:
            params["maxIdx"] = max_idx
        if synckey is not None:
            params["synckey"] = synckey
        return self.call("/review/list", **params)

    # ---- 推荐 ----

    def get_recommend(
        self,
        count: int | None = None,
        max_idx: int | None = None,
    ) -> dict[str, Any]:
        """获取个性化推荐（为你推荐）。"""
        params: dict[str, Any] = {}
        if count is not None:
            params["count"] = count
        if max_idx is not None:
            params["maxIdx"] = max_idx
        return self.call("/book/recommend", **params)

    def get_similar(
        self,
        book_id: str,
        count: int | None = None,
        max_idx: int | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """获取相似书推荐。"""
        params: dict[str, Any] = {"bookId": book_id}
        if count is not None:
            params["count"] = count
        if max_idx is not None:
            params["maxIdx"] = max_idx
        if session_id is not None:
            params["sessionId"] = session_id
        return self.call("/book/similar", **params)

__all__ = ["WeReadClient"]
