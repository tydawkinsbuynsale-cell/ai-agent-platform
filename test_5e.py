import requests
import json
import sqlite3

# Clear memories first
conn = sqlite3.connect('C:/Users/tydaw/ai_assistant/assistant.db')
conn.execute('DELETE FROM memories')
conn.commit()
conn.close()
print("Cleared all memories\n")

try:
    # Test 1: Save memory with "from now on" trigger
    print("=" * 60)
    print("TEST 1: Save memory with 'from now on' trigger")
    print("=" * 60)
    response = requests.post(
        "http://127.0.0.1:8000/chat",
        json={"thread_id": "test_5e", "user_message": "From now on, always answer in strict bullet points."},
        timeout=30
    )
    result1 = response.json()
    print(f"Response: {result1['assistant_message'][:200]}")
    
    # Check if memory was saved
    conn = sqlite3.connect('C:/Users/tydaw/ai_assistant/assistant.db')
    memories = conn.execute("SELECT * FROM memories").fetchall()
    conn.close()
    
    print(f"\nMemories in DB: {len(memories)}")
    for mem in memories:
        print(f"  - [{mem[2]}] {mem[3]} (importance: {mem[4]})")
    
    # Test 2: Retrieve memory and use it
    print("\n" + "=" * 60)
    print("TEST 2: Memory should be retrieved for next request")
    print("=" * 60)
    response = requests.post(
        "http://127.0.0.1:8000/chat",
        json={"thread_id": "test_5e", "user_message": "How do I list files?"},
        timeout=30
    )
    result2 = response.json()
    print(f"Response: {result2['assistant_message']}")
    
    print("\n" + "=" * 60)
    print("VERIFICATION:")
    print("=" * 60)
    print(f"✓ Memory saved: {'Yes' if len(memories) > 0 else 'No'}")
    print(f"✓ Tool calls in test 1: {result1.get('tool_calls', [])}")
    print(f"✓ Second response uses bullet points: {'Yes' if '•' in result2['assistant_message'] or '-' in result2['assistant_message'] else 'Check manually'}")
    
except Exception as e:
    print(f"Error: {e}")
