from typing import List, Optional

from pydantic import BaseModel


class GravatarAccount(BaseModel):
  """Gravatarプロフィールに紐づく外部サービスアカウント1件分。

  `/{hash}.json` の entry[].accounts に含まれる、本人が連携登録した
  SNS等のアカウント情報（必要フィールドのみ抽出）。
  """
  domain: Optional[str] = None      # サービスのドメイン (例: twitter.com)
  display: Optional[str] = None     # 表示名 (例: @username)
  url: Optional[str] = None         # アカウントURL
  username: Optional[str] = None    # アカウント名
  name: Optional[str] = None        # サービス名 (例: Twitter)
  shortname: Optional[str] = None   # サービス短縮名 (例: twitter)


class GravatarUrl(BaseModel):
  """プロフィールに登録された任意のリンク（entry[].urls の1件）。"""
  title: Optional[str] = None       # リンクのタイトル
  value: Optional[str] = None       # リンクURL


class GravatarEntry(BaseModel):
  """Gravatarプロフィール本体（entry配列の1要素、必要フィールドのみ抽出）。"""
  profileUrl: Optional[str] = None            # GravatarプロフィールページURL
  preferredUsername: Optional[str] = None     # 優先ユーザ名
  displayName: Optional[str] = None           # 表示名
  thumbnailUrl: Optional[str] = None          # プロフィール画像URL
  accounts: List[GravatarAccount] = []        # 連携サービスアカウント一覧
  urls: List[GravatarUrl] = []                # 登録リンク一覧


class GravatarResponseModel(BaseModel):
  """`/{hash}.json` のレスポンス（entry配列を保持）。

  メールがGravatarに登録されていれば entry に1件以上入る。
  未登録なら取得側で None を返す（本モデルは生成しない）。
  """
  entry: List[GravatarEntry] = []
