"""Export an Org file to HTML with Emacs and read its metadata."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from orgparse import load


def parse_labels(tags: str | None) -> list[str]:
    """Split an Org ``#+TAGS`` value into Blogger labels.

    Both comma-separated and whitespace-separated tags are accepted.
    """
    if not tags:
        return []
    return [tag for tag in re.split(r"[,\s]+", tags.strip()) if tag]


def export_and_read(org_file: str | Path) -> tuple[str, str, list[str]]:
    """Export ``org_file`` to HTML and return ``(title, html, labels)``.

    The temporary HTML file is removed before returning. Raises
    ``RuntimeError`` if Emacs fails or the expected metadata is missing.
    """
    org_file = Path(org_file).expanduser().resolve()
    html_file = org_file.with_suffix(".html")

    emacs_command = [
        "emacs",
        "--batch",
        "--eval",
        f'(progn (find-file "{org_file}") (org-html-export-to-html))',
    ]

    try:
        print(f"Exporting '{org_file.name}' to HTML with Emacs...")
        subprocess.run(
            emacs_command,
            check=True,
            capture_output=True,
            text=True,
        )
        print("Emacs export completed.")

        document = load(str(org_file))
        title = document.get_file_property("title")
        labels = parse_labels(document.get_file_property("tags"))

        if not title:
            raise RuntimeError(f"'{org_file.name}' has no #+TITLE property.")

        if not html_file.exists():
            raise RuntimeError(
                f"Emacs did not produce '{html_file.name}'. "
                "Check that org-html-export-to-html is available."
            )

        content = html_file.read_text(encoding="utf-8")
    except subprocess.CalledProcessError as error:
        stderr = (error.stderr or "").strip()
        raise RuntimeError(
            f"Emacs failed to export '{org_file.name}'. {stderr}"
        ) from error
    finally:
        html_file.unlink(missing_ok=True)

    return title, content, labels
