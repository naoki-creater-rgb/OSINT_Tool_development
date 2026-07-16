from typing import List
from pydantic import BaseModel


class GitHubUserItem(BaseModel):
  """検索ヒットした1ユーザ分の情報"""
  login: str  # ユーザ名
  html_url: str  # プロフィールページURL


class GitHubSearchResponse(BaseModel):
  """users検索APIのレスポンス（必要フィールドのみ抽出）"""
  total_count: int  # ヒット件数
  items: List[GitHubUserItem] = []  # ヒットしたユーザ一覧
