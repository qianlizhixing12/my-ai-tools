# WeRead MCP Server

微信读书 (WeRead) API 的 MCP 桥接服务。

将通过 Agent API Gateway 调用的微信读书接口暴露为标准 MCP 工具，
供任何 MCP 兼容客户端（如 Codex）使用。

## 配置

```bash
# 方式一：环境变量
export WEREAD_API_KEY=wrk-xxxx
python server.py

# 方式二：.env 文件
cp .env.example .env
# 编辑 .env 填入你的 API Key
python server.py
```

## 暴露的 MCP 工具

| 工具 | 描述 | 对应 API |
|------|------|----------|
| `weread_gateway_call` | 通用网关调用（兜底） | 任意 |
| `weread_search` | 搜索书籍/作者/文章 | `/store/search` |
| `weread_get_shelf` | 获取书架 | `/shelf/sync` |
| `weread_get_book_info` | 书籍详细信息 | `/book/info` |
| `weread_get_chapters` | 章节目录 | `/book/chapterinfo` |
| `weread_get_reading_progress` | 阅读进度 | `/book/getprogress` |
| `weread_get_reading_stats` | 阅读统计 | `/readdata/detail` |
| `weread_list_notebooks` | 笔记概览 | `/user/notebooks` |
| `weread_get_bookmarks` | 划线内容 | `/book/bookmarklist` |
| `weread_get_best_bookmarks` | 热门划线 | `/book/bestbookmarks` |
| `weread_get_my_reviews` | 个人想法/点评 | `/review/list/mine` |
| `weread_get_reviews` | 公开点评 | `/review/list` |
| `weread_get_recommend` | 个性化推荐 | `/book/recommend` |

## 开发

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

## 依赖

- Python >= 3.11
- [mcp](https://github.com/modelcontextprotocol/python-sdk)
- httpx
- python-dotenv

## License

MIT
