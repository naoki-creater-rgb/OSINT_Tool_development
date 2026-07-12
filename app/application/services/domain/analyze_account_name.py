import asyncio

import networkx as nx
from kg_gen.models import Graph

from app.infrastructure.clients.duckduckgo_search_client import search_keyword
from app.infrastructure.clients.playwright_client import get_html_with_playwright
from app.application.services.domain.extract_page_content import extract_page_content


async def _analyze_url(url: str) -> nx.MultiDiGraph | None:
  try:
    html = await asyncio.to_thread(get_html_with_playwright, url)
  except Exception as e:
    print(f"URL取得失敗のためスキップ: {url} ({e})")
    return None

  G_ai = await extract_page_content(html)

  G = nx.MultiDiGraph()
  G.add_node(url, type="url")
  G = nx.compose(G, G_ai)

  for node in G_ai.nodes():
    if node != url and G_ai.in_degree(node) == 0:
      G.add_edge(url, node, label="page content")

  return G


async def search_user_name(email: str) -> Graph:
  """
  メールのアカウント名(@より前)を検索エンジンで完全一致検索し、
  ヒットした各URLの本文テキストからAI(kg_gen)で関係グラフを構築・合成する。
  """
  duckduck_G = nx.MultiDiGraph()

  account_name = email.split("@")[0]
  duckduck_G.add_node(account_name, type="account_name")

  search_urls = await search_keyword(account_name)

  results = await asyncio.gather(*(_analyze_url(url) for url in search_urls))

  for url, G in zip(search_urls, results):
    if G is None:
      continue
    duckduck_G = nx.compose(duckduck_G, G)
    duckduck_G.add_edge(account_name, url, label="search hit")

  return duckduck_G
