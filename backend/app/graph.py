from neo4j import GraphDatabase

NEO4J_URI = "bolt://neo4j:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def init_graph():
    with driver.session() as session:
        session.execute_write(_create_constraints)
        session.execute_write(_seed_graph)


def _create_constraints(tx):
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Case) REQUIRE c.name IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (l:Law) REQUIRE l.code IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (j:Judge) REQUIRE j.name IS UNIQUE")


def _seed_graph(tx):
    tx.run(
        """
        MERGE (c:Case {name: $case_name, summary: $case_summary})
        MERGE (l:Law {code: $law_code, description: $law_description})
        MERGE (j:Judge {name: $judge_name, court: $judge_court})
        MERGE (c)-[:CITES]->(l)
        MERGE (j)-[:OVERTURNED]->(c)
        """,
        case_name="Data Privacy vs Public Safety",
        case_summary="A dispute over whether privacy protections can be bypassed for national security purposes.",
        law_code="GDPR-101",
        law_description="General data protection requirements for personal data handling.",
        judge_name="Justice A. Roberts",
        judge_court="Federal Supreme Court",
    )


def query_graph(query: str):
    search_text = query.lower()
    with driver.session() as session:
        results = session.run(
            """
            MATCH (n)
            WHERE toLower(coalesce(n.name, '')) CONTAINS $search
               OR toLower(coalesce(n.code, '')) CONTAINS $search
               OR toLower(coalesce(n.description, '')) CONTAINS $search
               OR toLower(coalesce(n.summary, '')) CONTAINS $search
            RETURN labels(n) AS labels, n.name AS name, n.description AS description, n.code AS code, n.summary AS summary
            LIMIT 5
            """,
            search=search_text,
        )
        hits = []
        for record in results:
            labels = ", ".join(record["labels"])
            parts = [f"labels={labels}"]
            if record["name"]:
                parts.append(f"name={record['name']}")
            if record["code"]:
                parts.append(f"code={record['code']}")
            if record["description"]:
                parts.append(f"desc={record['description']}")
            if record["summary"]:
                parts.append(f"summary={record['summary']}")
            hits.append(" | ".join(parts))
        return hits
