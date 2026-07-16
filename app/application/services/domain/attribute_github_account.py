import asyncio

import networkx as nx
from kg_gen.models import Graph

from app.infrastructure.clients.github_client import (
  search_users_by_email,
  get_repositories_html,
)
from app.infrastructure.clients.beautifulsoup4_client import select_records_from_html

# GitHubはリポジトリ一覧ページで各リポジトリを itemprop="owns" のコンテナで
# 区切り、その中に名前・説明・言語を itemprop 付きで描画する。
# コンテナのタグはユーザにより <li>/<div> と異なるためタグ非依存で選択する。
REPO_ITEM_SELECTOR = '[itemprop="owns"]'
REPO_FIELD_SELECTORS = {
  "name": 'a[itemprop="name codeRepository"]',
  "description": 'p[itemprop="description"]',
  "language": '[itemprop="programmingLanguage"]',
}


def parse_repository_names(html: str, owner_url: str) -> nx.MultiDiGraph:
  """リポジトリ一覧ページのHTMLからリポジトリ名・説明・言語を抽出し、
  所有者(owner_url) → 各リポジトリ の部分グラフを構築して返す。"""
  repo_G = nx.MultiDiGraph()

  records = select_records_from_html(html, REPO_ITEM_SELECTOR, REPO_FIELD_SELECTORS)
  for record in records:
    name = record.get("name")
    if not name:
      continue
    # 同名リポジトリの衝突を避けるため所有者URLで一意化したノードIDを使う。
    repo_id = f"{owner_url}/{name}"
    repo_G.add_node(
      repo_id,
      type="repository",
      label=name,
      description=record.get("description") or "",
      language=record.get("language") or "",
    )
    repo_G.add_edge(owner_url, repo_id, label="has repository")
  return repo_G


async def attribute_github_account(email: str) -> Graph:
  """メールから GitHub ユーザを検索し、ヒットしたアカウントとその
  公開リポジトリを関係グラフ化する。"""
  github_G = nx.MultiDiGraph()
  github_G.add_node(email, type="email")

  search_result = await search_users_by_email(email)
  if search_result.total_count == 0:
    return github_G

  # 各ヒットユーザのリポジトリページHTMLを並列取得
  htmls = await asyncio.gather(
    *(get_repositories_html(user.html_url) for user in search_result.items)
  )

  for user, html in zip(search_result.items, htmls):
    github_G.add_node(user.html_url, type="github_account", login=user.login)
    github_G.add_edge(email, user.html_url, label="github user")

    # 所有者 → リポジトリ の部分グラフを構築し、本体グラフに合流させる。
    repo_G = parse_repository_names(html, user.html_url)
    github_G = nx.compose(github_G, repo_G)

  return github_G
