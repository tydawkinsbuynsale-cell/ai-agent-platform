import requests

API_URL = "http://127.0.0.1:8000/chat"
THREAD_ID = "main"

print("Local AI Assistant (type 'exit' to quit)\n")

while True:
    user_input = input("> ").strip()
    if user_input.lower() in {"exit", "quit"}:
        break

    payload = {
        "thread_id": THREAD_ID,
        "user_message": user_input
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        # Show tool calls if any were made
        if data.get("tool_calls"):
            print("\n[Tools Used]")
            for tool in data["tool_calls"]:
                print(f"  • {tool['name']}: {tool['arguments']}")
        
        print("\n" + data["assistant_message"] + "\n")
    except Exception as e:
        print("Error:", e)
