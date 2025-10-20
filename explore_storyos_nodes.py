"""
Deep dive into StoryOS-specific nodes in Neo4j
"""
from neo4j import GraphDatabase
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connection details from environment
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASS = os.getenv("NEO4J_PASS")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

def explore_storyos():
    """Deep dive into StoryOS structure"""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

    with driver.session(database=NEO4J_DATABASE) as session:
        print("=" * 80)
        print("STORYOS STRUCTURE DEEP DIVE")
        print("=" * 80)

        # 1. StoryLayer details
        print("\n📦 STORY LAYERS (like UNF Layers):")
        print("-" * 80)
        result = session.run("MATCH (n:StoryLayer) RETURN n ORDER BY n.name")
        for record in result:
            node = dict(record["n"])
            print(f"  • {node.get('name', 'N/A')}")
            print(f"    ID: {node.get('id', 'N/A')}")
            print(f"    Org: {node.get('org', 'N/A')}")
            print()

        # 2. StoryFacet samples (these are like Elements)
        print("\n🎯 STORY FACETS (like UNF Elements):")
        print("-" * 80)
        result = session.run("""
            MATCH (n:StoryFacet)
            RETURN n.id as id, n.name as name, n.type as type, n.text as text
            LIMIT 5
        """)
        for record in result:
            print(f"  • {record['name']}")
            print(f"    ID: {record['id']}")
            print(f"    Type: {record.get('type', 'N/A')}")
            print(f"    Text preview: {str(record.get('text', 'N/A'))[:100]}...")
            print()

        # 3. StoryModel details
        print("\n📋 STORY MODELS:")
        print("-" * 80)
        result = session.run("MATCH (n:StoryModel) RETURN n ORDER BY n.name")
        for record in result:
            node = dict(record["n"])
            print(f"  • {node.get('name', 'N/A')}")
            print(f"    ID: {node.get('id', 'N/A')}")
            print(f"    Description: {node.get('description', 'N/A')}")
            print()

        # 4. DeliverableTemplate details
        print("\n📄 DELIVERABLE TEMPLATES:")
        print("-" * 80)
        result = session.run("MATCH (n:DeliverableTemplate) RETURN n ORDER BY n.name")
        for record in result:
            node = dict(record["n"])
            print(f"  • {node.get('name', 'N/A')}")
            print(f"    ID: {node.get('id', 'N/A')}")
            print(f"    Description: {node.get('description', 'N/A')}")
            print()

        # 5. TemplateSection details
        print("\n📑 TEMPLATE SECTIONS:")
        print("-" * 80)
        result = session.run("""
            MATCH (t:DeliverableTemplate)-[r:HAS_SECTION]->(s:TemplateSection)
            RETURN t.name as template, s.name as section, s.order as order
            ORDER BY t.name, s.order
            LIMIT 10
        """)
        for record in result:
            print(f"  {record['template']} → Section: {record['section']} (order: {record['order']})")

        # 6. Key relationship patterns
        print("\n🔗 KEY RELATIONSHIP PATTERNS:")
        print("-" * 80)

        # Template → StoryModel relationship
        result = session.run("""
            MATCH (t:DeliverableTemplate)-[r:USES_STORY_MODEL]->(m:StoryModel)
            RETURN t.name as template, m.name as model
        """)
        print("\n  Templates using Story Models:")
        for record in result:
            print(f"    {record['template']} uses {record['model']}")

        # Template → Section → Facet bindings
        result = session.run("""
            MATCH (t:DeliverableTemplate)-[:HAS_SECTION]->(s:TemplateSection)-[r:REQUIRES_FACET]->(f:StoryFacet)
            RETURN t.name as template, s.name as section, f.name as facet
            LIMIT 8
        """)
        print("\n  Section → Facet Bindings (Section Bindings):")
        for record in result:
            print(f"    {record['template']} / {record['section']} → {record['facet']}")

        # 7. Validation Rules
        print("\n✅ VALIDATION RULES:")
        print("-" * 80)
        result = session.run("""
            MATCH (t:DeliverableTemplate)-[:ENFORCES_RULE]->(v:ValidationRule)
            RETURN t.name as template, v.rule_type as rule_type, v.description as description
        """)
        for record in result:
            print(f"  {record['template']}")
            print(f"    Rule: {record['rule_type']}")
            print(f"    Description: {record.get('description', 'N/A')}")
            print()

    driver.close()
    print("\n" + "=" * 80)
    print("✅ EXPLORATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    try:
        explore_storyos()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
