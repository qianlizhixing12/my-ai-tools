---
name: hugo-blog-publish
description: 发布或更新 Hugo 博文到 GitHub，并将文章同步至微信公众号草稿箱；自动把 Markdown 转为微信兼容 HTML、根据正文生成专属封面、上传图片、创建草稿并记录同步回执。适用于发布新博文、继续同步已提交但尚未进入公众号的博文、更新已同步文章、补建微信草稿或仅生成微信兼容 HTML。
---

# Hugo 博文发布助手

将 Hugo 博客文章发布到 GitHub，并同步至微信公众号草稿箱。把 Git 发布与微信同步视为两个独立状态：文章已经提交或推送时，跳过对应 Git 操作，但仍继续判断并执行微信同步。

## 环境

- Hugo 仓库：`/home/nxx/wiki/hugo-blog`
- 转换脚本：本 skill 的 `scripts/publish.py`
- Python 环境：本 skill 的 `.venv`，依赖见 `scripts/requirements.txt`
- 微信接口：WeChatOA MCP 工具
- 同步回执：Git 元数据目录的 `wechat-publish-state.json`；脚本通过 `git rev-parse --git-path` 兼容普通仓库与 worktree

同步回执属于本机状态，不提交到 Git。不要把 Access Token、Cookie、公众号凭据或其他密钥写入回执或仓库。

## 发布状态判断

先定位目标 `_index.md`，读取 frontmatter 的 `title`，再执行：

```bash
cd /home/nxx/wiki/hugo-blog
git status --short -- <path>
git log -1 --format=%H -- <path>
git diff --quiet -- <path>
git diff --cached --quiet -- <path>
```

分别判断两个状态，不要因为 Git 工作区干净就结束任务。

### Git 状态

- 未跟踪文件：创建新 commit。
- 已跟踪且有改动：创建新 commit；除非用户明确要求，不使用 `commit --amend`。
- 无改动且已有 commit：记录为“已提交”，跳过 commit，继续微信同步。
- 推送前比较 upstream；只有本地领先时才 `git push`。
- 不使用 `push --force` 或 `push --force-with-lease`，除非用户明确要求重写远端历史。

只暂存目标文章及本次生成、且被文章引用的图片。不要顺带提交工作区内其他文件。

### 微信同步状态

使用本 skill 的 `scripts/publish_state.py` 检查 Git 元数据目录中的 `wechat-publish-state.json`：

```bash
.venv/bin/python scripts/publish_state.py check <article-path>
```

脚本输出 `synced`、`needs_sync`、`needs_update` 或 `unknown`。回执结构：

```json
{
  "content/docs/category/slug/_index.md": {
    "source_commit": "完整 Git commit SHA",
    "draft_media_id": "微信草稿 media_id",
    "synced_at": "ISO 8601 时间",
    "title": "实际创建草稿时的标题"
  }
}
```

按以下规则判断：

- 无目标文章记录：视为“尚未同步”，即使文章早已提交或推送，也要创建公众号草稿。
- `source_commit` 等于当前包含该文章的 commit，且用户未要求重建：视为“已同步”，不要重复创建。
- `source_commit` 不等于当前 commit：视为“博客已有更新”，创建新草稿。
- 回执损坏、字段缺失或无法读取：明确提示无法确认历史同步状态；默认继续创建草稿，但不要声称公众号中不存在旧草稿。
- 用户明确说“尚未同步”“重新同步”或“重建草稿”：以用户信息为准，创建草稿并更新回执。

WeChatOA 当前没有列举草稿或按标题查重的工具。不要仅凭标题、Git 状态或猜测宣称公众号草稿已存在；本地回执是自动判断依据。

## 工作流

### 1. 检查并发布 Git

先完成状态判断。若文章需要提交：

```bash
git add -- <article-path> <generated-image-path>
git commit -m "<title>"
```

然后在需要时执行 `git push`。若文章已提交，输出 commit SHA 并跳过这一步，不得停止后续流程。

### 2. 生成文章专属封面

禁止使用任何通用默认图。

按以下优先级选择封面：

1. 用户明确指定的封面；
2. frontmatter 明确配置的本地封面；
3. 根据文章内容生成的新封面。

需要生成时：

