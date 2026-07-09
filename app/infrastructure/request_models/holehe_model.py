from typing import List, Optional
from pydantic import BaseModel

class HoleheResponseModel(BaseModel):
  """Holeheのリクエストを取得するモデル"""
  name: Optional[str] = None #使用サービス名
  exists: Optional[bool] = None #サービス使用有無
  emailrecovery: Optional[str] = None #アカウント回復に使用するメールアドレス