from pydantic import BaseModel

class NodeModel(BaseModel):
  id: str #ノードID
  label: str #ノードの名前
  group: str = None #ノードメタ情報（任意）
  size: int #ノードの表示サイズ
  
class LinkModel(BaseModel):
  source: str #エッジ元
  target: str #エッジ先
  label: str #エッジの関係
  
class SendGraphModel(BaseModel):
  nades: list[NodeModel]
  links: list[LinkModel]