---
name: hugo-blog-publish
description: 发布 Hugo 博文到 GitHub 并同步至微信公众号草稿箱。适用场景：发布新博文、同步到微信、生成微信兼容 HTML。
version: 2.0.0
---

# Hugo 博文发布助手

将 Hugo 博客的 Markdown 博文一键发布到 GitHub，并通过 WeChatOA MCP 工具同步到微信公众号草稿箱。

## 前置条件

- Hugo 博客仓库：`/home/nxx/wiki/hugo-blog`
- WeChatOA MCP Server：`ai-tools/mcp/wechat_oa/`（Codex 自动管理，工具自动挂载）
- 转换脚本 venv：`ai-tools/skills/hugo-blog-publish/.venv`（dep: pyyaml）
- 公众号凭据：`ai-tools/mcp/wechat_oa/.env`（首次配置见 MCP README.md）

## 能力

| 步骤 | 说明 | 工具/命令 | 输入 |
|------|------|-----------|------|
| **Git 提交** | 自动判断新增/修改，提交并推送 | `git add` / `git commit` / `git push` | `_index.md` 路径 |
| **Markdown 转换** | 转微信公众号兼容 HTML（inline style） | `.venv/bin/python scripts/publish.py` | `_index.md` 路径 |
| **文章图片上传** | 上传至 mmbiz.qpic.cn，返回直接 URL | `wechat_oa_upload_article_image` | 本地图片路径 |
| **封面图上传** | 上传至素材库，返回 media_id | `wechat_oa_upload_cover_image` | 本地图片路径 |
| **创建草稿** | 创建草稿到草稿箱 | `wechat_oa_create_draft` | title + HTML + thumb_media_id |
| **删除草稿** | 按 media_id 删除 | `wechat_oa_delete_draft` | media_id |
| **权限诊断** | 检查各 API 可用性 | `wechat_oa_check_permissions` | - |
| **IP 检测** | 获取当前外网 IP | `wechat_oa_check_ip` | - |

## 工作流

### 1. Git 提交并推送

```bash
cd /home/nxx/wiki/hugo-blog
git status
```

- `_index.md` **新文件**：`git add <path> && git commit -m "<title>"`
- `_index.md` **已修改**：`git add <path> && git commit --amend -m "<title>"`
- `_index.md` **未跟踪**：`git add <path> && git commit -m "<title>"`

推送：`git push`（amend 时用 `git push --force-with-lease`）

标题取自 YAML frontmatter 的 `title:` 字段。

### 2. Markdown 转 HTML

```bash
cd ai-tools/skills/hugo-blog-publish
.venv/bin/python scripts/publish.py /home/nxx/wiki/hugo-blog/content/docs/<category>/<slug>/_index.md
```

输出：标题、日期、图片列表、HTML 长度。预览完整 HTML：

```bash
.venv/bin/python scripts/publish.py <path> --dry-run
```

### 3. 上传图片

遍历转换输出的图片列表，分别调用：

- 文章内图片 → `wechat_oa_upload_article_image(image_path=<path>)` → 用返回的 `url` 替换 HTML 中的占位符
- 首张图片同时作为封面 → `wechat_oa_upload_cover_image(image_path=<path>)` → 记下 `media_id`

### 4. 创建草稿

```python
wechat_oa_create_draft(
    title="标题（≤60 字节 UTF-8）",
    content="替换图片后的 HTML",
    thumb_media_id="封面图 media_id"
)
```

### 5. 后端手动发布

个人订阅号不支持 API 自动发布。登录 https://mp.weixin.qq.com：

1. 草稿箱预览，确认图片、作者、声明、推荐、赞赏开关
2. 手动声明**原创**（API 对个人号不生效）
3. 手动添加到**合集**
4. 点击**发布**

## 草稿设置

`wechat_client.py` 中硬编码的固定值：

| 设置项 | 值 |
|--------|----|
| 作者 | 函关骑牛 |
| 原创声明 | copyright_type=1 |
| 版权作者 | 函关骑牛 |
| 声明文案 | 个人观点，仅供参考 |
| 平台推荐 | need_open_recommend=1 |
| 赞赏 | need_open_reward=1 |
| 赞赏文案 | 感谢支持 |

## 分类→合集映射

发布后在后台手动打标：

| Hugo category | WeChat 合集 |
|---------------|------------|
| ai | AI学习合集 |
| career | 职场交流合集 |
| coding | linux内核学习合集 |

## 输出格式

每次发布操作完成后的摘要示例：

```
=== Step 1: Git ===
commit: 在obsidian上使用DeepSeek模型（免费）
push:   ✓

=== Step 2: 转换 ===
标题:   在obsidian上使用DeepSeek模型（免费）
日期:   2026-06-28
图片:   1 张 → 已上传
HTML:   3124 字符

=== Step 3: 草稿 ===
media_id: xxxxxxxxxxxxxxxxxxxx
状态:    已保存至草稿箱
```

## 注意事项

1. **标题限制**：微信公众号标题约 60 UTF-8 字节（中文字符各 3 字节，约 20 字），converter 自动截断
2. **图片接口**：文章图片用 `uploadimg`（返回 URL），封面图用 `add_material`（返回 media_id），两个接口不可混用
3. **JSON 编码**：`requests.post(url, json=payload)` 会把中文转成 `\uXXXX` 导致乱码，wechat_client.py 已用 `ensure_ascii=False` + 字节编码处理
4. **HTML 限制**：仅支持 section, h1-h6, p, span, strong, em, br, ul, ol, li, img, a, blockquote, pre, code, sub, sup；不支持 div / class / id / 外部 CSS
5. **个人号限制**：自动发布 (48001)、合集 API (48001) 均不可用，需后台手动操作
6. **IP 白名单**：服务器 IP 变更后需在微信后台更新，可用 `wechat_oa_check_ip` 检测
7. **封面图**：draft API 的 `thumb_media_id` 为必填，无文章图片时自动使用 `assets/default-cover.png`
