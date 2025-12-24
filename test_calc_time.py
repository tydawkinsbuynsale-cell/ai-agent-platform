import requests
import json

API_URL = "http://127.0.0.1:8000/chat"

payload = {
    "thread_id": "test2",
    "user_message": "Calculate 50 * 20, then tell me the current time."
}

print("Sending test prompt: 'Calculate 50 * 20, then tell me the current time.'\n")
try:
    response = requests.post(API_URL, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    
    print("[Tools Used]")
    if data.get("tool_calls"):
        for i, tool in enumerate(data["tool_calls"], 1):
            print(f"  {i}. {tool['name']}: {tool['arguments']}")
        print(f"\n✅ Total tool calls: {len(data['tool_calls'])}")
    else:
        print("  No tools used")
    
    print("\n[Assistant Response]")
    print(data["assistant_message"])
    
    # Check for JSON leak
    response_text = data["assistant_message"]
    if "{" in response_text and "tool" in response_text and "args" in response_text:
        print("\n❌ WARNING: Raw JSON detected in assistant response!")
    else:
        print("\n✅ No JSON leak detected in response")
    
except Exception as e:
    print(f"❌ Error: {e}")
