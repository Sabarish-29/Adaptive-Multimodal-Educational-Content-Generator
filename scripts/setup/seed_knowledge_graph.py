"""
NeuroSync AI – Seed Knowledge Graph

Populates Neo4j with a starter set of concepts, skills, topics,
and prerequisite relationships for demo / development purposes.

Usage:
    python scripts/setup/seed_knowledge_graph.py [--neo4j-uri URI]
"""

import argparse
import asyncio
import os


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

TOPICS = [
    {"id": "math", "name": "Mathematics", "description": "Core mathematics concepts"},
    {"id": "cs", "name": "Computer Science", "description": "Programming and CS fundamentals"},
    {"id": "physics", "name": "Physics", "description": "Classical and modern physics"},
]

CONCEPTS = [
    # Math
    {"id": "algebra_basics", "name": "Algebra Basics", "topic": "math", "difficulty": 0.2},
    {"id": "linear_equations", "name": "Linear Equations", "topic": "math", "difficulty": 0.3},
    {"id": "quadratic_equations", "name": "Quadratic Equations", "topic": "math", "difficulty": 0.5},
    {"id": "functions", "name": "Functions", "topic": "math", "difficulty": 0.4},
    {"id": "calculus_intro", "name": "Introduction to Calculus", "topic": "math", "difficulty": 0.6},
    {"id": "derivatives", "name": "Derivatives", "topic": "math", "difficulty": 0.7},
    {"id": "integrals", "name": "Integrals", "topic": "math", "difficulty": 0.75},
    # CS
    {"id": "variables", "name": "Variables & Data Types", "topic": "cs", "difficulty": 0.1},
    {"id": "control_flow", "name": "Control Flow", "topic": "cs", "difficulty": 0.2},
    {"id": "loops", "name": "Loops", "topic": "cs", "difficulty": 0.25},
    {"id": "functions_prog", "name": "Functions (Programming)", "topic": "cs", "difficulty": 0.3},
    {"id": "recursion", "name": "Recursion", "topic": "cs", "difficulty": 0.5},
    {"id": "data_structures", "name": "Data Structures", "topic": "cs", "difficulty": 0.5},
    {"id": "algorithms", "name": "Algorithms", "topic": "cs", "difficulty": 0.6},
    # Physics
    {"id": "kinematics", "name": "Kinematics", "topic": "physics", "difficulty": 0.3},
    {"id": "newtons_laws", "name": "Newton's Laws", "topic": "physics", "difficulty": 0.4},
    {"id": "energy", "name": "Energy & Work", "topic": "physics", "difficulty": 0.5},
    {"id": "waves", "name": "Waves", "topic": "physics", "difficulty": 0.5},
]

# (from_id, to_id) meaning from_id is a prerequisite of to_id
PREREQUISITES = [
    # Math chain
    ("algebra_basics", "linear_equations"),
    ("algebra_basics", "quadratic_equations"),
    ("linear_equations", "functions"),
    ("quadratic_equations", "functions"),
    ("functions", "calculus_intro"),
    ("calculus_intro", "derivatives"),
    ("derivatives", "integrals"),
    # CS chain
    ("variables", "control_flow"),
    ("control_flow", "loops"),
    ("loops", "functions_prog"),
    ("functions_prog", "recursion"),
    ("functions_prog", "data_structures"),
    ("data_structures", "algorithms"),
    # Physics chain
    ("kinematics", "newtons_laws"),
    ("newtons_laws", "energy"),
    ("kinematics", "waves"),
    # Cross-domain
    ("algebra_basics", "kinematics"),
    ("calculus_intro", "newtons_laws"),
    ("functions_prog", "algorithms"),
]


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------

async def seed(uri: str, user: str, password: str):
    try:
        from neo4j import AsyncGraphDatabase
    except ImportError:
        print("neo4j driver not installed – run: pip install neo4j")
        return

    print(f"Connecting to {uri} …")
    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    async with driver.session() as session:
        # Topics
        for t in TOPICS:
            await session.run(
                "MERGE (t:Topic {id: $id}) SET t.name = $name, t.description = $desc",
                id=t["id"], name=t["name"], desc=t["description"],
            )
        print(f"  ✓ {len(TOPICS)} topics")

        # Concepts
        for c in CONCEPTS:
            await session.run(
                """
                MERGE (c:Concept {id: $id})
                SET c.name = $name, c.difficulty = $difficulty
                WITH c
                MATCH (t:Topic {id: $topic})
                MERGE (c)-[:BELONGS_TO]->(t)
                """,
                id=c["id"], name=c["name"], difficulty=c["difficulty"], topic=c["topic"],
            )
        print(f"  ✓ {len(CONCEPTS)} concepts")

        # Prerequisites
        for src, dst in PREREQUISITES:
            await session.run(
                """
                MATCH (a:Concept {id: $src}), (b:Concept {id: $dst})
                MERGE (a)-[:PREREQUISITE_OF]->(b)
                """,
                src=src, dst=dst,
            )
        print(f"  ✓ {len(PREREQUISITES)} prerequisite edges")

    await driver.close()
    print("\n✅ Knowledge graph seeded.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(description="Seed NeuroSync knowledge graph")
    parser.add_argument("--neo4j-uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    parser.add_argument("--neo4j-user", default=os.getenv("NEO4J_USER", "neo4j"))
    parser.add_argument("--neo4j-password", default=os.getenv("NEO4J_PASSWORD", "neurosync_kg"))
    args = parser.parse_args()

    await seed(args.neo4j_uri, args.neo4j_user, args.neo4j_password)


if __name__ == "__main__":
    asyncio.run(main())
