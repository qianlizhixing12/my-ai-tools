"""
Hugo Markdown → 微信公众号 HTML 转换器

微信公众号支持的 HTML 子集：
  section, h1-h6, p, span, strong, em, br, ul, ol, li, img, a,
  blockquote, pre, code, sub, sup, table/thead/tbody/tr/th/td

不支持:
  div, class, id, external stylesheets, custom fonts, iframe, video
"""

import re
import yaml
import html as html_mod
from pathlib import Path


def parse_frontmatter(md_text: str) -> tuple[dict, str]:
    """分离 YAML frontmatter 和正文"""
    if md_text.startswith("---"):
        parts = md_text.split("---", 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()
            return meta, body
    return {}, md_text


def _escape_html(text: str) -> str:
    """转义 HTML 特殊字符（但保留已有的标签）"""
    return text


def _parse_inline(text: str) -> str:
    """处理行内格式：粗体、斜体、行内代码、链接、图片"""
    # 行内代码 `code`
    text = re.sub(
        r"`([^`]+)`",
        r'<code style="background:#f0f0f0;padding:1px 4px;border-radius:3px;font-size:14px;">\1</code>',
        text,
    )
    # 粗体 **text** 或 __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)
    # 斜体 *text* 或 _text_
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"_(.+?)_", r"<em>\1</em>", text)
    # 链接 [text](url)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2" style="color:#576b95;">\1</a>',
        text,
    )
    # 图片 ![alt](url) → 占位标记，后续由 API 上传替换
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"<!--WECHAT_IMG:\2-->\1<!--/WECHAT_IMG-->", text)
    # 删除线 ~~text~~
    text = re.sub(r"~~(.+?)~~", r'<span style="text-decoration:line-through;">\1</span>', text)
    return text


