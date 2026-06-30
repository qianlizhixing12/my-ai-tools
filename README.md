# my-ai-tools

个人 AI 工具集，包含 Codex 技能 (Skill) 和 MCP 服务器。

工具主要由 AI 辅助生成，持续迭代中。

## 目录结构

```
ai-tools/
├── AGENTS.md                     # Codex 全局规则
├── README.md                     # 本文件
├── skills/                       # Codex Skill 定义
│   ├── weread/                   # 微信读书阅读数据
│   │   ├── SKILL.md
│   │   └── readdata.md
│   └── hugo-blog-publish/        # Hugo 博文 → 微信公众号发布
│       ├── SKILL.md
│       ├── scripts/              # 转换脚本 (publish.py, converter.py)
│       └── assets/               # 默认封面图
└── mcp/                          # MCP Server 实现
    ├── weread/                   # 微信读书 API 桥接
    │   ├── server.py
    │   ├── weread_client.py
    │   ├── requirements.txt
    │   ├── .env / .env.example
    │   └── README.md
    └── wechat_oa/                # 微信公众号 API 桥接
        ├── server.py
        ├── wechat_client.py
        ├── wechat-api-notes.md
        ├── requirements.txt
        ├── .env / .env.example
        └── README.md
```

## 安装

MCP 服务器和 Skill 通过软链接注册到 Codex：

```bash
# Skill
ln -sf $PWD/skills/weread $HOME/.codex/skills/weread
ln -sf $PWD/skills/hugo-blog-publish $HOME/.codex/skills/hugo-blog-publish

# MCP
codex mcp add weread $PWD/mcp/weread/.venv/bin/python $PWD/mcp/weread/server.py
codex mcp add wechat_oa $PWD/mcp/wechat_oa/.venv/bin/python $PWD/mcp/wechat_oa/server.py

# 全局规则
ln -sf $PWD/AGENTS.md $HOME/.codex/AGENTS.md
```

首次使用需创建 `.env` 并安装依赖，详见各 MCP 目录下的 README。

## 技能 (Skills)

### weread — 微信读书阅读数据

获取微信读书阅读统计：本周、上周、本月、本年、总计。

| 能力 | 说明 |
|------|------|
| 本周阅读 | 当前自然周的阅读时长、天数、排行 |
| 上周阅读 | 上一完整周的阅读统计，支持环比 |
| 月度/年度/总计 | 更长周期的聚合数据 |

依赖 MCP：`weread`

### hugo-blog-publish — Hugo 博文发布

将 Hugo Markdown 博文发布到 GitHub 并同步至微信公众号草稿箱。

| 步骤 | 说明 |
|------|------|
| Git 提交推送 | 自动判断新增/修改，提交并推送 |
| Markdown 转换 | 转微信公众号兼容 HTML（inline style） |
| 图片上传 | 文章图片 + 封面图 → 微信服务器 |
| 创建草稿 | 含固定作者/原创/推荐/赞赏设置 |
| 手动发布 | 后台确认原创、合集后发布 |

依赖 MCP：`wechat_oa`

## MCP 服务器

### weread — 微信读书 API

13 个工具，覆盖搜索、书架、书籍信息、阅读统计、笔记划线、点评、推荐。

| 工具 | 说明 |
|------|------|
| `weread_search` | 搜索书籍/作者/文章 |
| `weread_get_shelf` | 获取书架列表 |
| `weread_get_book_info` | 书籍详细信息 |
| `weread_get_chapters` | 章节目录 |
| `weread_get_reading_progress` | 阅读进度 |
| `weread_get_reading_stats` | 阅读统计（Skill 核心依赖） |
| `weread_list_notebooks` | 笔记概览 |
| `weread_get_bookmarks` | 划线内容 |
| `weread_get_best_bookmarks` | 热门划线 |
| `weread_get_my_reviews` | 个人想法/点评 |
| `weread_get_reviews` | 公开点评 |
| `weread_get_recommend` | 个性化推荐 |
| `weread_gateway_call` | 通用网关调用（兜底） |

### wechat_oa — 微信公众号 API

8 个工具，覆盖图片上传、草稿管理、发布、权限诊断。

| 工具 | 说明 |
|------|------|
| `wechat_oa_get_access_token` | 获取 access_token（自动缓存） |
| `wechat_oa_upload_article_image` | 上传文章图片 → mmbiz.qpic.cn URL |
| `wechat_oa_upload_cover_image` | 上传封面图 → media_id |
| `wechat_oa_create_draft` | 创建草稿到草稿箱 |
| `wechat_oa_delete_draft` | 删除草稿 |
| `wechat_oa_publish_draft` | 发布草稿（个人号通常 48001） |
| `wechat_oa_check_permissions` | 诊断 API 权限 |
| `wechat_oa_check_ip` | 获取当前外网 IPv4 地址 |

个人订阅号限制：自动发布、合集 API 不可用（errcode 48001），需后台手动操作。

## 架构

```
Skill (SKILL.md)
  → 描述工作流和调用 MCP 工具
  → 不包含 MCP 安装/运行时细节

MCP Server (server.py + *_client.py)
  → 封装外部 API 为标准 MCP 工具
  → 由 Codex 自动管理生命周期
  → README.md 包含安装配置指南

scripts/ (.venv + requirements.txt)
  → 辅助脚本（转换、解析等）
  → 不直接调用外部 API，由 MCP 工具代理
```

## 参考

- https://jspang.com/article/39
- [Model Context Protocol](https://modelcontextprotocol.io/)
