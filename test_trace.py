import requests
import json
import time

API_URL = "http://127.0.0.1:8000/chat"

payload = {
    "thread_id": "test_trace",
    "user_message": "List files in the workspace, then create a file named ping.txt with the text ok, then read it back."
}

print("Sending test prompt...")
try:
    response = requests.post(API_URL, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    
    print("\n[Tools Used]")
    if data.get("tool_calls"):
        for tool in data["tool_calls"]:
            print(f"  • {tool['name']}: {tool['arguments']}")
    
    print("\n[Assistant Response]")
    print(data["assistant_message"])
    
    print("\n✅ Test completed successfully!")
    print("\nCheck the 'traces/' directory for the generated trace file.")
    
except Exception as e:
    print(f"❌ Error: {e}")
