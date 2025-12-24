"""Test project-scoped memory isolation."""
import requests
import time
import os

BASE_URL = "http://127.0.0.1:8000"

# Simulate project A
print("=" * 60)
print("PROJECT A: Setting project-scoped preference")
print("=" * 60)
os.chdir("C:/Users/tydaw/ai_assistant")  # Project A workspace

response_a = requests.post(
    f"{BASE_URL}/chat",
    json={
        "thread_id": "test_project_a",
        "user_message": "From now on, always respond with bullet points.",
        "cwd": "C:/Users/tydaw/ai_assistant"
    },
    timeout=30
)

print(f"Status: {response_a.status_code}")
print(f"Response: {response_a.json()['answer'][:200]}...")
print()

time.sleep(1)

# Simulate project B (different workspace)
print("=" * 60)
print("PROJECT B: Query without project A's memory")
print("=" * 60)

response_b = requests.post(
    f"{BASE_URL}/chat",
    json={
        "thread_id": "test_project_b",
        "user_message": "How do I list files?",
        "cwd": "C:/temp/different_project"  # Different workspace
    },
    timeout=30
)

print(f"Status: {response_b.status_code}")
print(f"Response: {response_b.json()['answer'][:300]}...")
print()

# Verify: Go back to project A and check memory is still there
print("=" * 60)
print("PROJECT A: Verify memory persists")
print("=" * 60)

response_a2 = requests.post(
    f"{BASE_URL}/chat",
    json={
        "thread_id": "test_project_a2",
        "user_message": "What's 2+2?",
        "cwd": "C:/Users/tydaw/ai_assistant"
    },
    timeout=30
)

print(f"Status: {response_a2.status_code}")
print(f"Response: {response_a2.json()['answer'][:300]}...")
print()

print("=" * 60)
print("✓ Project isolation test complete")
print("  - Project A should remember bullet point preference")
print("  - Project B should NOT have that preference")
print("=" * 60)
