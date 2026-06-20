from __future__ import annotations

from sqlalchemy import text

from app.agents.base import BaseAgent
from app.core.logging import logger
from app.db.database import engine
from app.schemas.models import TraceEvent
from app.schemas.query_state import QueryState
from app.services.llm_provider import llm


class SQLAnalystAgent(BaseAgent):
    name = "sql_analyst"

    async def execute(self, state: QueryState) -> tuple[QueryState, TraceEvent]:
        query = state.rewritten_query or state.query
        logger.info(f"SQL Analyst Agent translating query: {query}")

        schema = """
        CREATE TABLE documents (
            id VARCHAR PRIMARY KEY,
            filename VARCHAR,
            content_type VARCHAR,
            file_path VARCHAR,
            status VARCHAR,
            created_at DATETIME
        );
        """
        prompt = (
            f"Given the following SQLite schema:\n{schema}\n"
            f"Write a SELECT statement to answer the user query: '{query}'.\n"
            "RETURN ONLY THE SQL STATEMENT NO MARKDOWN."
        )
        sql = await llm.generate("You output raw SQL only.", prompt)
        sql = sql.replace("```sql", "").replace("```", "").strip()

        result_str = ""
        try:
            with engine.connect() as conn:
                res = conn.execute(text(sql)).fetchall()
                result_str = (
                    str([dict(row._mapping) for row in res]) if res else "No results found."
                )
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            result_str = f"Error executing SQL: {e}"

        state.retrieved_candidates = [
            {
                "score": 1.0,
                "metadata": {"document_name": "Database Analytics", "chunk_id": "sql-0", "page": 1},
                "text": f"SQL Query Run: {sql}\nResults: {result_str}",
            }
        ]

        return state, TraceEvent(
            agent=self.name,
            action="execute_sql",
            result=f"Ran query: {sql[:50]}...",
        )
