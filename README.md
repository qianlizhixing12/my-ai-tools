# my-ai-tools

- 个人ai工具(包括不限于skill mcp等)
- 工具本身大多由ai自动生成

## 参考

- https://jspang.com/article/39

## 目录结构

```
ai-tools/
├── AGENTS.md                 # 用户行为准则文件
├── mcp/weread/               # MCP Server — 微信读书 API 桥接（自动加载）
│   ├── server.py             # MCP 入口，注册 13 个 weread_* 工具
│   ├── weread_client.py      # WeRead Agent API Gateway 客户端
│   ├── requirements.txt      # Python 依赖
│   ├── .env                  # WEREAD_API_KEY（MCP server 自动读取）
│   ├── .env.example          # 环境变量模板
│   ├── README.md             # 使用说明
│   └── .venv/                # Python 虚拟环境
└── skills/weread/            # Skill — 阅读数据获取
    ├── SKILL.md              # 技能定义：最新一周 / 本周 / 所有时期阅读统计
    └── readdata.md           # 阅读统计字段参考
```

## 使用(加入codex全局)

- AGENTS.md `ln -s $PWD/AGENTS.md $HOME/.codex/AGENTS.md`
- skill(weread为例) `$ ln -s $PWD/skills/weread $HOME/.codex/skills/weread`
- mcp(weread为例) `codex mcp add weread $PWD/mcp/weread/.venv/bin/python $PWD/mcp/weread/server.py`

## 架构说明

- **MCP 层**（`mcp/weread`）：将微信读书 Agent API Gateway 封装为标准 MCP 工具。
  配置在 `~/.codex/config.*` 中，由 Codex 自动管理启动和连接，
  工具直接暴露为可调用函数（`mcp__weread__weread_*`）。
  包含搜索、书架、书籍信息、阅读统计、笔记划线、点评、推荐等全部接口。
- **Skill 层**（`skills/weread`）：基于 MCP 工具，聚焦阅读数据获取场景。
  通过 `weread_get_reading_stats` 工具查询最新一周 / 本周 / 所有时期的阅读统计。

## 工具列表

MCP server 启动后，以下工具自动挂载为可调用函数：

- `mcp__weread__weread_search` — 搜索书籍/作者/文章
- `mcp__weread__weread_get_shelf` — 书架列表
- `mcp__weread__weread_get_book_info` — 书籍信息
- `mcp__weread__weread_get_chapters` — 章节目录
- `mcp__weread__weread_get_reading_progress` — 阅读进度
- `mcp__weread__weread_get_reading_stats` — 阅读统计（skill 核心依赖）
- `mcp__weread__weread_list_notebooks` — 笔记概览
- `mcp__weread__weread_get_bookmarks` — 划线内容
- `mcp__weread__weread_get_best_bookmarks` — 热门划线
- `mcp__weread__weread_get_my_reviews` — 个人想法
- `mcp__weread__weread_get_reviews` — 公开点评
- `mcp__weread__weread_get_recommend` — 个性化推荐
- `mcp__weread__weread_gateway_call` — 通用网关调用

## 使用方式

MCP server 由 Codex 自动管理，无需手动启动。
直接调用对应的 `mcp__weread__weread_*` 函数即可。

技能使用参考 `skills/weread/SKILL.md`。
