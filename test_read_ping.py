import requests
import json

API_URL = "http://127.0.0.1:8000/chat"

payload = {
    "thread_id": "test_read",
    "user_message": "Read ping.txt and tell me what it says in one sentence."
}

print("Sending test prompt: 'Read ping.txt and tell me what it says in one sentence.'\n")
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
    
    # Check for JSON leak
    response_text = data["assistant_message"]
    has_json = "{" in response_text and ("tool" in response_text or "final" in response_text)
    
    if has_json:
        print("\n❌ WARNING: Possible JSON detected in response!")
    else:
        print("\n✅ No JSON leak detected")
    
    # Verify read_file was used
    if data.get("tool_calls"):
        read_file_used = any(t['name'] == 'read_file' for t in data["tool_calls"])
        if read_file_used:
            print("✅ Planner chose read_file tool")
        else:
            print("❌ read_file tool was not used")
    
    print("\n✅ Test completed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
