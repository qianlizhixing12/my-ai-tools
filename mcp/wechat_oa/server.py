"""MCP Server: 微信公众号 (WeChat Official Account) API 桥接层。

将微信公众号开发者 API 暴露为标准 MCP 工具，供 Codex 等 MCP 客户端调用。

使用方式：
    export WECHAT_APPID=wx-xxxx
    export WECHAT_APPSECRET=xxxx
    python server.py
    # 或使用 .env 文件
    cp .env.example .env
    # 编辑 .env 填入凭据
    python server.py
"""

import os
import sys
import json
from pathlib import Path

from mcp.server import FastMCP
from dotenv import load_dotenv

from wechat_client import WeChatAPI

# ---- MCP 服务初始化 ----

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

appid = os.environ.get("WECHAT_APPID")
appsecret = os.environ.get("WECHAT_APPSECRET")
if not appid or not appsecret:
    print("错误: 未设置 WECHAT_APPID / WECHAT_APPSECRET 环境变量。", file=sys.stderr)
    print("请通过 export 或 .env 文件设置。", file=sys.stderr)
    sys.exit(1)

client = WeChatAPI(appid=appid, appsecret=appsecret)

mcp = FastMCP(
    "WeChatOA",
    instructions="微信公众号 (WeChat Official Account) API 桥接 — "
    "上传图片、创建草稿、发布文章、检查权限。",
)


# ---- 工具注册 ----

@mcp.tool(
    description="上传文章内图片: 上传图片到微信服务器，返回可嵌入 <img src> 的 mmbiz.qpic.cn URL。"
)
def wechat_oa_upload_article_image(image_path: str) -> str:
    """上传文章正文图片。

    Args:
        image_path: 本地图片文件路径。

    Returns:
        JSON 字符串，包含 url 字段。
    """
    url = client.upload_article_image(image_path)
    return json.dumps({"url": url}, ensure_ascii=False)


@mcp.tool(
    description="上传封面图: 上传图片至微信素材库，返回 media_id（用于 draft/add 的 thumb_media_id）。"
)
def wechat_oa_upload_cover_image(image_path: str) -> str:
    """上传封面图素材。

    Args:
        image_path: 本地图片文件路径。

    Returns:
        JSON 字符串，包含 media_id 字段。
    """
    media_id = client.upload_cover_image(image_path)
    return json.dumps({"media_id": media_id}, ensure_ascii=False)


@mcp.tool(
    description="创建草稿: 创建微信公众号草稿，保存在草稿箱。返回草稿的 media_id。"
)
def wechat_oa_create_draft(
    title: str,
    content: str,
    thumb_media_id: str | None = None,
) -> str:
    """创建微信公众号草稿。

    Args:
        title: 文章标题（约 60 字节 UTF-8 限制）。
        content: 微信公众号兼容的 HTML 内容。
        thumb_media_id: 封面图 media_id（通过 wechat_oa_upload_cover_image 获取）。

    Returns:
        JSON 字符串，包含 media_id 字段。
    """
    media_id = client.create_draft(
        title=title,
        content=content,
        thumb_media_id=thumb_media_id,
    )
    return json.dumps({"media_id": media_id}, ensure_ascii=False)


@mcp.tool(description="删除草稿: 按 media_id 删除微信公众号草稿箱中的草稿。")
def wechat_oa_delete_draft(media_id: str) -> str:
    """删除草稿。

    Args:
        media_id: 草稿的 media_id。

    Returns:
        JSON 字符串，成功时包含 errcode=0。
    """
    result = client.delete_draft(media_id)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool(
    description="发布草稿: 通过自由发布接口发布已有草稿（个人订阅号可能返回 48001 无权限）。"
)
def wechat_oa_publish_draft(media_id: str) -> str:
    """发布草稿。

    个人订阅号通常无此权限（errcode=48001）。

    Args:
        media_id: 草稿的 media_id。

    Returns:
        JSON 字符串，包含 publish_id、msg_data_id 等字段。
    """
    result = client.publish_draft(media_id)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool(
    description="检查权限: 诊断当前公众号有哪些 API 接口可用。返回各接口测试结果。"
)
def wechat_oa_check_permissions() -> str:
    """检查当前账号的 API 权限。

    Returns:
        JSON 字符串，各接口测试结果。
    """
    perms = client.check_permissions()
    return json.dumps(perms, ensure_ascii=False, indent=2)


@mcp.tool(
    description="获取 Access Token: 获取微信 API 访问令牌（自动缓存 2 小时）。"
)
def wechat_oa_get_access_token() -> str:
    """获取 access_token。

    Returns:
        JSON 字符串，包含 access_token（脱敏显示前 16 位）。
    """
    token = client.get_access_token()
    return json.dumps(
        {"access_token": f"{token[:16]}...", "full_length": len(token)},
        ensure_ascii=False,
    )

@mcp.tool(
    description="检查外网 IP: 获取当前机器的公网 IPv4 地址，用于配置微信 IP 白名单。"
)
def wechat_oa_check_ip() -> str:
    """获取当前外网 IP。"""
    import subprocess
    try:
        result = subprocess.run(
            ["curl", "-4", "ifconfig.me"],
            capture_output=True, text=True, timeout=10,
        )
        ip = result.stdout.strip()
        return json.dumps({"ip": ip}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)



# ---- 入口 ----

def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
