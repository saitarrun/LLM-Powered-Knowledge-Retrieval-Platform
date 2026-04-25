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
        graph = await self.get_topology_with_health()
        return {"nodes": graph["nodes"], "links": graph["links"]}

    def _empty_graph(self, status: str, neo4j_available: bool, errors: list[str] | None = None):
        return {
            "nodes": [],
            "links": [],
            "health": {
                "status": status,
                "neo4j_available": neo4j_available,
                "node_count": 0,
                "relationship_count": 0,
                "document_count": 0,
                "chunk_count": 0,
                "entity_count": 0,
                "disconnected_document_count": 0,
                "partial_extraction": False,
                "errors": errors or [],
            },
        }

    async def get_topology_with_health(self):
        nodes: list[dict] = []
        links: list[dict] = []
        node_ids: set[str] = set()
        errors: list[str] = []

        async with self.driver.session() as session:
            try:
                connectivity = await session.run("RETURN 1 AS ok")
                await connectivity.consume()

                result = await session.run(
                    """
                    MATCH (n)-[r]->(m)
                    RETURN labels(n) AS source_labels,
                           coalesce(n.id, n.name, elementId(n)) AS source_id,
                           coalesce(n.filename, n.title, n.id, elementId(n)) AS source_label,
                           type(r) AS type,
                           labels(m) AS target_labels,
                           coalesce(m.id, m.name, elementId(m)) AS target_id,
                           coalesce(m.filename, m.title, m.id, elementId(m)) AS target_label
                    LIMIT 300
                    """
                )
                async for record in result:
                    source = str(record["source_id"])
                    target = str(record["target_id"])
                    rel_type = record["type"]

                    if source not in node_ids:
                        source_type = self._node_type(record["source_labels"])
                        nodes.append({
                            "id": source,
                            "label": record["source_label"] or source,
                            "type": source_type,
                            "group": source_type,
                        })
                        node_ids.add(source)
                    if target not in node_ids:
                        target_type = self._node_type(record["target_labels"])
                        nodes.append({
                            "id": target,
                            "label": record["target_label"] or target,
                            "type": target_type,
                            "group": target_type,
                        })
                        node_ids.add(target)

                    links.append({
                        "source": source,
                        "target": target,
                        "type": rel_type
                    })

                isolated_documents = await session.run(
                    """
                    MATCH (d:Document)
                    WHERE NOT (d)--()
                    RETURN coalesce(d.id, elementId(d)) AS id,
                           coalesce(d.filename, d.title, d.id, elementId(d)) AS label
                    LIMIT 100
                    """
                )
                async for record in isolated_documents:
                    document_id = str(record["id"])
                    if document_id in node_ids:
                        continue
                    nodes.append({
                        "id": document_id,
                        "label": record["label"] or document_id,
                        "type": "document",
                        "group": "document",
                        "connected": False,
                    })
                    node_ids.add(document_id)
            except Exception as e:
                logger.error(f"Failed to fetch full graph: {e}")
                return self._empty_graph("unavailable", False, ["Neo4j unavailable"])

        counts = self._count_nodes(nodes)
        partial_extraction = bool(nodes) and (counts["document_count"] == 0 or counts["entity_count"] == 0)
        status = "empty"
        if nodes:
            status = "partial" if partial_extraction else "healthy"

        return {
            "nodes": nodes,
            "links": links,
            "health": {
                "status": status,
                "neo4j_available": True,
                "node_count": len(nodes),
                "relationship_count": len(links),
                "document_count": counts["document_count"],
                "chunk_count": counts["chunk_count"],
                "entity_count": counts["entity_count"],
                "disconnected_document_count": counts["disconnected_document_count"],
                "partial_extraction": partial_extraction,
                "errors": errors,
            },
        }

    def _node_type(self, labels):
        normalized = {str(label).lower() for label in labels or []}
        if "document" in normalized:
            return "document"
        if "documentchunk" in normalized or "chunk" in normalized:
            return "chunk"
        if "relationship" in normalized:
            return "relationship"
        return "entity"

    def _count_nodes(self, nodes: list[dict]):
        document_count = sum(1 for node in nodes if node.get("type") == "document")
        chunk_count = sum(1 for node in nodes if node.get("type") == "chunk")
        entity_count = sum(1 for node in nodes if node.get("type") == "entity")
        disconnected_document_count = sum(
            1 for node in nodes
            if node.get("type") == "document" and not node.get("connected", True)
        )
        return {
            "document_count": document_count,
            "chunk_count": chunk_count,
            "entity_count": entity_count,
            "disconnected_document_count": disconnected_document_count,
        }

    async def close(self):
        await self.driver.close()

graph_extractor = GraphExtractor()
