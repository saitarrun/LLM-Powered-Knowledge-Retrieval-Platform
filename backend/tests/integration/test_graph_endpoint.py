from fastapi.testclient import TestClient

from app.graph.extractor import graph_extractor
from app.main import app


def test_graph_endpoint_returns_health_and_topology(monkeypatch):
    async def fake_graph():
        return {
            "nodes": [
                {"id": "doc-1", "label": "handbook.pdf", "type": "document"},
                {"id": "chunk-1", "label": "Chunk 1", "type": "chunk"},
                {"id": "entity-1", "label": "Policy", "type": "entity"},
            ],
            "links": [
                {"source": "doc-1", "target": "chunk-1", "type": "HAS_CHUNK"},
                {"source": "chunk-1", "target": "entity-1", "type": "MENTIONS"},
            ],
            "health": {
                "status": "healthy",
                "neo4j_available": True,
                "node_count": 3,
                "relationship_count": 2,
                "document_count": 1,
                "chunk_count": 1,
                "entity_count": 1,
                "disconnected_document_count": 0,
                "partial_extraction": False,
                "errors": [],
            },
        }

    monkeypatch.setattr(graph_extractor, "get_topology_with_health", fake_graph)
    client = TestClient(app)

    response = client.get("/api/v1/documents/graph")

    assert response.status_code == 200
    data = response.json()
    assert data["health"]["status"] == "healthy"
    assert data["health"]["neo4j_available"] is True
    assert {node["type"] for node in data["nodes"]} == {"document", "chunk", "entity"}
    assert {link["type"] for link in data["links"]} == {"HAS_CHUNK", "MENTIONS"}


def test_graph_endpoint_handles_neo4j_unavailable(monkeypatch):
    async def unavailable_graph():
        return {
            "nodes": [],
            "links": [],
            "health": {
                "status": "unavailable",
                "neo4j_available": False,
                "node_count": 0,
                "relationship_count": 0,
                "document_count": 0,
                "chunk_count": 0,
                "entity_count": 0,
                "disconnected_document_count": 0,
                "partial_extraction": False,
                "errors": ["Neo4j unavailable"],
            },
        }

    monkeypatch.setattr(graph_extractor, "get_topology_with_health", unavailable_graph)
    client = TestClient(app)

    response = client.get("/api/v1/documents/graph")

    assert response.status_code == 200
    data = response.json()
    assert data["health"]["status"] == "unavailable"
    assert data["health"]["neo4j_available"] is False
    assert "password" not in response.text.lower()
    assert "bolt://" not in response.text
