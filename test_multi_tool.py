import requests
import time

API_URL = "http://127.0.0.1:8000/chat"

def test_multi_tool():
    print("\n" + "="*60)
    print("Testing: Calculate 50 * 20, then tell me what time it is")
    print("="*60)
    
    response = requests.post(
        API_URL,
        json={
            "thread_id": "test_multi",
            "user_message": "Calculate 50 * 20, then tell me what time it is"
        },
        timeout=90
    )
    
    data = response.json()
    
    print("\n[Tool Calls]")
    if data.get("tool_calls"):
        for i, tool in enumerate(data["tool_calls"], 1):
            print(f"  {i}. {tool['name']}: {tool['arguments']}")
            print(f"     Status: {tool.get('status', 'ok')}")
    
    print(f"\n[Final Answer]\n{data['assistant_message']}\n")

if __name__ == "__main__":
    time.sleep(3)  # Wait for server
    try:
        test_multi_tool()
    except Exception as e:
        print(f"Error: {e}")
