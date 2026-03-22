import os
import json
from neo4j import AsyncGraphDatabase
from app.services.llm_provider import llm
from app.core.config import settings
from app.core.logging import logger

neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

class GraphExtractor:
    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    async def extract_and_store(self, text: str, source_id: str):
        if not llm.client: return # Skip if no API key
        prompt = f"""
        Extract knowledge graph triples from the text. 
        Return ONLY a JSON list of dictionaries with keys "head", "type", "tail".
        Do not include any other markdown or text.
        Text: {text}
        """
        response = await llm.generate("You are a data extraction bot. Output only valid JSON.", prompt)
        
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            triples = json.loads(response.strip())
        except Exception as e:
            logger.error(f"Failed to parse graph triples: {e}")
            return
            
        async with self.driver.session() as session:
            for t in triples:
                head = t.get("head")
                rel = t.get("type", "RELATED_TO")
                tail = t.get("tail")
                if head and rel and tail:
                    rel_type = "".join(e for e in rel.upper().replace(" ", "_").replace("-", "_") if e.isalnum() or e == "_")
                    if not rel_type: rel_type = "RELATED_TO"
                    query = f'''
                    MERGE (h:Entity {{id: $head}})
                    MERGE (t:Entity {{id: $tail}})
                    MERGE (h)-[r:`{rel_type}`]->(t)
                    SET r.source_id = $source_id
                    '''
                    try:
                        await session.run(query, head=head[:100], tail=tail[:100], source_id=source_id)
                    except Exception as e:
                        logger.warning(f"Neo4j merge error: {e}")
        
    async def query_graph(self, query: str):
        if not llm.client: return []
        prompt = f"Extract the main subject entity from this query: '{query}'. Return ONLY the entity string, nothing else."
        entity = await llm.generate("You extract single noun subjects from queries.", prompt)
        entity = entity.strip().strip("'").strip('"')
        
        results = []
        async with self.driver.session() as session:
            try:
                # Basic context expansion around the entity
                res = await session.run(
                    "MATCH (e:Entity)-[r]-(t) WHERE toLower(e.id) CONTAINS toLower($ent) RETURN e.id, type(r), t.id LIMIT 10",
                    ent=entity
                )
                async for record in res:
                    results.append(f"{record['e.id']} {record['type(r)']} {record['t.id']}")
            except Exception as e:
                logger.error(f"Graph query error: {e}")
        return results

    async def get_full_graph(self):
        nodes = []
        links = []
        node_ids = set()
        
        async with self.driver.session() as session:
            try:
                # Get all entities and relationships
                result = await session.run(
                    "MATCH (n:Entity)-[r]->(m:Entity) RETURN n.id as source, type(r) as type, m.id as target LIMIT 200"
                )
                async for record in result:
                    source = record["source"]
                    target = record["target"]
                    rel_type = record["type"]
                    
                    if source not in node_ids:
                        nodes.append({"id": source, "label": source, "group": 1})
                        node_ids.add(source)
                    if target not in node_ids:
                        nodes.append({"id": target, "label": target, "group": 2})
                        node_ids.add(target)
                        
                    links.append({
                        "source": source,
                        "target": target,
                        "type": rel_type
                    })
            except Exception as e:
                logger.error(f"Failed to fetch full graph: {e}")
                
        return {"nodes": nodes, "links": links}

    async def close(self):
        await self.driver.close()

graph_extractor = GraphExtractor()
