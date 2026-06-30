# WeChat MCP Server

微信公众号 (WeChat Official Account) API 的 MCP 桥接服务。

将微信公众号开发者 API 暴露为标准 MCP 工具，供任何 MCP 兼容客户端（如 Codex）使用。

## 首次配置

```bash
cd ai-tools/mcp/wechat_oa
cp .env.example .env
# 编辑 .env 填入真实的 WECHAT_APPID 和 WECHAT_APPSECRET
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

凭据获取：https://mp.weixin.qq.com → 设置与开发 → 基本配置。

### IP 白名单

所有 API 调用需要在微信公众号后台配置 **IP 白名单**（设置与开发 → 基本配置 → IP 白名单）。

检查当前外网 IP：启动 MCP 后调用 `wechat_oa_check_ip` 工具。

## 暴露的 MCP 工具

| 工具                             | 描述                                 | 对应 API                         |
| -------------------------------- | ------------------------------------ | -------------------------------- |
| `wechat_oa_get_access_token`     | 获取 access_token（自动缓存）        | `/cgi-bin/token`                 |
| `wechat_oa_upload_article_image` | 上传文章图片，返回 mmbiz.qpic.cn URL | `/cgi-bin/media/uploadimg`       |
| `wechat_oa_upload_cover_image`   | 上传封面图，返回 media_id            | `/cgi-bin/material/add_material` |
| `wechat_oa_create_draft`         | 创建草稿到草稿箱                     | `/cgi-bin/draft/add`             |
| `wechat_oa_delete_draft`         | 删除草稿                             | `/cgi-bin/draft/delete`          |
| `wechat_oa_publish_draft`        | 发布草稿（个人号通常 48001）         | `/cgi-bin/freepublish/submit`    |
| `wechat_oa_check_permissions`    | 诊断 API 权限                        | 多个接口                         |
| `wechat_oa_check_ip`             | 获取当前外网 IPv4 地址               | -                                |

## 个人订阅号限制

| 功能      | API          | 替代方案               |
| --------- | ------------ | ---------------------- |
| 创建草稿  | ✓            | -                      |
| 自动发布  | ✗ (48001)    | 后台手动发布           |
| 原创声明  | 部分支持     | 后台手动声明           |
| 合集/专辑 | ✗ (48001)    | 后台手动添加           |
| 赞赏      | 需 500+ 粉丝 | API 可传参，可能被忽略 |

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
- requests
- python-dotenv

## 参考

- [wechat-api-notes.md](wechat-api-notes.md) — API 踩坑记录
- 微信官方文档: https://developers.weixin.qq.com/doc/offiaccount/

## 许可

MIT
