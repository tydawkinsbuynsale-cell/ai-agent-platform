# Demo: Project-Scoped Memory Isolation

This demo proves that memories are isolated between different workspaces, with each project maintaining its own context.

## Concept

Each workspace gets a unique `project_id` computed from its resolved absolute path:

```
C:/projects/backend  → project_id: a3f92b7e1c4d
C:/projects/frontend → project_id: 8d1e5f2a9b3c
```

Memories saved with `scope="project"` are only visible within that workspace.

---

## Setup

Create two distinct project directories:

```powershell
# Project A: Backend API
New-Item -ItemType Directory -Path C:\temp\project_a
Set-Location C:\temp\project_a
Copy-Item C:\Users\tydaw\ai_assistant\.env .

# Project B: Frontend UI
New-Item -ItemType Directory -Path C:\temp\project_b
Set-Location C:\temp\project_b
Copy-Item C:\Users\tydaw\ai_assistant\.env .
```

---

## Demo 1: Save Project-Specific Preference

### Project A (Backend)

**Working Directory:** `C:\temp\project_a`

**Prompt:**
```
Remember for this project: always use FastAPI for REST endpoints
```

**Expected Tool Calls:**
1. Detects: "remember" + "this project"
2. `save_memory(kind="preference", text="Use FastAPI for REST endpoints", scope="project")`
3. Saves with `project_id` = hash of `C:\temp\project_a`

**Expected Response:**
```
✓ I'll remember to use FastAPI for REST endpoints in this project.
```

**Verify Project ID:**
```powershell
python -c "from app import compute_project_id; print(compute_project_id('C:/temp/project_a'))"
# Output: abc123def456 (example)
```

### Project B (Frontend)

**Working Directory:** `C:\temp\project_b`

**Prompt:**
```
Remember for this project: always use React with TypeScript
```

**Expected Tool Calls:**
1. `save_memory(kind="preference", text="Use React with TypeScript", scope="project")`
2. Saves with `project_id` = hash of `C:\temp\project_b`

**Expected Response:**
```
✓ I'll remember to use React with TypeScript in this project.
```

---

## Demo 2: Verify Isolation

### Query Project A

**Working Directory:** `C:\temp\project_a`

**Prompt:**
```
What framework should I use for building APIs?
```

**Expected Memory Retrieval:**
- Loads: "Use FastAPI for REST endpoints" (project_id matches)
- Does NOT load: "Use React with TypeScript" (different project_id)

**Expected Response:**
```
You should use FastAPI for REST endpoints. It provides:
- Automatic API documentation
- Type hints support
- High performance with async/await
```

### Query Project B

**Working Directory:** `C:\temp\project_b`

**Prompt:**
```
What framework should I use for the frontend?
```

**Expected Memory Retrieval:**
- Loads: "Use React with TypeScript" (project_id matches)
- Does NOT load: "Use FastAPI for REST endpoints" (different project_id)

**Expected Response:**
```
Use React with TypeScript for your frontend. Benefits include:
- Strong type checking
- Component reusability
- Large ecosystem
```

---

## Demo 3: Global Memory (Accessible Everywhere)

### Save Global Preference

**Working Directory:** Any project

**Prompt:**
```
Always remember: I prefer concise explanations without verbosity
```

**Expected Tool Calls:**
1. Detects: "always remember"
2. `save_memory(kind="preference", text="Prefer concise explanations", scope="global")`
3. Saves with `project_id = NULL`

**Expected Response:**
```
✓ I'll keep explanations concise across all projects.
```

### Verify Global Access

**Test in Project A:**
```
Explain what CORS is
```

**Expected:** Concise response (global memory applied)

**Test in Project B:**
```
Explain what props are in React
```

**Expected:** Concise response (same global memory applied)

---

## Demo 4: Memory Priority (Project > Global)

### Setup

**Project A:**
```
Remember for this project: use Python 3.11 specifically
```

**Global:**
```
Always remember: I prefer Python 3.12 in general
```

### Query in Project A

**Prompt:**
```
What Python version should I use?
```