def markdown_to_wechat_html(md_body: str) -> str:
    """
    将 Markdown 正文转换为微信公众号兼容的 HTML。
    返回 (html, image_paths) — images 是需要上传的本地图片路径列表。
    """
    lines = md_body.split("\n")
    output = []
    i = 0
    image_paths = []

    while i < len(lines):
        line = lines[i]

        # 空行
        if not line.strip():
            output.append("<p><br></p>")
            i += 1
            continue

        # 代码块 ```
        if line.strip().startswith("```"):
            lang = line.strip()[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            code_text = "\n".join(code_lines)
            escaped = html_mod.escape(code_text)
            escaped = re.sub(r"<!--WECHAT_IMG:.+?-->.+?<!--/WECHAT_IMG-->",
                             lambda m: html_mod.unescape(m.group(0)), escaped)
            output.append(
                f'<pre style="background:#f5f5f5;padding:12px;border-radius:4px;'
                f'overflow-x:auto;font-size:13px;line-height:1.6;'
                f'font-family:monospace;"><code>{escaped}</code></pre>'
            )
            continue

        # 标题 ## ### ####
        heading_match = re.match(r"^(#{2,6})\s+(.+)$", line)
        if heading_match:
            level = min(len(heading_match.group(1)), 6)
            text = _parse_inline(heading_match.group(2))
            sizes = {2: 20, 3: 18, 4: 16, 5: 15, 6: 14}
            weights = {2: "bold", 3: "bold", 4: "bold", 5: "normal", 6: "normal"}
            colors = {2: "#1a1a1a", 3: "#333", 4: "#555", 5: "#666", 6: "#777"}
            output.append(
                f'<h{level} style="font-size:{sizes.get(level,16)}px;'
                f'font-weight:{weights.get(level,"bold")};'
                f'color:{colors.get(level,"#333")};'
                f'margin:16px 0 8px 0;line-height:1.5;">{text}</h{level}>'
            )
            i += 1
            continue

        # 无序列表 - item 或 * item
        ul_match = re.match(r"^(\s*)[-*]\s+(.+)$", line)
        if ul_match:
            indent = len(ul_match.group(1))
            items = []
            while i < len(lines):
                m = re.match(rf"^(\s{{{indent}}})[-*]\s+(.+)$", lines[i])
                if not m or len(m.group(1)) != indent:
                    break
                items.append(_parse_inline(m.group(2)))
                i += 1
            lis = "".join(
                f'<li style="margin:4px 0;line-height:1.75;">{item}</li>'
                for item in items
            )
            output.append(
                f'<ul style="padding-left:1.5em;margin:8px 0;color:#333;list-style-type:disc;">{lis}</ul>'
            )
            continue

        # 有序列表 1. item
        ol_match = re.match(r"^(\s*)\d+\.\s+(.+)$", line)
        if ol_match:
            indent = len(ol_match.group(1))
            items = []
            while i < len(lines):
                m = re.match(rf"^(\s{{{indent}}})\d+\.\s+(.+)$", lines[i])
                if not m or len(m.group(1)) != indent:
                    break
                items.append(_parse_inline(m.group(2)))
                i += 1
            lis = "".join(
                f'<li style="margin:4px 0;line-height:1.75;">{item}</li>'
                for item in items
            )
            output.append(
                f'<ol style="padding-left:1.5em;margin:8px 0;color:#333;">{lis}</ol>'
            )
            continue

        # 引用 >
        if line.strip().startswith(">"):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q = lines[i].strip()[1:].strip()
                quote_lines.append(q if q else "<br>")
                i += 1
            quoted = _parse_inline("<br>".join(quote_lines))
            output.append(
                f'<blockquote style="border-left:3px solid #ccc;'
                f'padding:8px 12px;margin:8px 0;color:#666;'
                f'background:#f9f9f9;font-size:14px;">{quoted}</blockquote>'
            )
            continue

        # 水平线 --- 或 ***
        if re.match(r"^[-*]{3,}\s*$", line.strip()):
            output.append(
                '<hr style="border:none;border-top:1px solid #e0e0e0;margin:16px 0;">'
            )
            i += 1
            continue

        # 图片行 ![](url)
        img_match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", line.strip())
        if img_match:
            alt = img_match.group(1) or "图片"
            src = img_match.group(2)
            image_paths.append(src)
            output.append(f"<!--WECHAT_IMG_PLACEHOLDER:{src}:{alt}-->")
            i += 1
            continue

        # 普通段落
        para_lines = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{2,6}\s|```|[-*]\s|\d+\.\s|>\s|!\[)", lines[i].strip()):
            para_lines.append(lines[i])
            i += 1
        para = " ".join(para_lines)
        if para.strip():
            para = _parse_inline(para)
            output.append(
                f'<p style="font-size:15px;color:#333;line-height:1.75;margin:0 0 8px 0;">{para}</p>'
            )

    # 收集图片路径
    all_images = []
    html_text = "\n".join(output)

    # 从占位符中提取图片
    placeholders = re.findall(r"<!--WECHAT_IMG_PLACEHOLDER:(.+?):(.+?)-->", html_text)
    for src, alt in placeholders:
        all_images.append((src, alt))

    return html_text, all_images


def convert_post(md_path: str) -> dict:
    """转换整篇 Hugo 博文"""
    with open(md_path, "r", encoding="utf-8") as f:
        raw = f.read()

    meta, body = parse_frontmatter(raw)
    html, images = markdown_to_wechat_html(body)

    # 用 section 包裹
    full_html = (
        '<section style="padding:0 16px;max-width:100%%;box-sizing:border-box;">\n'
        f'{html}\n'
        '</section>'
    )

    return {
        "title": meta.get("title", ""),
        "date": str(meta.get("date", "")),
        "content": full_html,
        "images": images,  # [(path, alt), ...]
        "source_file": md_path,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = convert_post(sys.argv[1])
        print("=== TITLE ===")
        print(result["title"])
        print("=== IMAGES ===")
        for p, a in result["images"]:
            print(f"  {p} ({a})")
        print("=== HTML (first 500 chars) ===")
        print(result["content"][:500])
    else:
        print("Usage: python converter.py <path-to-_index.md>")
