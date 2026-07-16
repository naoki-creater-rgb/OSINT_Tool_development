import asyncio

import networkx as nx
from kg_gen.models import Graph

from app.infrastructure.clients.gravatar_client import get_gravatar_profile
from app.infrastructure.clients.playwright_client import get_html_with_playwright
from app.infrastructure.request_models.gravatar_model import GravatarResponseModel
from app.application.services.domain.extract_page_content import extract_page_content


async def _follow_account_url(url: str | None) -> nx.MultiDiGraph | None:
  """連携サービスのアカウントURLをPlaywrightで取得し、本文をkg_genで関係グラフ化する。

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


async def attribute_gravatar_account(email: str, follow_account_urls: bool = False) -> Graph:
  """メールからGravatar公開プロフィールを取得し、関係グラフ化する。

  Gravatarは本人が明示的に連携登録したアカウントのみを返す信頼性の高い
  情報源であるため、ヒットした連携サービス(accounts)は検証を挟まず
  「無条件で」ノードとして出力する。

  follow_account_urls:
    False（既定）: 連携サービスのノード生成のみで高速。Playwright取得も
                   kg_gen（ローカルLLM）抽出も行わない。
    True         : さらに各アカウントURLをPlaywrightで取得し、本文を
                   kg_genで関係グラフ化してぶら下げる深掘りモード（低速）。
                   本人連携=高信頼URLなので追跡結果のノイズは少ない。
  """
  gravatar_G = nx.MultiDiGraph()
  gravatar_G.add_node(email, type="email")

  result: GravatarResponseModel | None = await get_gravatar_profile(email)
  if result is None or not result.entry:
    return gravatar_G

  # メール1件に対しentryは通常1件。将来の複数返却にも備えて全件走査する。
  for entry in result.entry:
    # Gravatarプロフィール自体をノード化し、emailに接続する。
    if entry.profileUrl:
      gravatar_G.add_node(
        entry.profileUrl,
        type="gravatar_profile",
        display_name=entry.displayName or "",
        username=entry.preferredUsername or "",
        thumbnail=entry.thumbnailUrl or "",
      )
      gravatar_G.add_edge(email, entry.profileUrl, label="gravatar profile")
    # profileUrlが無い場合でも連携サービスをemailへ直接ぶら下げるため、
    # 以降のエッジ起点をここで決めておく。
    anchor = entry.profileUrl or email

    # 深掘り指定時のみ、各アカウントURLをPlaywright取得→kg_genで関係グラフ化。
    # 既定では取得・LLM抽出を一切行わずノード生成のみで高速に済ませる。
    if follow_account_urls:
      ai_graphs = await asyncio.gather(
        *(_follow_account_url(account.url) for account in entry.accounts)
      )
    else:
      ai_graphs = [None] * len(entry.accounts)

    # 連携サービスアカウント: Gravatarでマッチした=本人連携なので無条件で出力。
    for account, G_ai in zip(entry.accounts, ai_graphs):
      # ノードIDはURLを優先（一意）。無ければサービス名+アカウント名で代替。
      node_id = account.url or f"{account.name or account.shortname}:{account.username}"
      if not node_id:
        continue
      gravatar_G.add_node(
        node_id,
        type="gravatar_account",
        service=account.name or account.shortname or account.domain or "",
        username=account.username or "",
        display=account.display or "",
      )
      gravatar_G.add_edge(anchor, node_id, label="linked account")

      if G_ai is None:
        continue

      # kg_gen由来の関係グラフを合流させ、根(入次数0)ノードをアカウントへぶら下げる。
      gravatar_G = nx.compose(gravatar_G, G_ai)
      # 追跡できたのは本人連携=高信頼リンクなので、配下のAI抽出ノードは
      # prune の関係数フィルタで間引かれないよう type を付与して残す
      # （WMNの低信頼ヒットと違い、ここは表示を増やしてよい）。
      for node in G_ai.nodes():
        if gravatar_G.nodes[node].get("type") is None:
          gravatar_G.nodes[node]["type"] = "gravatar_detail"
        if node != node_id and G_ai.in_degree(node) == 0:
          gravatar_G.add_edge(node_id, node, label="page content")

    # プロフィールに登録された任意リンクも同様に無条件で出力する。
    for link in entry.urls:
      if not link.value:
        continue
      gravatar_G.add_node(
        link.value,
        type="gravatar_url",
        title=link.title or "",
      )
      gravatar_G.add_edge(anchor, link.value, label="linked url")

  return gravatar_G
