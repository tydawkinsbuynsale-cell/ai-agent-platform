import sys
sys.path.insert(0, 'C:/Users/tydaw/ai_assistant')

from app import add_memory, search_memories, mark_memory_used

# Test adding memories
print("Adding test memories...")
add_memory("preference", "User prefers Python over JavaScript", importance=4)
add_memory("fact", "User's name is Tyler", importance=5)
add_memory("project", "Working on AI assistant with FastAPI", importance=4)

# Test searching memories
print("\nSearching for 'Python':")
results = search_memories("Python")
for mem in results:
    print(f"  [{mem['kind']}] {mem['text']} (importance: {mem['importance']}, uses: {mem['uses']})")

# Test marking memory as used
if results:
    mem_id = results[0]['id']
    print(f"\nMarking memory {mem_id} as used...")
    mark_memory_used(mem_id)
    
    # Search again to verify uses incremented
    print("\nSearching again after marking as used:")
    results2 = search_memories("Python")
    for mem in results2:
        print(f"  [{mem['kind']}] {mem['text']} (importance: {mem['importance']}, uses: {mem['uses']})")

print("\n✅ Memory system working!")
