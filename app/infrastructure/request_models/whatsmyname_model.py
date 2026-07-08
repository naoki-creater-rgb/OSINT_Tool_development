from typing import List, Optional
from pydantic import BaseModel

class WhatsMyNameResponse(BaseModel):
  """
  WhatsMyNameからのレスポンスモデル
  """
  site_name: Optional[str] = None #サービス名
  result_url: Optional[str] = None #チェックに使用したURL
  result_status: Optional[str] = None #レスポンスステータス 200であったらサービス使用と仮定