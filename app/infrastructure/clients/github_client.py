import asyncio
import os

import httpx
from dotenv import load_dotenv

from app.infrastructure.clients.playwright_client import get_html_with_playwright
from app.infrastructure.request_models.github_model import GitHubSearchResponse

load_dotenv(".env")

GITHUB_SEARCH_URL = "https://api.github.com/search/users"
# 任意。設定するとレート制限が緩和される（未設定でも動作する）。
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def _headers() -> dict:
  header = {"Accept": "application/vnd.github+json"}
  if GITHUB_TOKEN:
    header["Authorization"] = f"Bearer {GITHUB_TOKEN}"
  return header


async def search_users_by_email(email: str) -> GitHubSearchResponse:
  """メールアドレスで GitHub ユーザを検索し、ヒットしたアカウントを返す。"""
  async with httpx.AsyncClient() as client:
    response = await client.get(
      GITHUB_SEARCH_URL, headers=_headers(), params={"q": email}
    )
    response.raise_for_status()
    return GitHubSearchResponse.model_validate(response.json())


async def get_repositories_html(html_url: str) -> str:
  """プロフィールURLのリポジトリタブを開き、レンダリング後のHTMLを返す。
  抽出（リポジトリ名のパース）はサービス層で行う。"""
  repositories_url = f"{html_url}?tab=repositories"
  return await asyncio.to_thread(get_html_with_playwright, repositories_url)
