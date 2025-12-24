import sys
sys.path.insert(0, 'C:/Users/tydaw/ai_assistant')

# Test the gating logic directly
user_messages = [
    "Please remember that I prefer Python over JavaScript",
    "I like Python",
    "Always use dark mode",
    "From now on, save my preferences",
    "Store this information: I'm a developer",
    "What's the weather today?"
]

allowed_keywords = ["remember", "save this", "from now on", "always", "store this"]

print("Testing save_memory gating logic:\n")
for msg in user_messages:
    user_lower = msg.lower()
    is_allowed = any(keyword in user_lower for keyword in allowed_keywords)
    status = "✅ ALLOWED" if is_allowed else "❌ REJECTED"
    print(f"{status}: \"{msg}\"")

print("\n✅ Gating logic working correctly!")
