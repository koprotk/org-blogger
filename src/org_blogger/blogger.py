"""Thin wrappers around the Google Blogger API."""

from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import SCOPES, find_secret_file


def get_credentials(cred_dir: str | Path) -> Credentials:
    """Load, refresh, or create the OAuth credentials for Blogger."""
    cred_dir = Path(cred_dir).expanduser()
    token_file = cred_dir / "token.json"
    secret_file = find_secret_file(cred_dir)

    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(secret_file), SCOPES)
            creds = flow.run_local_server(port=0)

        cred_dir.mkdir(parents=True, exist_ok=True)
        token_file.write_text(creds.to_json(), encoding="utf-8")

    return creds


def get_blog_id(cred_dir: str | Path) -> str | None:
    """Return the ID of the first blog owned by the authenticated user."""
    service = build("blogger", "v3", credentials=get_credentials(cred_dir))
    blogs = service.blogs().listByUser(userId="self").execute()
    items = blogs.get("items", [])
    if not items:
        print("No blogs found for this user.")
        return None
    blog_id = items[0]["id"]
    print(f"Your blog ID is: {blog_id}")
    return blog_id


def create_post(
    blog_id: str,
    title: str,
    content: str,
    labels: list[str],
    cred_dir: str | Path,
    *,
    is_draft: bool = False,
) -> bool:
    """Create a Blogger post. Return ``True`` on success."""
    service = build("blogger", "v3", credentials=get_credentials(cred_dir))
    post_body = {
        "kind": "blogger#post",
        "blog": {"id": blog_id},
        "title": title,
        "content": content,
        "labels": labels,
    }
    try:
        response = (
            service.posts()
            .insert(blogId=blog_id, body=post_body, isDraft=is_draft)
            .execute()
        )
    except HttpError as error:
        print(f"Could not create the post: {error}")
        return False

    print(f"Post created successfully. Title: {response['title']}")
    print(f"Post URL: {response['url']}")
    return True
