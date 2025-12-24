import requests
import json
import time

API_URL = "http://127.0.0.1:8000/chat"

payload = {
    "thread_id": "test_simple",
    "user_message": "What is 10 + 5?"
}

print("Sending test prompt: 'What is 10 + 5?'\n")
try:
    response = requests.post(API_URL, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    
    print("[Tools Used]")
    if data.get("tool_calls"):
        for i, tool in enumerate(data["tool_calls"], 1):
            print(f"  {i}. {tool['name']}: {tool['arguments']}")
    else:
        print("  No tools used")
    
    print("\n[Assistant Response]")
    print(data["assistant_message"])
    
    print("\n✅ Test completed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
