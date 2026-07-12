import asyncio
from typing import List

from ddgs import DDGS

# 1回の検索で取得する最大件数
MAX_RESULTS = 3

def _search(keyword: str) -> List[str]:
  # DDGS は同期APIのため、呼び出し側は asyncio.to_thread 経由で使う。
  # キーワードを完全一致（"..."）で検索し、ヒットしたURLのリストを返す。
  results = DDGS().text(f'"{keyword}"', max_results = MAX_RESULTS)

  return [result["href"] for result in results if result.get("href")]

async def search_keyword(keyword: str) -> List[str]:
  """
  キーワードを DuckDuckGo で完全一致検索し、ヒットしたURLのリストを返す。
  ヒット0件の場合は空リスト。
  """
  return await asyncio.to_thread(_search, keyword)
