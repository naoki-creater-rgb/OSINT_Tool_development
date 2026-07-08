import os

from dotenv import load_dotenv
from kg_gen import KGGen
from kg_gen.models import Graph

load_dotenv()

kg = KGGen(
    model="gemini/gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
)

def relation_generate_from_text(text: str) -> set[tuple[str, str, str]]:
    graph = kg.generate(input_data=text, cluster=True)
    return graph.relations

def graph_from_triples(triples: list[tuple[str, str, str]]) -> set[tuple[str, str, str]]:
    relations = set(triples)
    entities = {s for s, _, _ in triples} | {o for _, _, o in triples}
    edges = {e for _, e, _ in triples}
    
    graph =  Graph(
        entities = entities,
        edges = edges,
        relations = relations
    )
    
    return graph.relations