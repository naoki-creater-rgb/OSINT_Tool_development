import hashlib
import json
import re

import httpx

from app.infrastructure.request_models.gravatar_model import (
  GravatarResponseModel,
  GravatarUrl,
)

# Gravatarの公開プロフィールAPI。メールのMD5ハッシュを鍵に照会する。
GRAVATAR_PROFILE_URL = "https://gravatar.com/{hash}.json"

# HTMLプロフィールページに埋め込まれる schema.org(JSON-LD) を拾う正規表現。
_LD_JSON_RE = re.compile(
  r'<script type="application/ld\+json">(.*?)</script>', re.S
)


def _email_hash(email: str) -> str:
  """Gravatar仕様のメールハッシュ（前後空白除去 + 小文字化 → MD5）を返す。"""
  normalized = email.strip().lower().encode("utf-8")
  return hashlib.md5(normalized).hexdigest()


async def _fetch_profile_links(profile_url: str) -> list[GravatarUrl]:
  """HTMLプロフィールページから拡張リンク(sameAs)を取得する。

  `/{hash}.json` は現在 urls(拡張リンク) を返さなくなっており、本人が
  プロフィールに登録した外部リンクはHTMLの JSON-LD(schema.org Person)の
  `sameAs` 配列にのみ残っている。ページはサーバ側レンダリングで初期HTMLに
  ld+jsonが含まれるため、httpx取得で足りる（Playwright不要）。
  取得失敗・リンク無しは空リストを返す（拡張リンク無しとして扱う）。
  """
  try:
    async with httpx.AsyncClient(follow_redirects=True) as client:
      response = await client.get(
        profile_url, headers={"User-Agent": "Mozilla/5.0"}
      )
    response.raise_for_status()
  except httpx.HTTPError as e:
    print(f"[!] Gravatar拡張リンク取得失敗のためスキップ: {profile_url} ({e})")
    return []

  match = _LD_JSON_RE.search(response.text)
  if not match:
    return []
  try:
    ld = json.loads(match.group(1))
  except json.JSONDecodeError:
    return []

  same_as = ld.get("sameAs")
  if isinstance(same_as, str):  # 単一リンクは文字列で来る場合がある
    same_as = [same_as]
  if not isinstance(same_as, list):
    return []

  return [GravatarUrl(value=url) for url in same_as if isinstance(url, str) and url]


async def get_gravatar_profile(email: str) -> GravatarResponseModel | None:
  """メールのハッシュからGravatar公開プロフィールを取得する。

  登録済みなら GravatarResponseModel を、未登録(404)や取得失敗なら
  None を返す。パース/構造化はサービス層で行う。
  """
  url = GRAVATAR_PROFILE_URL.format(hash=_email_hash(email))
  # UA未指定だとGravatar側が弾く場合があるため明示する。
  headers = {"User-Agent": "OSINT-tool/1.0"}

  async with httpx.AsyncClient() as client:
    response = await client.get(url, headers=headers)

  # 未登録メールは404。ここで例外にせず「該当なし」として扱う。
  if response.status_code == 404:
    return None
  response.raise_for_status()

  model = GravatarResponseModel.model_validate(response.json())

  # `.json` は拡張リンク(urls)を返さなくなったため、空のときだけHTML
  # プロフィールの JSON-LD(sameAs) から補完する（既存の urls があれば尊重）。
  for entry in model.entry:
    if not entry.urls and entry.profileUrl:
      entry.urls = await _fetch_profile_links(entry.profileUrl)

  return model
