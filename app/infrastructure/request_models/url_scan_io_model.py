from pydantic import BaseModel
from typing import Optional

# ---urlscan.ioから返却されるJSONモデルの定義（解析結果のURLが返却される）---
class UrlScanIoUrlModel(BaseModel):
    message: str
    uuid: str
    api: str
    visibility: str

# ---ページ基本情報---
class UrlScanPageMetaData(BaseModel):
    url: Optional[str] = None #調査したURL
    title: Optional[str] = None #ページタイトル
    domain: Optional[str] = None #調査ドメイン名（後続のWhoIs/VirusTotalの鍵）
    apexDomain: Optional[str] = None #登録ドメイン（サブドメインを除いたapex。WhoIs向き）
    ip: Optional[str] = None #調査ドメインのIPアドレス
    country: Optional[str] = None #ドメインが所属する国コード

# ---ネットワーク通信履歴 ---
# 実データの階層: data.requests[i].request.request.url (request が二重ネスト)
class UrlScanRequestDetail(BaseModel):
    url: Optional[str] = None #通信が発生したURL

class UrlScanRequestInfo(BaseModel):
    request: Optional[UrlScanRequestDetail] = None #内側の request（url を保持）

class UrlScanNetworkTransaction(BaseModel):
    request: Optional[UrlScanRequestInfo] = None #外側の request

class UrlScanDataContainer(BaseModel):
    requests: list[UrlScanNetworkTransaction] = []

# ---ルートモデル（スキャン完了時に返却される解析結果）---
# 注: 未完了時(HTTP 404)は {message, status, errors} という別形状のため
#     このモデルは完了(HTTP 200)のレスポンスにのみ適用する。
#     404/200 の判定は本文の status ではなく HTTP ステータスコードで行う。
class UrlScanResponseRoot(BaseModel):
    page: UrlScanPageMetaData
    data: UrlScanDataContainer