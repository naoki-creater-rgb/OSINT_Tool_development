import networkx as nx
from kg_gen.models import Graph

from app.infrastructure.clients.ghunt_client import ghunt_response
from app.infrastructure.request_models.ghunt_model import GHuntResponse

async def attribute_google_account(email: str) -> Graph:
  """メールから GHunt で公開Googleアカウント情報を収集し、関係グラフ化する。"""
  ghunt_G = nx.MultiDiGraph()
  ghunt_G.add_node(email, type="email")

  result: GHuntResponse | None = await ghunt_response(email)
  if result is None:
    return ghunt_G

  # gaia_id（Google内部の固有ID）
  if result.gaia_id:
    ghunt_G.add_node(result.gaia_id, type="gaia_id")
    ghunt_G.add_edge(email, result.gaia_id, label="gaia id")

  # プロフィール（名前・写真）
  if result.profile:
    if result.profile.name:
      ghunt_G.add_node(result.profile.name, type="account_name")
      ghunt_G.add_edge(email, result.profile.name, label="name")

    photo = result.profile.profile_photo
    if photo and photo.url and not photo.is_default:
      ghunt_G.add_node(photo.url, type="profile_photo")
      ghunt_G.add_edge(email, photo.url, label="profile photo")

  # 各Googleサービス
  services = result.services
  if services:
    # Calendar（公開予定名）
    if services.calendar:
      for event in services.calendar.events:
        if event.summary:
          ghunt_G.add_node(event.summary, type="calendar_event")
          ghunt_G.add_edge(email, event.summary, label="calendar event")

    # Maps（レビューした店名）
    if services.maps:
      for review in services.maps.reviews:
        if review.store_name:
          ghunt_G.add_node(review.store_name, type="maps_review")
          ghunt_G.add_edge(email, review.store_name, label="maps review")

    # Play Games（プレイしたゲーム）
    if services.play_games:
      for game in services.play_games.games:
        if game.title:
          ghunt_G.add_node(game.title, type="play_game")
          ghunt_G.add_edge(email, game.title, label="play game")

  return ghunt_G
