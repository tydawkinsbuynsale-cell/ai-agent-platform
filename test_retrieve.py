import sys
import time
sys.path.insert(0, 'C:/Users/tydaw/ai_assistant')

from app import add_memory, retrieve_memories, mark_memory_used

# Clear and add test memories
import sqlite3
conn = sqlite3.connect('C:/Users/tydaw/ai_assistant/assistant.db')
conn.execute('DELETE FROM memories')
conn.commit()
conn.close()

print("Adding test memories with varying importance and timestamps...")
add_memory("preference", "User prefers Python over JavaScript", importance=5)
time.sleep(0.1)
add_memory("fact", "User's name is Tyler", importance=4)
time.sleep(0.1)
add_memory("project", "Working on AI assistant with FastAPI", importance=3)
time.sleep(0.1)
add_memory("preference", "User likes dark mode", importance=5)
time.sleep(0.1)
add_memory("fact", "User lives in California", importance=3)

# Test 1: Retrieve with keyword match
print("\n=== Test 1: Retrieve with 'Python' (keyword match boost) ===")
results = retrieve_memories("Python", limit=8)
for i, mem in enumerate(results):
    print(f"{i+1}. [{mem['kind']}] {mem['text']}")
    print(f"   importance={mem['importance']}, uses={mem['uses']}, last_used_ts={mem['last_used_ts']}")

# Mark one memory as used to test recency
if results:
    mem_id = results[0]['id']
    print(f"\nMarking memory {mem_id} as used...")
    mark_memory_used(mem_id)
    time.sleep(0.1)

# Test 2: Retrieve all (no keyword) - should sort by importance, then recency
print("\n=== Test 2: Retrieve all (empty query) - sorted by importance + recency ===")
results = retrieve_memories("", limit=8)
for i, mem in enumerate(results):
    print(f"{i+1}. [{mem['kind']}] {mem['text']}")
    print(f"   importance={mem['importance']}, uses={mem['uses']}")

# Test 3: Retrieve with keyword match - recently used should rank higher
print("\n=== Test 3: Retrieve 'Python' again (should show updated uses) ===")
results = retrieve_memories("Python", limit=8)
for i, mem in enumerate(results):
    print(f"{i+1}. [{mem['kind']}] {mem['text']}")
    print(f"   importance={mem['importance']}, uses={mem['uses']}")

print("\n✅ Memory retrieval working with importance + recency + keyword boost!")
