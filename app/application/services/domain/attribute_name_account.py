import asyncio

import networkx as nx
from kg_gen.models import Graph

from app.infrastructure.clients.whatsmyname_client import check_user_service
from app.infrastructure.clients.playwright_client import get_html_with_playwright
from app.application.services.domain.extract_page_content import extract_page_content


async def _follow_service_url(url: str | None) -> nx.MultiDiGraph | None:
  """サービスのプロフィールURLをPlaywrightで取得し、本文をkg_genで関係グラフ化する。

  取得(Playwright)・テキスト抽出(BS4)・関係抽出(kg_gen)はいずれも
  インフラ層のクライアントに委譲し、ここでは呼び出しの組み立てのみ行う。
  extract_page_content が内部で BS4→kg_gen を実施する。
  """
  if not url:
    return None
  try:
    html = await asyncio.to_thread(get_html_with_playwright, url)
  except Exception as e:
    print(f"URL取得失敗のためスキップ: {url} ({e})")
    return None
  return await extract_page_content(html)


async def attribute_name_account(email: str, follow_service_urls: bool = False) -> Graph:
  """WhatsMyNameでアカウント名の利用サービスを探索し関係グラフ化する。

  follow_service_urls:
    False（既定）: 各サービスの site_name / profile url ノードのみ作る高速モード。
                   Playwright取得も kg_gen（ローカルLLM）抽出も行わない。
    True         : さらに各プロフィールURLをPlaywrightで取得し、本文を
                   kg_genで関係グラフ化してぶら下げる深掘りモード（低速）。

  WMNは同名別人を含め多数ヒットするため、深掘りは1件ごとに
  「ブラウザ描画＋ローカルLLM推論」のコストが乗る。速度優先なら既定のFalse、
  本文の裏付けまで欲しい場合のみTrueを指定する。
  """
  account_name = email.split("@")[0]

  use_service = await check_user_service(account_name)
  whatsmyname_G = nx.MultiDiGraph()

  # WhatsMyNameはアカウント名から探索するため、サービスノードは
  # emailではなくaccount_nameから伸ばす（compose時にaccount_nameノードで合流）。
  whatsmyname_G.add_node(account_name, type="account_name")

  # 深掘り指定時のみ、各プロフィールURLをPlaywright取得→kg_genで関係グラフ化。
  # 既定では取得・LLM抽出を一切行わずノード生成のみで高速に済ませる。
  if follow_service_urls:
    ai_graphs = await asyncio.gather(
      *(_follow_service_url(service.result_url) for service in use_service)
    )
  else:
    ai_graphs = [None] * len(use_service)

  for service, G_ai in zip(use_service, ai_graphs):
    whatsmyname_G.add_node(service.site_name, type="service name")
    whatsmyname_G.add_edge(account_name, service.site_name, label="may use")

    url = service.result_url
    if not url:
      continue

    # プロフィールURL自体をノード化（service name → url）。
    whatsmyname_G.add_node(url, type="url")
    whatsmyname_G.add_edge(service.site_name, url, label="profile url")

    if G_ai is None:
      continue

    # kg_gen由来の関係グラフを合流させ、根(入次数0)ノードをURLへぶら下げる。
    whatsmyname_G = nx.compose(whatsmyname_G, G_ai)
    for node in G_ai.nodes():
      if node != url and G_ai.in_degree(node) == 0:
        whatsmyname_G.add_edge(url, node, label="page content")

  return whatsmyname_G
