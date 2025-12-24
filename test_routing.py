import requests
import json
from pathlib import Path

API_URL = "http://127.0.0.1:8000/chat"

def test_routing():
    print("=" * 70)
    print("TESTING MULTI-MODEL ROUTING")
    print("=" * 70)
    print()
    
    # Test 1: Short prompt - should use normal executor
    print("TEST 1: Short prompt (normal executor expected)")
    print("-" * 70)
    
    response = requests.post(
        API_URL,
        json={
            "thread_id": "routing_test_1",
            "user_message": "List files in workspace"
        },
        timeout=60
    )
    
    data = response.json()
    print(f"User: List files in workspace")
    print(f"Status: {data.get('status')}")
    print(f"Response preview: {data.get('assistant_message', '')[:100]}...")
    print()
    
    # Check trace file
    traces_dir = Path("traces")
    if traces_dir.exists():
        trace_files = sorted(traces_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if trace_files:
            trace_data = json.loads(trace_files[0].read_text(encoding="utf-8"))
            
            # Find routing events
            planner_routing = next((e for e in trace_data if e.get("type") == "planner_routing"), None)
            executor_routing = next((e for e in trace_data if e.get("type") == "executor_routing"), None)
            
            if planner_routing:
                print(f"  Planner: {planner_routing.get('provider')}/{planner_routing.get('model')}")
            if executor_routing:
                print(f"  Executor: {executor_routing.get('provider')}/{executor_routing.get('model')}")
                print(f"  Strong executor triggered: {executor_routing.get('is_strong_executor')}")
    
    print()
    print()
    
    # Test 2: Long prompt - should trigger strong executor
    print("TEST 2: Long prompt (strong executor expected)")
    print("-" * 70)
    
    long_message = "Please design the architecture for " + "x" * 600
    
    response = requests.post(
        API_URL,
        json={
            "thread_id": "routing_test_2",
            "user_message": long_message
        },
        timeout=60
    )
    
    data = response.json()
    print(f"User: [Long message with 'architecture' keyword, 600+ chars]")
    print(f"Status: {data.get('status')}")
    print(f"Response preview: {data.get('assistant_message', '')[:100]}...")
    print()
    
    # Check trace file
    if traces_dir.exists():
        trace_files = sorted(traces_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if trace_files:
            trace_data = json.loads(trace_files[0].read_text(encoding="utf-8"))
            
            # Find routing events
            planner_routing = next((e for e in trace_data if e.get("type") == "planner_routing"), None)
            executor_routing = next((e for e in trace_data if e.get("type") == "executor_routing"), None)
            
            if planner_routing:
                print(f"  Planner: {planner_routing.get('provider')}/{planner_routing.get('model')}")
            if executor_routing:
                print(f"  Executor: {executor_routing.get('provider')}/{executor_routing.get('model')}")
                print(f"  Strong executor triggered: {executor_routing.get('is_strong_executor')}")
    
    print()
    print("=" * 70)
    print("ROUTING TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    try:
        test_routing()
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Start server first:")
        print("   .venv\\Scripts\\uvicorn.exe app:app --host 127.0.0.1 --port 8000")
    except Exception as e:
        print(f"❌ Error: {e}")
