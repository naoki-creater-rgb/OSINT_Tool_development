from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict, Field
class AnalysisId(BaseModel):
  """
  VirusTotalの解析結果IDを返却
  """
  id: Optional[str] = None

class VirusTotalFirstResponse(BaseModel):
  """POST /urls のレスポンス"""
  data: Optional[AnalysisId]


class ThreatContext(BaseModel):
  """crowdsourced_context の1件。detail が解説本文（kg-gen の入力になる）"""
  model_config = ConfigDict(populate_by_name=True)

  detail: Optional[str] = Field(default=None, alias="details")  # 脅威の解説テキスト
  title: Optional[str] = None     # 見出し
  source: Optional[str] = None    # 提供元
  severity: Optional[str] = None  # 深刻度


class LastAnalysisStats(BaseModel):
  """カテゴリごとの検出数。malicious 判定などに使う"""
  malicious: int = 0
  suspicious: int = 0
  undetected: int = 0
  harmless: int = 0
  timeout: int = 0


class UrlAttributes(BaseModel):
  """GET /urls/{id}（URLオブジェクト）の attributes。malicious 判定と解説を持つ"""
  last_analysis_stats: Optional[LastAnalysisStats] = None
  crowdsourced_context: List[ThreatContext] = [] #分析コメント,kg-genに最終的に渡す


class UrlData(BaseModel):
  id: Optional[str] = None    # オブジェクトの識別子
  type: Optional[str] = None  # オブジェクトのタイプ（"url"）
  attributes: UrlAttributes


class VirusTotalResponse(BaseModel):
  """GET /urls/{id}（URLオブジェクト）のレスポンス。最終的にこれを返す"""
  data: UrlData

class AnalysisAttributes(BaseModel):
  status: Optional[str] = None    # queued / in-progress / completed


class AnalysisData(BaseModel):
  attributes: AnalysisAttributes


class UrlInfo(BaseModel):
  """meta.url_info。id は URLオブジェクト取得（GET /urls/{id}）に使う"""
  id: Optional[str] = None
  url: Optional[str] = None


class VirusTotalMeta(BaseModel):
  url_info: Optional[UrlInfo] = None


class VirusTotalAnalysisResponse(BaseModel):
  """GET /analyses/{id} のレスポンス。status で完了を判定し meta.url_info.id を得る"""
  data: AnalysisData
  meta: Optional[VirusTotalMeta] = None
