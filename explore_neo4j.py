"""
Explore existing Neo4j structure for StoryOS
"""
from neo4j import GraphDatabase
import json

# Connection details
NEO4J_URI = "neo4j+s://REDACTED_HOST"
NEO4J_USER = "neo4j"
NEO4J_PASS = "REDACTED"
NEO4J_DATABASE = "neo4j"

def explore_database():
    """Connect and explore the Neo4j database structure"""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

    with driver.session(database=NEO4J_DATABASE) as session:
        print("=" * 80)
        print("NEO4J DATABASE EXPLORATION")
        print("=" * 80)

        # 1. Get all node labels
        print("\n📦 NODE LABELS:")
        print("-" * 80)
        result = session.run("CALL db.labels()")
        labels = [record["label"] for record in result]
        for label in labels:
            print(f"  • {label}")

        # 2. Get all relationship types
        print("\n🔗 RELATIONSHIP TYPES:")
        print("-" * 80)
        result = session.run("CALL db.relationshipTypes()")
        rel_types = [record["relationshipType"] for record in result]
        for rel_type in rel_types:
            print(f"  • {rel_type}")

        # 3. Count nodes by label
        print("\n📊 NODE COUNTS:")
        print("-" * 80)
        for label in labels:
            # Skip CSV import labels (they contain dots which break Cypher syntax)
            if '.csv' in label:
                continue
            result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
            count = result.single()["count"]
            print(f"  {label}: {count} nodes")

        # 4. Sample nodes from each label (first 2)
        print("\n🔍 SAMPLE NODES:")
        print("-" * 80)
        for label in labels:
            # Skip CSV import labels
            if '.csv' in label:
                continue
            print(f"\n  {label}:")
            result = session.run(f"MATCH (n:{label}) RETURN n LIMIT 2")
            for i, record in enumerate(result, 1):
                node = record["n"]
                print(f"    Node {i}:")
                print(f"      Properties: {dict(node)}")

        # 5. Sample relationships
        print("\n🔗 SAMPLE RELATIONSHIPS:")
        print("-" * 80)
        for rel_type in rel_types[:5]:  # Show first 5 relationship types
            print(f"\n  {rel_type}:")
            result = session.run(
                f"MATCH (a)-[r:{rel_type}]->(b) "
                f"RETURN labels(a)[0] as from_label, labels(b)[0] as to_label, "
                f"properties(r) as props LIMIT 2"
            )
            for i, record in enumerate(result, 1):
                print(f"    Relationship {i}:")
                print(f"      From: {record['from_label']}")
                print(f"      To: {record['to_label']}")
                print(f"      Properties: {record['props']}")

        # 6. Get schema visualization (relationship patterns)
        print("\n🗺️  SCHEMA PATTERNS:")
        print("-" * 80)
        result = session.run("""
            MATCH (a)-[r]->(b)
            RETURN DISTINCT labels(a)[0] as from, type(r) as rel, labels(b)[0] as to
            ORDER BY from, rel, to
        """)
        for record in result:
            print(f"  ({record['from']})-[{record['rel']}]->({record['to']})")

        # 7. Check for any existing UNF-related nodes
        print("\n🔎 SEARCHING FOR UNF/STORYOS RELATED NODES:")
        print("-" * 80)
        unf_keywords = ['Element', 'Layer', 'Template', 'Deliverable', 'Voice', 'Story', 'Brand', 'UNF']
        for keyword in unf_keywords:
            for label in labels:
                if keyword.lower() in label.lower():
                    print(f"  Found: {label}")
                    result = session.run(f"MATCH (n:{label}) RETURN n LIMIT 1")
                    sample = result.single()
                    if sample:
                        print(f"    Sample: {dict(sample['n'])}")

    driver.close()
    print("\n" + "=" * 80)
    print("✅ EXPLORATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    try:
        explore_database()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
