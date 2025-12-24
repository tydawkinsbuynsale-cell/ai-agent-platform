"""Simple test of project-scoped memory isolation."""
from app import compute_project_id, add_memory, db, retrieve_memories

# Simulate Project A
print("=" * 60)
print("PROJECT A: Save project-scoped memory")
print("=" * 60)
proj_a = compute_project_id("C:/Users/tydaw/ai_assistant")
print(f"Project A ID: {proj_a}")

add_memory("preference", "Always respond with bullet points", 5, proj_a)
print("✓ Saved: 'Always respond with bullet points' (scope=project)")
print()

# Simulate Project B
print("=" * 60)
print("PROJECT B: Query memories")
print("=" * 60)
proj_b = compute_project_id("C:/temp/different_project")
print(f"Project B ID: {proj_b}")

con = db()
memories_b = retrieve_memories(con, "respond", project_id=proj_b, limit=5)
con.close()

print(f"Memories found in Project B: {len(memories_b)}")
for m in memories_b:
    scope = "PROJECT" if m['project_id'] == proj_b else "GLOBAL"
    print(f"  [{scope}] {m['kind']}: {m['text'][:50]}...")
print()

# Back to Project A
print("=" * 60)
print("PROJECT A: Query memories")
print("=" * 60)

con = db()
memories_a = retrieve_memories(con, "respond", project_id=proj_a, limit=5)
con.close()

print(f"Memories found in Project A: {len(memories_a)}")
for m in memories_a:
    scope = "PROJECT" if m['project_id'] == proj_a else "GLOBAL"
    print(f"  [{scope}] {m['kind']}: {m['text'][:50]}...")
print()

# Verify isolation
print("=" * 60)
print("VERIFICATION")
print("=" * 60)
proj_a_count = sum(1 for m in memories_a if m['project_id'] == proj_a)
proj_b_count = sum(1 for m in memories_b if m['project_id'] == proj_a)

print(f"✓ Project A sees its own memory: {proj_a_count} project-scoped")
print(f"✓ Project B does NOT see Project A's memory: {proj_b_count} from A")

if proj_a_count > 0 and proj_b_count == 0:
    print("\n✅ ISOLATION SUCCESSFUL - Memories are project-scoped!")
else:
    print("\n❌ ISOLATION FAILED")
