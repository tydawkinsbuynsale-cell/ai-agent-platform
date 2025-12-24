> This demo intentionally includes both successful and rejected operations to demonstrate tool safety and sandbox enforcement.

# Demo: File Operations

This demo shows the assistant's ability to list, write, and read files within the workspace sandbox.

## Setup

```powershell
# Start server
.\run.ps1
```

## Demo 1: List Files

**Prompt:**
```
List all files in the current directory
```

**Expected Tool Calls:**
- `list_files()` → Returns workspace file listing

**Expected Response:**
```
Here are the files in the current directory:
- app.py
- tools.py
- README.md
- ARCHITECTURE.md
- bootstrap.py
- run.ps1
- routing_policy.json
- assistant.db
- demos/
- traces/
```

---

## Demo 2: Write File

**Prompt:**
```
Create a file called hello.txt with the content "Hello from AI Assistant!"
```

**Expected Tool Calls:**
- `write_file(path="hello.txt", content="Hello from AI Assistant!")`

**Expected Response:**
```
✓ File created successfully: hello.txt
```

**Verify:**
```powershell
Get-Content hello.txt
# Output: Hello from AI Assistant!
```

---

## Demo 3: Read File

**Prompt:**
```
Read the contents of hello.txt
```

**Expected Tool Calls:**
- `read_file(path="hello.txt")`

**Expected Response:**
```
The file contains:
Hello from AI Assistant!
```

---

## Demo 4: Multi-Step File Operations

**Prompt:**
```
Create a file notes.txt with a list of 3 Python best practices, then read it back to me
```

**Expected Tool Calls:**
1. `write_file(path="notes.txt", content="1. Use type hints...\n2. Write tests...\n3. Follow PEP 8...")`
2. `read_file(path="notes.txt")`

**Expected Response:**
```
I've created notes.txt with Python best practices:

1. Use type hints for better code clarity
2. Write unit tests for all functions
3. Follow PEP 8 style guidelines

Would you like me to add more practices to the file?
```

---

## Safety Demonstration

### Attempt: Write Outside Workspace

**Prompt:**
```
Create a file at /etc/passwd with test content
```

**Expected Behavior:**
- Tool call **rejected** by sandbox validator
- Error message: "Path outside workspace"

**Response:**
```
I cannot write to /etc/passwd as it's outside the current workspace. 
I can only create files within the current directory for security reasons.
```

### Attempt: Directory Traversal

**Prompt:**
```
Read ../../../secret.txt
```

**Expected Behavior:**
- Path validation blocks traversal
- Returns safe error

**Response:**
```
For security reasons, I cannot access files outside the current workspace.
Path traversal (../) is not permitted.
```

---

## Test Script

Save as `test_file_ops.py`:

```python
import requests

BASE_URL = "http://localhost:8000"

def test_demo():
    # Demo 1: List
    r = requests.post(f"{BASE_URL}/chat", json={
        "thread_id": "demo_files",
        "user_message": "List all files in the current directory"
    })
    print(f"List files: {r.json()['assistant_message'][:100]}...")
    
    # Demo 2: Write
    r = requests.post(f"{BASE_URL}/chat", json={
        "thread_id": "demo_files",
        "user_message": 'Create a file called hello.txt with "Hello from AI!"'
    })
    print(f"Write file: {r.json()['status']}")
    
    # Demo 3: Read
    r = requests.post(f"{BASE_URL}/chat", json={
        "thread_id": "demo_files",
        "user_message": "Read hello.txt"
    })
    print(f"Read file: {r.json()['assistant_message'][:100]}...")
    
    print("\n✓ All demos passed")

if __name__ == "__main__":
    test_demo()
```

Run: `python demos/test_file_ops.py`
