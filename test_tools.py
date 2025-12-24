"""
Simple script to test the AI assistant's tool capabilities
"""
import requests
import json

API_URL = "http://127.0.0.1:8000/chat"
THREAD_ID = "test_tools"

def test_tool(message):
    """Send a message and display the response with tool usage"""
    print(f"\n{'='*60}")
    print(f"USER: {message}")
    print('='*60)
    
    payload = {
        "thread_id": THREAD_ID,
        "user_message": message
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        # Show tool calls if any
        if data.get("tool_calls"):
            print("\n[Tools Used]")
            for tool in data["tool_calls"]:
                print(f"  🔧 {tool['name']}")
                print(f"     Args: {json.dumps(tool['arguments'], indent=10)}")
                print(f"     Result: {tool['result'][:100]}...")
        
        print(f"\nASSISTANT: {data['assistant_message']}\n")
        
    except Exception as e:
        print(f"Error: {e}\n")

# Test each tool
if __name__ == "__main__":
    print("\n🤖 Testing AI Assistant Tools")
    
    # Test 1: Calculator
    test_tool("What is 123 * 456?")
    
    # Test 2: Current time
    test_tool("What time is it?")
    
    # Test 3: List files
    test_tool("What files are in the current directory?")
    
    # Test 4: Weather
    test_tool("What's the weather like in Tokyo?")
    
    # Test 5: Write and read file
    test_tool("Create a file called test_output.txt with the content 'Hello from AI assistant!'")
    test_tool("Read the contents of test_output.txt")
    
    # Test 6: Multiple tools in one request
    test_tool("Calculate 50 * 20, then tell me what time it is")
    
    print("\n✅ All tests completed!")
