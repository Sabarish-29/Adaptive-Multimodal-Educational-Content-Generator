"""
NeuroSync AI – Database Initialisation Script

Creates MongoDB collections with indexes and Neo4j constraints/indexes
for all agent services.

Usage:
    python scripts/setup/init_databases.py [--mongo-url URL] [--neo4j-uri URI]
"""

import argparse
import asyncio
import os
import sys


# ---------------------------------------------------------------------------
# MongoDB setup
# ---------------------------------------------------------------------------

async def init_mongodb(mongo_url: str, db_name: str = "neurosync"):
    """Create collections and indexes in MongoDB."""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
    except ImportError:
        print("motor not installed – skipping MongoDB init")
        return

    print(f"[MongoDB] Connecting to {mongo_url} …")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    collections = {
        # Agent-related
        "cognitive_states": [
            {"keys": [("session_id", 1)], "unique": False},
            {"keys": [("student_id", 1), ("timestamp", -1)], "unique": False},
        ],
        "interventions": [
            {"keys": [("session_id", 1)], "unique": False},
            {"keys": [("student_id", 1), ("created_at", -1)], "unique": False},
        ],
        "content_cache": [
            {"keys": [("concept_id", 1), ("modality", 1)], "unique": False},
            {"keys": [("created_at", 1)], "expireAfterSeconds": 86400},
        ],
        "skill_snapshots": [
            {"keys": [("student_id", 1)], "unique": False},
            {"keys": [("updated_at", -1)], "unique": False},
        ],
        "peer_profiles": [
            {"keys": [("student_id", 1)], "unique": True},
        ],
        "peer_groups": [
            {"keys": [("group_id", 1)], "unique": True},
        ],
        # Legacy
        "profiles": [
            {"keys": [("user_id", 1)], "unique": True},
        ],
        "sessions": [
            {"keys": [("session_id", 1)], "unique": True},
            {"keys": [("user_id", 1), ("created_at", -1)], "unique": False},
        ],
    }

    for coll_name, indexes in collections.items():
        coll = db[coll_name]
        for idx in indexes:
            expire = idx.get("expireAfterSeconds")
            kwargs = {"unique": idx.get("unique", False)}
            if expire is not None:
                kwargs["expireAfterSeconds"] = expire
            await coll.create_index(idx["keys"], **kwargs)
            print(f"  ✓ {coll_name} – index on {idx['keys']}")

    print(f"[MongoDB] Initialised {len(collections)} collections in '{db_name}'")
    client.close()


# ---------------------------------------------------------------------------
# Neo4j setup
# ---------------------------------------------------------------------------

async def init_neo4j(uri: str, user: str, password: str):
    """Create constraints and indexes in Neo4j."""
    try:
        from neo4j import AsyncGraphDatabase
    except ImportError:
        print("neo4j driver not installed – skipping Neo4j init")
        return

    print(f"[Neo4j] Connecting to {uri} …")
    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    constraints = [
        "CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT skill_id IF NOT EXISTS FOR (s:Skill) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT topic_id IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE",
        "CREATE CONSTRAINT student_id IF NOT EXISTS FOR (st:Student) REQUIRE st.id IS UNIQUE",
    ]

    indexes = [
        "CREATE INDEX concept_name IF NOT EXISTS FOR (c:Concept) ON (c.name)",
        "CREATE INDEX skill_name IF NOT EXISTS FOR (s:Skill) ON (s.name)",
        "CREATE INDEX topic_name IF NOT EXISTS FOR (t:Topic) ON (t.name)",
    ]

    async with driver.session() as session:
        for stmt in constraints + indexes:
            try:
                await session.run(stmt)
                label = "constraint" if "CONSTRAINT" in stmt else "index"
                print(f"  ✓ {label}: {stmt.split('IF NOT EXISTS')[0].strip()}")
            except Exception as e:
                print(f"  ⚠ {stmt[:60]}… – {e}")

    await driver.close()
    print("[Neo4j] Schema initialised")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(description="Initialise NeuroSync databases")
    parser.add_argument("--mongo-url", default=os.getenv("MONGO_URL", "mongodb://localhost:27017"))
    parser.add_argument("--mongo-db", default=os.getenv("MONGO_DB", "neurosync"))
    parser.add_argument("--neo4j-uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    parser.add_argument("--neo4j-user", default=os.getenv("NEO4J_USER", "neo4j"))
    parser.add_argument("--neo4j-password", default=os.getenv("NEO4J_PASSWORD", "neurosync_kg"))
    args = parser.parse_args()

    await init_mongodb(args.mongo_url, args.mongo_db)
    await init_neo4j(args.neo4j_uri, args.neo4j_user, args.neo4j_password)
    print("\n✅ All databases initialised.")


if __name__ == "__main__":
    asyncio.run(main())
