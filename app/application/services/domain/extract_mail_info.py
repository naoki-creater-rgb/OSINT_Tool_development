import asyncio

import networkx as nx
from kg_gen.models import Graph

from app.application.services.domain.attribute_used_service import attribute_used_service
from app.application.services.domain.attribute_name_account import attribute_name_account
from app.application.services.domain.analyze_account_name import search_user_name
from app.application.services.domain.attribute_google_account import attribute_google_account
from app.application.services.domain.attribute_github_account import attribute_github_account
from app.application.services.domain.attribute_gravatar_account import attribute_gravatar_account
from app.application.services.graph.prune import prune_graph


def _graph_or_empty(result, label: str) -> nx.MultiDiGraph:
    """gather(return_exceptions=True)の結果を安全にグラフ化する。

    サブフローが例外を投げても全体を巻き添えにせず、そのフローだけ空グラフ
    として握りつぶす（部分結果 > 全滅）。失敗はログに残す。
    """
    if isinstance(result, Exception):
        print(f"[!] {label} 失敗のためスキップ: {result!r}")
        return nx.MultiDiGraph()
    return result


async def extract_mail_info(
  email: str, follow_wmn_urls: bool = False, follow_gravatar_urls: bool = False
) -> Graph:
  """メールアドレスを起点に各単体フローを並列実行し、それぞれの戻り値である
  Graph(=nx.MultiDiGraph)を「おおもとのemailノード」へ合流させて1つの
  関係グラフにまとめる。

  follow_wmn_urls: WhatsMyNameヒットのプロフィールURLまで追跡し本文をAI抽出
    するか。既定Falseはノード生成のみで高速。Trueは低速だが本文の裏付け付き。
  follow_gravatar_urls: Gravatar連携サービスのアカウントURLまで追跡し本文を
    AI抽出するか。既定Falseはノード生成のみ。Trueは低速だが本人連携=高信頼の
    URL先まで展開する。

  各単体フローは以下（遷移図のメール系/Googleアカウント系）:
    - attribute_used_service : Holehe（利用サービス, 信頼性高）
    - attribute_name_account : WhatsMyName（アカウント名からの利用サービス, 信頼性低）
    - search_user_name       : 検索エンジン（アカウント名の完全一致 → ページ本文AI抽出）
    - attribute_google_account: GHunt（公開Googleアカウント情報）
    - attribute_github_account: GitHub（アカウント + 公開リポジトリ）
    - attribute_gravatar_account: Gravatar（本人連携サービス, 信頼性高・無条件出力）
  """
  # おおもとのノード（全単体グラフが共有するemailノード）
  mail_G = nx.MultiDiGraph()
  mail_G.add_node(email, type="email")

  # 各単体フローを並列実行。いずれもemailノードを根に持つため
  # compose_allで同一emailノード上に合流する。
  # 1つのサブフロー失敗で全体を失わないよう耐障害化（部分結果 > 全滅）。
  used_service_r, name_account_r, user_name_r, google_r, github_r, gravatar_r = await asyncio.gather(
    attribute_used_service(email),
    attribute_name_account(email, follow_service_urls=follow_wmn_urls),
    search_user_name(email),
    attribute_google_account(email),
    attribute_github_account(email),
    attribute_gravatar_account(email, follow_account_urls=follow_gravatar_urls),
    return_exceptions=True,
  )
  used_service_G = _graph_or_empty(used_service_r, "Holehe")
  name_account_G = _graph_or_empty(name_account_r, "WhatsMyName")
  user_name_G = _graph_or_empty(user_name_r, "検索エンジン")
  google_G = _graph_or_empty(google_r, "GHunt")
  github_G = _graph_or_empty(github_r, "GitHub")
  gravatar_G = _graph_or_empty(gravatar_r, "Gravatar")

  # それぞれの戻り値Graphをおおもとのグラフへ結合する。
  mail_G = nx.compose_all(
    [mail_G, used_service_G, name_account_G, user_name_G, google_G, github_G, gravatar_G]
  )

  # search_user_name だけはアカウント名(@より前)を根とするため、
  # おおもとのemailノードへ明示的に接続してグラフを連結させる。
  account_name = email.split("@")[0]
  if account_name in mail_G:
    mail_G.add_edge(email, account_name, label="account name")

  # ハブフィルタ: 検索経由のAI由来ノイズを間引く（構造化ノードは常に残す）。
  # 島が出たらおおもと(email)へ再接続して連結成分1を保つ。
  mail_G = prune_graph(mail_G, anchor=email)

  return mail_G
