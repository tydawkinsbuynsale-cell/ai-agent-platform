"""Test memory trace functionality."""
import json
from app import compute_project_id, add_memory, db, retrieve_memories

# Setup: Create test memories
proj_id = compute_project_id("C:/test/workspace")
print(f"Project ID: {proj_id}")

# Add test memories
add_memory("preference", "Use strict typing", 5, proj_id)
add_memory("fact", "Global memory for all", 3, None)

# Retrieve memories
con = db()
memories = retrieve_memories(con, "typing", project_id=proj_id, limit=5)
con.close()

# Build trace
memory_trace = []
for m in memories:
    memory_trace.append({
        "id": m['id'],
        "kind": m['kind'],
        "scope": "project" if m['project_id'] == proj_id else "global",
        "project_id": m['project_id']
    })

print(f"\nMemory trace ({len(memory_trace)} items):")
print(json.dumps(memory_trace, indent=2))

print("\nSummary:")
print(f"  Project: {sum(1 for m in memory_trace if m['scope'] == 'project')}")
print(f"  Global: {sum(1 for m in memory_trace if m['scope'] == 'global')}")
