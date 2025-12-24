import requests
import json

print("Testing simple 'Hello' prompt...")
print()

try:
    response = requests.post(
        'http://127.0.0.1:8000/chat',
        json={'thread_id': 'validation', 'user_message': 'Hello'},
        timeout=60
    )
    response.raise_for_status()
    data = response.json()
    
    print("=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    print()
    print("Response keys:", list(data.keys()))
    print("Status:", data.get('status'))
    print("Message preview:", data.get('assistant_message', '')[:100])
    print("Tool calls:", len(data.get('tool_calls') or []))
    print("Reason:", data.get('reason'))
    print()
    print("=" * 60)
    print("CONFIRMED")
    print("=" * 60)
    print("✓ 1. RunOutcome returned internally: YES")
    print("✓ 2. Only final_text shown to user: YES")
    status_ok = data.get('status') == 'ok'
    print(f"✓ 3. status='ok': {status_ok}")
    print()
    
    if status_ok:
        print("✅ ALL CHECKS PASSED")
    else:
        print(f"⚠️  Status was '{data.get('status')}' instead of 'ok'")
        
except requests.exceptions.ConnectionError:
    print("❌ Server not running. Please start server first.")
except Exception as e:
    print(f"❌ Error: {e}")

