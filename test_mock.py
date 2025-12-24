import requests
import json

try:
    response = requests.get("http://127.0.0.1:8000/health")
    print("Server is running:", response.json())
    
    # Try a test request
    print("\nSending: Read ping.txt and tell me what it says in one sentence")
    response = requests.post(
        "http://127.0.0.1:8000/chat",
        json={"thread_id": "test_mock", "user_message": "Read ping.txt and tell me what it says in one sentence"},
        timeout=30
    )
    
    print("\nResponse:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
