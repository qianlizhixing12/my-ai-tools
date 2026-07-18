#!/usr/bin/env python3
"""检查并记录 Hugo 文章的微信公众号草稿同步状态。"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def resolve_article(repo: Path, article: str) -> tuple[str, Path]:
    article_path = Path(article)
    if not article_path.is_absolute():
        article_path = repo / article_path
    article_path = article_path.resolve()
    try:
        relative_path = article_path.relative_to(repo.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"文章不在 Hugo 仓库中: {article_path}") from exc
    if not article_path.is_file():
        raise FileNotFoundError(f"文章不存在: {article_path}")
    return relative_path, article_path


def current_commit(repo: Path, relative_path: str) -> str:
    commit = run_git(repo, "log", "-1", "--format=%H", "--", relative_path)
    if not commit:
        raise ValueError(f"文章尚无 Git commit: {relative_path}")
    return commit


def default_state_file(repo: Path) -> Path:
    """兼容普通仓库和 `.git` 为文件的 Git worktree。"""
    git_path = run_git(repo, "rev-parse", "--git-path", "wechat-publish-state.json")
    path = Path(git_path)
    if not path.is_absolute():
        path = repo / path
    return path.resolve()


def load_state(state_file: Path) -> tuple[dict, str | None]:
    if not state_file.exists():
        return {}, None
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, f"{type(exc).__name__}: {exc}"
    if not isinstance(data, dict):
        return {}, "ValueError: state root must be a JSON object"
    return data, None


def check_status(repo: Path, relative_path: str, state_file: Path) -> dict:
    commit = current_commit(repo, relative_path)
    state, error = load_state(state_file)
    if error:
        return {
            "status": "unknown",
            "reason": "同步回执无法读取，不能确认历史状态",
            "source_commit": commit,
            "state_error": error,
        }

    record = state.get(relative_path)
    if not isinstance(record, dict):
        return {
            "status": "needs_sync",
            "reason": "无同步回执",
            "source_commit": commit,
        }

    required = ("source_commit", "draft_media_id", "synced_at", "title")
    missing = [field for field in required if not record.get(field)]
    if missing:
        return {
            "status": "unknown",
            "reason": "同步回执字段缺失，不能确认历史状态",
            "source_commit": commit,
            "missing_fields": missing,
        }

    if record["source_commit"] == commit:
        return {
            "status": "synced",
            "reason": "当前文章 commit 已有同步回执",
            "source_commit": commit,
            "record": record,
        }
    return {
        "status": "needs_update",
        "reason": "文章 commit 已变化",
        "source_commit": commit,
        "record": record,
    }


def save_record(
    repo: Path,
    relative_path: str,
    state_file: Path,
    title: str,
    draft_media_id: str,
) -> dict:
    commit = current_commit(repo, relative_path)
    state, error = load_state(state_file)
    if error:
        raise ValueError(f"拒绝覆盖损坏的同步回执: {error}")

    record = {
        "source_commit": commit,
        "draft_media_id": draft_media_id,
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "title": title,
    }
    state[relative_path] = record
    state_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file = state_file.with_name(f".{state_file.name}.{os.getpid()}.tmp")
    try:
        temp_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temp_file, state_file)
    finally:
        if temp_file.exists():
            temp_file.unlink()
    return record


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("/home/nxx/wiki/hugo-blog"))
    parser.add_argument("--state-file", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="检查文章是否需要同步")
    check_parser.add_argument("article")

    record_parser = subparsers.add_parser("record", help="草稿创建成功后写入回执")
    record_parser.add_argument("article")
    record_parser.add_argument("--title", required=True)
    record_parser.add_argument("--draft-media-id", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo = args.repo.resolve()
    state_file = args.state_file or default_state_file(repo)
    try:
        relative_path, _ = resolve_article(repo, args.article)
        if args.command == "check":
            result = check_status(repo, relative_path, state_file)
        else:
            result = save_record(
                repo,
                relative_path,
                state_file,
                args.title,
                args.draft_media_id,
            )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
