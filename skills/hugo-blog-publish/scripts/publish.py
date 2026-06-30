#!/usr/bin/env python3
"""
Hugo 博客 → 微信公众号 HTML 转换器

将 Hugo Markdown 博文转换为微信公众号兼容的 HTML。
所有微信 API 调用（上传图片、创建草稿、IP 检测等）由 wechat MCP 服务器处理。

用法:
    python publish.py <path-to-_index.md>            # 转换 + 输出结果摘要
    python publish.py <path-to-_index.md> --dry-run  # 转换 + 输出完整 HTML
"""

import sys
import argparse
from pathlib import Path

from converter import convert_post


def main():
    parser = argparse.ArgumentParser(description="Hugo 博客 → 微信公众号 HTML 转换器")
    parser.add_argument("md_file", nargs="?", help="_index.md 文件路径")
    parser.add_argument("--dry-run", action="store_true", help="输出完整 HTML 预览")
    args = parser.parse_args()

    if not args.md_file:
        parser.print_help()
        sys.exit(1)

    md_path = Path(args.md_file)
    if not md_path.exists():
        print(f"文件不存在: {md_path}")
        sys.exit(1)

    print(f"=== 转换博文: {md_path} ===")
    try:
        result = convert_post(str(md_path))
    except Exception as e:
        print(f"转换失败: {e}")
        sys.exit(1)

    title = result["title"]
    title_bytes = len(title.encode("utf-8"))
    print(f"标题:   {title}")
    if title_bytes > 60:
        print(f"        ⚠ 标题 {title_bytes} 字节，超出微信 60 字节限制，需截断")
    print(f"日期:   {result['date']}")
    print(f"图片:   {len(result['images'])} 张")
    for img_path, alt in result["images"]:
        print(f"        - {img_path} ({alt})")
    print(f"HTML:   {len(result['content'])} 字符")

    if args.dry_run:
        print(f"\n=== HTML ===")
        print(result["content"])


if __name__ == "__main__":
    main()
