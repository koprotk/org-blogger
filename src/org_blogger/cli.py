"""Command line interface for org-blogger."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from . import __version__
from .blogger import create_post, get_blog_id
from .config import find_secret_file, resolve_config_dir
from .org_export import export_and_read

COMMANDS = {"publish"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="org-blogger",
        description="Export Org mode files with Emacs and publish them to Blogger.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    publish = subparsers.add_parser(
        "publish", help="Export an Org file and publish it to Blogger."
    )
    publish.add_argument(
        "file",
        help=(
            "Org file to publish. It can be a path or a filename inside "
            "--drafts-dir."
        ),
    )
    publish.add_argument(
        "--drafts-dir",
        default="drafts",
        help="Directory where drafts live (default: ./drafts).",
    )
    publish.add_argument(
        "--posts-dir",
        default="posts",
        help="Directory where published Org files are moved (default: ./posts).",
    )
    publish.add_argument(
        "--config-dir",
        default=None,
        help=(
            "Directory containing client_secret*.json and token.json. "
            "Defaults to ./config when it exists, otherwise "
            "$XDG_CONFIG_HOME/org-blogger."
        ),
    )
    publish.add_argument(
        "--blog-id",
        default=None,
        help="Blogger blog ID. Defaults to the first blog of the authenticated user.",
    )
    publish.add_argument(
        "--draft",
        action="store_true",
        help="Create the post as a draft instead of publishing it immediately.",
    )
    return parser


def resolve_org_file(file_arg: str, drafts_dir: str | Path) -> Path:
    """Resolve an Org file given directly or as a name inside ``drafts_dir``."""
    direct = Path(file_arg).expanduser()
    if direct.is_file():
        return direct.resolve()

    in_drafts = Path(drafts_dir).expanduser() / file_arg
    if in_drafts.is_file():
        return in_drafts.resolve()

    raise FileNotFoundError(
        f"Org file '{file_arg}' not found (looked at '{direct}' and '{in_drafts}')."
    )


def publish(args: argparse.Namespace) -> int:
    config_dir = resolve_config_dir(args.config_dir)
    find_secret_file(config_dir)

    org_file = resolve_org_file(args.file, args.drafts_dir)
    title, content, labels = export_and_read(org_file)

    blog_id = args.blog_id or get_blog_id(config_dir)
    if not blog_id:
        return 1

    success = create_post(
        blog_id,
        title,
        content,
        labels,
        config_dir,
        is_draft=args.draft,
    )
    if not success:
        return 1

    posts_dir = Path(args.posts_dir).expanduser()
    posts_dir.mkdir(parents=True, exist_ok=True)
    destination = posts_dir / org_file.name
    if destination.resolve() != org_file:
        shutil.move(str(org_file), str(destination))
        print(f"Moved '{org_file.name}' to '{posts_dir}'.")

    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # Backwards compatibility: `publish-blog post.org` used to take no
    # subcommand. Keep accepting that form.
    if argv and argv[0] not in COMMANDS and argv[0] not in {
        "-h",
        "--help",
        "--version",
    }:
        argv.insert(0, "publish")

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return publish(args)
    except (FileNotFoundError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
