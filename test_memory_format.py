import sys
sys.path.insert(0, 'C:/Users/tydaw/ai_assistant')

from app import add_memory, retrieve_memories

# Clear and add test memories
import sqlite3
conn = sqlite3.connect('C:/Users/tydaw/ai_assistant/assistant.db')
conn.execute('DELETE FROM memories')
conn.commit()
conn.close()

print("Adding test memories...")
add_memory("preference", "User prefers strict, production-grade answers.", importance=5)
add_memory("project", "Current assistant architecture: planner/executor split, tool chaining, traces enabled.", importance=4)
add_memory("fact", "User's name is Tyler", importance=3)
add_memory("preference", "User likes dark mode in IDEs", importance=4)

print("\nRetrieving memories for query 'assistant'...")
memories = retrieve_memories("assistant", limit=8)

print("\nFormatted output for model:")
print("MEMORY:")
for m in memories:
    print(f"- ({m['kind']}, {m['importance']}) {m['text']}")

print("\n✅ Memory formatting working!")