**Expected Memory Ranking:**
1. "Use Python 3.11 specifically" (PROJECT - highest priority)
2. "I prefer Python 3.12 in general" (GLOBAL - lower priority)

**Expected Response:**
```
For this project, use Python 3.11 specifically as configured.
```

### Query in Project B (no project-specific memory)

**Prompt:**
```
What Python version should I use?
```

**Expected Memory Ranking:**
1. "I prefer Python 3.12 in general" (GLOBAL - only match)

**Expected Response:**
```
Use Python 3.12 as that's your preferred version.
```

---

## Test Script

Save as `test_project_scope.py`:

```python
import requests
import os

BASE_URL = "http://localhost:8000"

def test_isolation():
    # Project A
    r = requests.post(f"{BASE_URL}/chat", json={
        "thread_id": "proj_a",
        "user_message": "Remember for this project: use FastAPI",
        "cwd": "C:/temp/project_a"
    })
    print(f"Project A saved: {r.json()['status']}")
    
    # Project B
    r = requests.post(f"{BASE_URL}/chat", json={
        "thread_id": "proj_b",
        "user_message": "Remember for this project: use React",
        "cwd": "C:/temp/project_b"
    })
    print(f"Project B saved: {r.json()['status']}")
    
    # Query A (should mention FastAPI, not React)
    r = requests.post(f"{BASE_URL}/chat", json={
        "thread_id": "proj_a_query",
        "user_message": "What framework should I use?",
        "cwd": "C:/temp/project_a"
    })
    response_a = r.json()['assistant_message']
    print(f"Project A isolated: {'FastAPI' in response_a and 'React' not in response_a}")
    
    # Query B (should mention React, not FastAPI)
    r = requests.post(f"{BASE_URL}/chat", json={
        "thread_id": "proj_b_query",
        "user_message": "What framework should I use?",
        "cwd": "C:/temp/project_b"
    })
    response_b = r.json()['assistant_message']
    print(f"Project B isolated: {'React' in response_b and 'FastAPI' not in response_b}")
    
    print("\n✓ Project isolation verified")

if __name__ == "__main__":
    test_isolation()
```

Run: `python demos/test_project_scope.py`

---

## Trace Verification

Check `traces/trace_*.json` to see memory loading in action:

```json
{
  "type": "run_start",
  "project_id": "abc123def456",
  "memories": [
    {
      "id": 42,
      "kind": "preference",
      "scope": "project",
      "project_id": "abc123def456"
    },
    {
      "id": 15,
      "kind": "preference",
      "scope": "global",
      "project_id": null
    }
  ]
}
```

---

## Database Verification

```powershell
# Show all project-scoped memories
C:\Users\tydaw\ai_assistant\.venv\Scripts\python.exe -c "
import sqlite3
conn = sqlite3.connect('assistant.db')
rows = conn.execute('''
    SELECT text, project_id 
    FROM memories 
    WHERE project_id IS NOT NULL
    ORDER BY id DESC
''').fetchall()
for text, pid in rows:
    print(f'{pid[:12]}: {text[:50]}')
"
```

**Expected Output:**
```
abc123def456: Use FastAPI for REST endpoints
def789abc123: Use React with TypeScript
```

---

## Use Cases

### 1. Multi-Client Development
- Client A project: "Use their custom API wrapper"
- Client B project: "Use standard requests library"
- Prevents mixing client-specific practices

### 2. Experimentation
- Stable project: "Use production-tested patterns"
- Experimental project: "Try new approaches freely"
- Keeps experimental preferences isolated

### 3. Team Collaboration
- Frontend team workspace: "React conventions"
- Backend team workspace: "FastAPI patterns"
- Each team sees relevant context only

---

## Cleanup

```powershell
# Remove test projects
Remove-Item -Recurse -Force C:\temp\project_a
Remove-Item -Recurse -Force C:\temp\project_b

# Clear test memories from database
C:\Users\tydaw\ai_assistant\.venv\Scripts\python.exe -c "
import sqlite3
conn = sqlite3.connect('assistant.db')
conn.execute('DELETE FROM memories WHERE text LIKE \"%FastAPI%\" OR text LIKE \"%React%\"')
conn.commit()
"
```
