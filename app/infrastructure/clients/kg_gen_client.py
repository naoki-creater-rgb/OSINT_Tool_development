import os

from dotenv import load_dotenv
from kg_gen import KGGen
from kg_gen.models import Graph

load_dotenv()

# ローカルLLM(Ollama)を利用。APIキー不要・完全無料・日次制限なし。
# 環境変数で切り替え可能: OLLAMA_MODEL / OLLAMA_API_BASE
kg = KGGen(
    model=os.getenv("OLLAMA_MODEL", "ollama_chat/qwen2.5:3b"),
    api_base=os.getenv("OLLAMA_API_BASE", "http://localhost:11434"),
)

def relation_generate_from_text(text: str) -> Graph:
    # cluster=False: 小型ローカルLLMだとクラスタリングが過剰にノードを潰すため無効化。
    # 抽出精度が保たれ、クラスタリング分の呼び出しが減り高速化もする。
    graph = kg.generate(input_data=text, cluster=False)
    return graph

def graph_from_tuples(triples: list[tuple[str, str, str]]) -> Graph:
    relations = set(triples)
    entities = {s for s, _, _ in triples} | {o for _, _, o in triples}
    edges = {e for _, e, _ in triples}
    
    graph =  Graph(
        entities = entities,
        edges = edges,
        relations = relations
    )
    
    return graph