1. 阅读标题、摘要/description、一级主题、主要小节和结论，提炼一个视觉主体。
2. 使用内置 `image_gen` 工具生成横向文章封面，建议 2.35:1 或接近微信公众号封面比例。
3. 使用简洁、可辨识的构图；不得包含水印、品牌 Logo、密钥、个人信息或未经用户要求的文字。标题文字容易生成错误，默认不在图片中绘制文字。
4. 将最终图片复制到文章目录，命名为 `wechat-cover.png`；若文件已存在且用户未要求覆盖，使用 `wechat-cover-v2.png` 等版本名。
5. 检查图片内容与文章主题一致、横向裁切后主体仍清晰，然后把它作为封面上传。

生成图只作为微信封面时无需插入 Markdown；若用户要求博客页面也展示封面，再更新 Markdown/frontmatter 引用并纳入 Git 提交。

### 3. 转换 Markdown

在 skill 目录运行：

```bash
.venv/bin/python scripts/publish.py /home/nxx/wiki/hugo-blog/content/docs/<category>/<slug>/_index.md
```

完整预览：

```bash
.venv/bin/python scripts/publish.py <path> --dry-run
```

转换失败时保留关键英文异常，不继续创建不完整草稿。

### 4. 上传正文图片与封面

- 正文图片：逐张调用 `wechat_oa_upload_article_image(image_path=<absolute-path>)`，用返回的 `url` 替换对应 HTML 占位符。
- 封面图片：调用 `wechat_oa_upload_cover_image(image_path=<absolute-path>)`，保存返回的 `media_id`。
- Markdown 中的相对图片路径以 `_index.md` 所在目录解析，再传绝对路径。
- 图片不存在或上传失败时停止创建草稿，报告具体路径和英文错误。

正文首图与封面是不同用途。除非用户明确指定复用，使用上一步选定或生成的专属封面。

### 5. 创建或更新草稿

调用：

```python
wechat_oa_create_draft(
    title="标题（≤60 UTF-8 字节）",
    content="已替换正文图片 URL 的 HTML",
    thumb_media_id="封面 media_id"
)
```

当前工具没有原地更新草稿的接口：

- 首次同步：创建草稿。
- 文章更新：创建新草稿；若回执中有旧 `draft_media_id`，只有用户明确授权替换/删除旧草稿时，才调用 `wechat_oa_delete_draft`。
- 不要为了“更新”自动删除旧草稿，避免不可逆地删错内容。

创建成功后运行：

```bash
.venv/bin/python scripts/publish_state.py record <article-path> \
  --title "<实际标题>" \
  --draft-media-id "<media_id>"
```

脚本通过 `git rev-parse --git-path` 定位并原子更新 `wechat-publish-state.json`，记录目标文章的 repo 相对路径、当前 `source_commit`、新 `draft_media_id`、`synced_at` 和实际标题。创建失败时不得写成功回执。

若封面只用于微信且位于文章目录、但用户不希望它进入静态博客提交，可以保留为未跟踪文件；在结果中明确说明。

### 6. 后台手动发布

个人订阅号不支持 API 自动发布。登录 `https://mp.weixin.qq.com`：

1. 在草稿箱预览并检查图片、作者和排版；
2. 手动声明原创；
3. 手动添加合集；
4. 点击发布。

## 固定设置与限制

- 标题约限 60 UTF-8 字节；中文通常约 20 字。超限时先给出拟截断标题，保持语义完整。
- 正文图片使用 `uploadimg` 返回 URL；封面使用素材接口返回 `media_id`，不可混用。
- HTML 仅使用微信支持的标签和 inline style，不使用外部 CSS、`class`、`id`、`iframe` 或未知脚本。
- 自动发布和合集 API 对个人号可能返回 `48001`，需后台手动完成。
- IP 白名单异常时调用 `wechat_oa_check_ip`，保留原始错误码与英文错误信息。

分类与合集：

| Hugo category | WeChat 合集 |
|---|---|
| ai | AI学习合集 |
| career | 职场交流合集 |
| coding | linux内核学习合集 |

## 完成摘要

最终明确报告 Git 与微信两个状态：

```text
=== Git ===
文章: content/docs/<category>/<slug>/_index.md
commit: <sha>（新建 / 已存在）
push: 已推送 / 无需推送 / 失败

=== 微信 ===
判断: 无同步回执 / commit 已变化 / 已同步 / 用户要求重建
封面: <generated-or-selected-path>（根据正文生成 / 用户指定）
正文图片: <count> 张，已上传
draft media_id: <id>
回执: <git-path>/wechat-publish-state.json 已更新
状态: 已保存至草稿箱 / 已跳过 / 失败
```

不得把“Git 已提交”写成“微信公众号已同步”，也不得在微信创建失败时输出成功状态。
