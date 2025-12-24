import os
import sqlite3
import json
import time
import random
import re
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

from tools import (
    calculator,
    current_time,
    web_search,
    weather,
    list_files,
    read_file,
    write_file,
    run_command,
    save_memory,
)

@dataclass
class RunOutcome:
    status: str               # "ok" | "partial" | "error"
    final_text: str
    tool_logs: List[Dict]
    reason: Optional[str] = None

# -------------------- EXCEPTIONS --------------------
class AgentTimeout(Exception):
    """Raised when agent loop exceeds time limit."""
    pass

class PlannerError(Exception):
    pass

class ToolExecutionError(Exception):
    pass

class ExecutorError(Exception):
    pass

# -------------------- ROUTING POLICY --------------------
def load_routing_policy(path="routing_policy.json"):
    from pathlib import Path
    return json.loads(Path(path).read_text(encoding="utf-8"))

def create_llm_from_policy(policy_entry: Dict[str, str]):
    """
    Create an LLM client from a policy entry {provider, model}.
    
    Args:
        policy_entry: Dict with 'provider' and 'model' keys
        
    Returns:
        Tuple of (llm_client, model_name)
    """
    provider = policy_entry["provider"]
    model = policy_entry["model"]
    
    if provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        return OpenAI(
            api_key="ollama",
            base_url=base_url
        ), model
    elif provider == "openai_compat" or provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        if base_url:
            return OpenAI(api_key=api_key, base_url=base_url), model
        else:
            return OpenAI(api_key=api_key), model
    else:
        raise ValueError(f"Unknown provider: {provider}")

def should_use_strong_executor(user_text: str, policy: dict) -> bool:
    rules = policy["rules"]["use_strong_executor_if"]
    if len(user_text) >= rules["min_user_chars"]:
        return True
    t = user_text.lower()
    return any(k in t for k in rules["contains_any"])

# -------------------- ENV --------------------
load_dotenv()

# Check if we're in mock mode for testing
LLM_MODE = os.getenv("LLM_MODE", "live")

# Load routing policy
try:
    ROUTING_POLICY = load_routing_policy()
    print(f"📋 Loaded routing policy: Planner={ROUTING_POLICY['planner']['primary']['model']}, Executor={ROUTING_POLICY['executor']['primary']['model']}")
except FileNotFoundError:
    print("⚠️  No routing_policy.json found, using environment variables")
    ROUTING_POLICY = None

# Create two separate LLM clients
def create_llm_client(provider: str, model: str, base_url: Optional[str] = None):
    """Create an LLM client based on provider type."""
    if provider == "ollama":
        return OpenAI(
            api_key="ollama",  # Ollama doesn't need real key
            base_url=base_url or "http://localhost:11434/v1"
        ), model
    elif provider == "openai_compat" or provider == "openai":
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY")), model
    else:
        raise ValueError(f"Unknown provider: {provider}")

# Initialize planner and executor LLMs
if LLM_MODE == "mock":
    # Use mock LLMs for testing (no network calls)
    from mock_llm import MockLLM
    planner_llm = MockLLM("planner")
    planner_model_name = "mock-planner"
    executor_llm = MockLLM("executor")
    executor_model_name = "mock-executor"
    print("🧪 Running in MOCK mode (no network calls)")
else:
    # Use routing policy if available, otherwise fall back to env vars
    if ROUTING_POLICY:
        planner_llm, planner_model_name = create_llm_from_policy(ROUTING_POLICY["planner"]["primary"])
        executor_llm, executor_model_name = create_llm_from_policy(ROUTING_POLICY["executor"]["primary"])
        print(f"🚀 Running with policy-driven routing")
    else:
        # Legacy: Use environment variables
        planner_provider = os.getenv("PLANNER_PROVIDER", "openai")
        planner_model = os.getenv("PLANNER_MODEL", "gpt-4o-mini")
        planner_base_url = os.getenv("PLANNER_OLLAMA_BASE_URL", "http://localhost:11434/v1")
        planner_llm, planner_model_name = create_llm_client(planner_provider, planner_model, planner_base_url)

        executor_provider = os.getenv("EXECUTOR_PROVIDER", "openai")
        executor_model = os.getenv("EXECUTOR_MODEL", "gpt-4o-mini")
        executor_llm, executor_model_name = create_llm_client(executor_provider, executor_model)
        print(f"🚀 Running in LIVE mode - Planner: {planner_provider}/{planner_model_name}, Executor: {executor_provider}/{executor_model_name}")

# Legacy client for backwards compatibility
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------- DB --------------------
DB_PATH = "assistant.db"

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER NOT NULL,
        kind TEXT NOT NULL,
        text TEXT NOT NULL,
        importance INTEGER NOT NULL,
        last_used_ts INTEGER NOT NULL,
        uses INTEGER NOT NULL
    )
    """)
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_memories_kind ON memories(kind)
    """)
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance)
    """)
    # Add project_id column if it doesn't exist (non-destructive migration)
    try:
        cur.execute("ALTER TABLE memories ADD COLUMN project_id TEXT")
    except Exception:
        pass  # Column already exists
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project_id)
    """)
    conn.commit()
    conn.close()

def add_message(thread_id: str, role: str, content: str):
    conn = db()
    conn.execute(
        "INSERT INTO messages(thread_id, role, content) VALUES (?, ?, ?)",
        (thread_id, role, content),
    )
    conn.commit()
    conn.close()

def get_recent_messages(thread_id: str, limit: int = 20) -> List[Dict[str, str]]:
    conn = db()
    rows = conn.execute(
        "SELECT role, content FROM messages WHERE thread_id=? ORDER BY id DESC LIMIT ?",
        (thread_id, limit),
    ).fetchall()
    conn.close()
    rows = list(reversed(rows))
    return [{"role": r["role"], "content": r["content"]} for r in rows]

# -------------------- PROJECT-AWARE MEMORY --------------------
def compute_project_id(workspace_dir: str) -> str:
    import hashlib
    from pathlib import Path
    p = Path(workspace_dir).resolve().as_posix()
    return hashlib.sha1(p.encode("utf-8")).hexdigest()[:12]

def add_memory(kind: str, text: str, importance: int = 5, project_id: str = None):
    """Add a new memory with the new schema."""
    import time
    conn = db()
    ts = int(time.time())
    conn.execute(
        "INSERT INTO memories(ts, kind, text, importance, last_used_ts, uses, project_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (ts, kind.strip(), text.strip(), int(importance), ts, 0, project_id),
    )
    conn.commit()
    conn.close()

def retrieve_memories(con, query: str, project_id: str = None, limit: int = 8) -> List[sqlite3.Row]:
    """
    Retrieve memories with intelligent ranking:
    - Project memories first (project_id = current)
    - Global memories second (project_id IS NULL)
    - Then by keyword match, importance, recency
    """
    q = f"%{query.lower()}%"
    rows = con.execute("""
        SELECT id, kind, text, importance, last_used_ts, uses, project_id
        FROM memories
        WHERE (project_id = ? OR project_id IS NULL)
        ORDER BY
          (project_id = ?) DESC,
          (CASE WHEN lower(text) LIKE ? THEN 1 ELSE 0 END) DESC,
          importance DESC,
          last_used_ts DESC
        LIMIT ?
    """, (project_id, project_id, q, limit)).fetchall()
    return rows

def mark_memory_used(memory_id: int):
    """Increment uses counter and update last_used_ts when a memory is retrieved."""
    import time
    conn = db()
    ts = int(time.time())
    conn.execute(
        "UPDATE memories SET uses = uses + 1, last_used_ts = ? WHERE id = ?",
        (ts, memory_id)
    )
    conn.commit()
    conn.close()

def format_memories(memories):
    """Format memories for display to the model."""
    if not memories:
        return ""
    lines = ["MEMORY:"]
    for m in memories:
        kind, text, importance = m['kind'], m['text'], m['importance']
        lines.append(f"- ({kind}, {importance}) {text}")
    return "\n".join(lines)

def should_save_memory(user_message: str) -> Optional[Dict[str, Any]]:
    """
    Uses GPT to decide if the user message contains info worth remembering.
    Returns dict with key/value/importance or None.
    """
    # Skip in mock mode
    if LLM_MODE == "mock":
        return None
    
    prompt = (
        "Decide if this message contains a fact, preference, or context worth remembering.\n"
        "If yes, extract:\n"
        '  - "key": a short label (e.g., "Location", "Preference: Build Tools")\n'
        '  - "value": the actual fact/detail\n'
        '  - "importance": 1-10\n\n'
        "If not worth remembering, output exactly: NO\n\n"
        f'User message: "{user_message}"\n\n'
        "Output (JSON or NO):"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    text = response.choices[0].message.content.strip()
    if text.upper() == "NO":
        return None
    try:
        import json
        data = json.loads(text)
        if "key" in data and "value" in data:
            return {
                "key": data["key"],
                "value": data["value"],
                "importance": data.get("importance", 5),
            }
    except:
        pass
    return None

# -------------------- AGENT LOOP --------------------
def extract_first_json_object(text: str) -> Optional[dict]:
    """
    Extract the first valid JSON object from a string, even if mixed with text.
    Returns dict if found, else None.
    """
    s = text.strip()
    # Fast path: pure JSON
    if s.startswith("{") and s.endswith("}"):
        try:
            obj = json.loads(s)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

    # Mixed content: scan for a JSON object by bracket balancing
    start = s.find("{")
    if start == -1:
        return None

    depth = 0
    for i in range(start, len(s)):
        ch = s[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = s[start : i + 1]
                try:
                    obj = json.loads(candidate)
                    if isinstance(obj, dict):
                        return obj
                except Exception:
                    return None
    return None


TOOL_CALL_RE = re.compile(r"\{.*\}", re.DOTALL)

def parse_tool_call(text: str) -> Optional[Dict[str, Any]]:
    """
    Extracts the first JSON object from a response and validates it as a tool call.
    Returns None if response is not a valid tool call.
    """
    if not text:
        return None

    # If model returns pure JSON, use it; otherwise extract first {...} block
    candidate = text.strip()
    if not (candidate.startswith("{") and candidate.endswith("}")):
        m = TOOL_CALL_RE.search(text)
        if not m:
            return None
        candidate = m.group(0)

    try:
        obj = json.loads(candidate)
    except Exception:
        return None

    if not isinstance(obj, dict):
        return None
    if "tool" not in obj or "args" not in obj:
        return None
    if not isinstance(obj["tool"], str):
        return None
    if not isinstance(obj["args"], dict):
        return None

    return obj


def try_parse_json(text: str):
    """Safely parse JSON, returning None on failure."""
    try:
        return json.loads(text.strip())
    except Exception:
        return None


def trace(event: dict):
    """Log events to agent.log with timestamp."""
    event["ts"] = int(time.time())
    with open("agent.log", "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def call_llm_with_retries(
    messages: List[dict],
    *,
    llm_client = None,
    model: str = "gpt-4o-mini",
    max_retries: int = 5,
    max_total_time: float = 50.0,
) -> str:
    """
    Retries the LLM call on transient failures (rate limits/timeouts).
    Caps total retry time to avoid HTTP timeout.
    Raises the exception if all retries fail.
    """
    if llm_client is None:
        llm_client = client
    
    # Handle MockLLM (no retry needed, deterministic)
    if hasattr(llm_client, 'mode'):  # MockLLM has mode attribute
        from mock_llm import Msg
        mock_messages = [Msg(role=m["role"], content=m["content"]) for m in messages]
        return llm_client.chat(mock_messages)
    
    last_err: Optional[Exception] = None
    start_time = time.time()
    
    for attempt in range(max_retries + 1):
        try:
            response = llm_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                # Check if we have time for another retry
                elapsed = time.time() - start_time
                base_delay = 2.0
                delay = min(15, base_delay * (2 ** attempt))
                
                if elapsed + delay > max_total_time:
                    print(f"Retry budget exhausted ({elapsed:.1f}s elapsed, {max_total_time}s limit)")
                    break
                
                print(f"Retry {attempt + 1}/{max_retries} after {delay:.1f}s...")
                time.sleep(delay)
    
    raise last_err


def needs_tools(user_text: str) -> bool:
    """Check if user input likely requires tool usage."""
    keywords = ["file", "read", "write", "search", "run", "command", "calculate", "time", "date", "folder", "directory"]
    t = user_text.lower()
    return any(k in t for k in keywords)


tool_cache = {}  # key: (tool_name, json.dumps(args, sort_keys=True))


def run_tool(tool_name: str, args: dict) -> str:
    """Execute tool with caching to avoid redundant calls."""
    key = (tool_name, json.dumps(args, sort_keys=True))
    if key in tool_cache:
        return tool_cache[key]
    result = TOOLS[tool_name](**args)
    tool_cache[key] = result
    return result


def synthesize_fallback(tool_logs: list) -> str:
    """Generate fallback response when executor fails but tools succeeded."""
    if not tool_logs:
        return "I couldn't complete that due to a temporary issue. Please try again."
    lines = ["I completed the steps, but couldn't finalize the response. Here are the results:"]
    for t in tool_logs:
        tool = t.get("tool", "unknown")
        res = str(t.get("result", ""))[:400]
        lines.append(f"- {tool}: {res}")
    return "\n".join(lines)


def run_agent_loop(
    tools: Dict[str, Callable],
    messages: List[dict],
    *,
    max_steps: int = 8,
    max_seconds: float = 90,  # MUST be < FastAPI timeout
    enable_trace: bool = False,
    memory_block: str = "",
    project_id: str = "default",
    memory_trace: List[dict] = None,
) -> RunOutcome:
    """
    Agent loop with planner/executor split.
    
    Args:
        tools: Dict mapping tool names to callable functions
        messages: List of message dicts with 'role' and 'content' (includes user request)
        max_steps: Maximum number of tool call iterations
        max_seconds: Maximum execution time in seconds
        enable_trace: Whether to log events to agent.log
        memory_block: Formatted memory text to inject into planner context
        project_id: Project identifier for scoped memory
        
    Returns:
        RunOutcome with explicit status, final_text, tool_calls, and optional error
    """
    import uuid
    
    run_id = str(uuid.uuid4())
    start_ts = int(time.time())
    trace = [{
        "type": "run_start",
        "ts": start_ts,
        "run_id": run_id,
        "project_id": project_id,
        "memories": memory_trace or []
    }]
    
    start_time = time.time()
    
    # Extract user text from messages
    user_text = next((m["content"] for m in messages if m["role"] == "user"), "")
    
    # Select executor based on complexity (policy-driven)
    active_executor_llm = executor_llm
    active_executor_model = executor_model_name
    
    if ROUTING_POLICY and LLM_MODE != "mock":
        # Check if request is complex enough for strong executor
        if should_use_strong_executor(user_text, ROUTING_POLICY):
            # Use a stronger model if configured (for now, just log it)
            # Future: Could have a "strong_executor" field in policy
            trace.append({
                "type": "routing_decision",
                "ts": int(time.time()),
                "run_id": run_id,
                "decision": "complex_request_detected",
                "using_strong_executor": True
            })
    
    # Log planner routing decision
    trace.append({
        "type": "planner_routing",
        "ts": int(time.time()),
        "run_id": run_id,
        "provider": ROUTING_POLICY["planner"]["primary"]["provider"] if ROUTING_POLICY and LLM_MODE != "mock" else "mock",
        "model": planner_model_name,
        "has_fallback": bool(ROUTING_POLICY and "fallback" in ROUTING_POLICY.get("planner", {}))
    })
    
    # Planner loop state
    planner_history = []
    tool_logs = []
    final_instruction = None
    
    try:
        for step in range(1, max_steps + 1):
            # Check timeout
            if time.time() - start_time > max_seconds:
                from pathlib import Path
                Path("traces").mkdir(exist_ok=True)
                Path(f"traces/{start_ts}_{run_id}.json").write_text(
                    json.dumps(trace, indent=2),
                    encoding="utf-8"
                )
                return RunOutcome(
                    status="error",
                    final_text="I couldn't complete that request. Please try again.",
                    tool_logs=tool_logs,
                    reason="timeout"
                )
            
            if enable_trace:
                trace({"event": "planner_step", "step": step})
            
            # Build fresh planner messages
            tool_logs_text = "\n".join([
            f"- {log['name']}: {log['result'][:200]}" for log in tool_logs
            ]) if tool_logs else "None yet"
            
            user_message_with_logs = f"{user_text}\n\nTool logs so far:\n{tool_logs_text}"
            
            planner_messages = [
            {"role": "system", "content": PLANNER_SYSTEM},
            ]
            if memory_block:
                planner_messages.append({"role": "system", "content": memory_block})
            planner_messages.extend([
            *planner_history,
            {"role": "user", "content": user_message_with_logs}
            ])
            
            # Call planner LLM (with fallback support)
            planner_error = None
            try:
                raw = call_llm_with_retries(
                    planner_messages,
                    llm_client=planner_llm,
                    model=planner_model_name
                )
            except Exception as e:
                planner_error = e
                # Try fallback planner if available
                if ROUTING_POLICY and LLM_MODE != "mock" and "fallback" in ROUTING_POLICY["planner"]:
                    trace.append({
                        "type": "planner_fallback",
                        "ts": int(time.time()),
                        "run_id": run_id,
                        "primary_error": str(e)[:200],
                        "trying_fallback": True
                    })
                    try:
                        fallback_llm, fallback_model = create_llm_from_policy(ROUTING_POLICY["planner"]["fallback"])
                        raw = call_llm_with_retries(
                            planner_messages,
                            llm_client=fallback_llm,
                            model=fallback_model
                        )
                        planner_error = None  # Fallback succeeded
                        trace.append({
                            "type": "planner_fallback_success",
                            "ts": int(time.time()),
                            "run_id": run_id,
                            "fallback_provider": ROUTING_POLICY["planner"]["fallback"]["provider"],
                            "fallback_model": fallback_model
                        })
                    except Exception as fallback_error:
                        planner_error = fallback_error
                
                # If still failed, return error
                if planner_error:
                    from pathlib import Path
                    Path("traces").mkdir(exist_ok=True)
                    Path(f"traces/{start_ts}_{run_id}.json").write_text(
                        json.dumps(trace, indent=2),
                        encoding="utf-8"
                    )
                    return RunOutcome(
                        status="error",
                        final_text="I couldn't complete that request. Please try again.",
                        tool_logs=tool_logs,
                        reason="planner_failure"
                    )

            trace.append({
            "type": "planner_raw",
            "ts": int(time.time()),
            "run_id": run_id,
            "text": raw[:4000],
            })

            if not raw or not raw.strip():
                from pathlib import Path
                Path("traces").mkdir(exist_ok=True)
                Path(f"traces/{start_ts}_{run_id}.json").write_text(
                json.dumps(trace, indent=2),
                encoding="utf-8"
                )
                raise PlannerError("Planner returned empty output")

            # Try to parse as tool call
            obj = parse_tool_call(raw)
            
            if obj and "tool" in obj:
                tool_name = obj["tool"]
                args = obj["args"]
                
                if enable_trace:
                    trace({"event": "tool_call", "step": step, "tool": tool_name, "args": args})
                
                # Check if tool exists
                if tool_name not in tools:
                    planner_history.append({"role": "assistant", "content": raw})
                    planner_history.append({"role": "user", "content": f"Tool '{tool_name}' is not available. Continue without tools."})
                    continue
                
                # Gate save_memory tool - only allow if user requested it
                if tool_name == "save_memory":
                    allowed_keywords = ["remember", "save this", "from now on", "always", "store this"]
                    user_lower = user_text.lower()
                    if not any(keyword in user_lower for keyword in allowed_keywords):
                        result = "User did not request saving memory."
                        status = "rejected"
                        planner_history.append({"role": "assistant", "content": raw})
                        planner_history.append({"role": "user", "content": result})
                        continue
                    # If allowed, actually save the memory
                    try:
                        kind = args.get("kind", "fact")
                        text = args.get("text", "")
                        importance = args.get("importance", 5)
                        scope = args.get("scope", "global")
                        # If scope="project", save with project_id; otherwise NULL (global)
                        mem_project_id = project_id if scope == "project" else None
                        add_memory(kind, text, importance, mem_project_id)
                        result = f"Memory saved: [{kind}] {text} (scope: {scope})"
                        status = "ok"
                    except Exception as e:
                        result = f"Error saving memory: {str(e)}"
                        status = "error"
                else:
                    # Execute normal tool
                    try:
                        result = run_tool(tool_name, args)
                        status = "ok"
                    except Exception as e:
                        raise ToolExecutionError(f"{type(e).__name__}: {e}") from e
                
                tool_logs.append({
                    "name": tool_name,
                    "arguments": args,
                    "result": result,
                    "status": status
                })
                
                trace.append({
                    "type": "tool_result",
                    "ts": int(time.time()),
                    "run_id": run_id,
                    "tool": tool_name,
                    "args": args,
                    "status": status,
                    "result": str(result)[:8000],
                })
                
                if enable_trace:
                    trace({"event": "tool_result", "step": step, "tool": tool_name, "status": status})
                
                # Update planner history minimally
                planner_history.append({"role": "assistant", "content": raw})
                planner_history.append({"role": "user", "content": f"Tool result:\n{result}"})
                continue
            
            # Check for final instruction
            try:
                final_obj = json.loads(raw.strip())
                if isinstance(final_obj, dict) and "final" in final_obj and isinstance(final_obj["final"], str):
                    final_instruction = final_obj["final"].strip()
                    if enable_trace:
                        trace({"event": "planner_final", "step": step, "instruction": final_instruction})
                    break
            except:
                pass
            
            # Planner returned something else - ask to continue
            planner_history.append({"role": "assistant", "content": raw})
            planner_history.append({"role": "user", "content": 'Please output either {"tool":"name","args":{...}} or {"final":"instruction"}'})

        # Executor call (once) - AFTER the loop
        # Log executor routing decision
        trace.append({
            "type": "executor_routing",
            "ts": int(time.time()),
            "run_id": run_id,
            "provider": ROUTING_POLICY["executor"]["primary"]["provider"] if ROUTING_POLICY and LLM_MODE != "mock" else "mock",
            "model": active_executor_model,
            "is_strong_executor": should_use_strong_executor(user_text, ROUTING_POLICY) if ROUTING_POLICY else False
        })
        
        tool_logs_text = "\n".join([
            f"- {log['name']}({log['arguments']}): {log['result']}" for log in tool_logs
        ]) if tool_logs else "No tools were used."
        
        executor_messages = [
            {"role": "system", "content": EXECUTOR_SYSTEM},
            {"role": "user", "content": user_text},
            {"role": "user", "content": f"Planner instruction:\n{final_instruction or 'Provide answer based on available information'}"},
            {"role": "user", "content": f"Tool logs:\n{tool_logs_text}"}
        ]
        
        try:
            final_text = call_llm_with_retries(lambda: active_executor_llm.chat(executor_messages))
        except Exception as e:
            raise ExecutorError(f"Executor LLM failed: {e}") from e
        
        trace.append({
            "type": "executor_response",
            "ts": int(time.time()),
            "run_id": run_id,
            "text": final_text[:4000],
        })
        
        if enable_trace:
            trace({"event": "final_answer", "text_preview": final_text[:500]})
        
        from pathlib import Path
        Path("traces").mkdir(exist_ok=True)
        Path(f"traces/{start_ts}_{run_id}.json").write_text(
            json.dumps(trace, indent=2),
            encoding="utf-8"
        )
        
        return RunOutcome(
            status="ok",
            final_text=final_text,
            tool_logs=tool_logs,
            reason=None
        )
    
    except PlannerError as e:
        # Planner failed - return error outcome
        from pathlib import Path
        Path("traces").mkdir(exist_ok=True)
        Path(f"traces/{start_ts}_{run_id}.json").write_text(
            json.dumps(trace, indent=2),
            encoding="utf-8"
        )
        return RunOutcome(
            status="error",
            final_text="I couldn't complete that request. Please try again.",
            tool_logs=tool_logs,
            reason="planner_failure"
        )
    
    except ToolExecutionError as e:
        # Tool execution failed - return error outcome
        from pathlib import Path
        Path("traces").mkdir(exist_ok=True)
        Path(f"traces/{start_ts}_{run_id}.json").write_text(
            json.dumps(trace, indent=2),
            encoding="utf-8"
        )
        return RunOutcome(
            status="error",
            final_text="I couldn't complete that request. Please try again.",
            tool_logs=tool_logs,
            reason="tool_failure"
        )
    
    except ExecutorError as e:
        # Executor failed - return partial outcome with fallback
        from pathlib import Path
        Path("traces").mkdir(exist_ok=True)
        Path(f"traces/{start_ts}_{run_id}.json").write_text(
            json.dumps(trace, indent=2),
            encoding="utf-8"
        )
        return RunOutcome(
            status="partial",
            final_text=synthesize_fallback(tool_logs),
            tool_logs=tool_logs,
            reason="executor_failed"
        )
    
    except Exception as e:
        # Unrecoverable error during agent loop
        from pathlib import Path
        Path("traces").mkdir(exist_ok=True)
        Path(f"traces/{start_ts}_{run_id}.json").write_text(
            json.dumps(trace, indent=2),
            encoding="utf-8"
        )
        return RunOutcome(
            status="error",
            final_text="I couldn't complete that request. Please try again.",
            tool_logs=tool_logs,
            reason="unknown_error"
        )

# -------------------- TOOLS --------------------
# Tool registry mapping tool names to functions
TOOLS: Dict[str, Callable] = {
    "calculator": calculator,
    "current_time": current_time,
    "web_search": web_search,
    "weather": weather,
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
    "save_memory": save_memory,
}

# -------------------- APP --------------------
app = FastAPI()
init_db()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/ping")
def ping():
    return {"reply": "ping", "tool_logs": []}

# Available tools description for the AI
TOOLS_DESCRIPTION = """Available tools:
- calculator: {"expression": "math expression"} - Evaluate math
- current_time: {} - Get current date/time
- web_search: {"query": "search term"} - Search the web
- weather: {"location": "city name"} - Get weather info
- list_files: {"path": "directory"} - List files (default: current dir)
- read_file: {"path": "file.txt"} - Read file contents
- write_file: {"path": "file.txt", "content": "text"} - Write to file
- run_command: {"cmd": "ls"} - Run safe commands (ls, pwd, dir, python)
"""

PLANNER_SYSTEM = (
    "You are the PLANNER.\n"
    + TOOLS_DESCRIPTION + "\n"
    "Your job: decide the next step to solve the user request.\n"
    'If a tool is needed, output ONLY valid JSON: {"tool":"name","args":{...}}\n'
    'If no tool is needed, output ONLY: {"final": "<short instruction to executor>"}\n'
    "Never include any other text."
)

EXECUTOR_SYSTEM = (
    "You are the EXECUTOR.\n"
    "You receive: the user request, brief planner instruction, and tool results.\n"
    "Write the final response to the user in clear natural language.\n"
    "Do NOT output JSON. Do NOT request tools."
)

class ChatRequest(BaseModel):
    thread_id: str
    user_message: str
    save_memory: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    assistant_message: str
    used_memories: List[Dict[str, Any]]
    tool_calls: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None
    reason: Optional[str] = None

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    import uuid
    import os
    
    # Compute project ID from current workspace
    current_workspace = os.getcwd()
    project_id = compute_project_id(current_workspace)
    
    run_id = str(uuid.uuid4())
    start_ts = int(time.time())
    trace = []
    
    try:
        if req.save_memory:
            add_memory(
                key=req.save_memory.get("key", ""),
                value=req.save_memory.get("value", ""),
                importance=int(req.save_memory.get("importance", 5)),
            )

        add_message(req.thread_id, "user", req.user_message)

        auto_mem = should_save_memory(req.user_message)
        if auto_mem:
            add_memory(
                key=auto_mem["key"],
                value=auto_mem["value"],
                importance=auto_mem["importance"],
            )

        history = get_recent_messages(req.thread_id)
        
        with db() as con:
            memories = retrieve_memories(con, req.user_message, project_id=project_id, limit=8)

        memory_block = ""
        memory_trace = []
        if memories:
            memory_block = format_memories(memories)
            
            # Trace memory usage for debugging
            for m in memories:
                memory_trace.append({
                    "id": m['id'],
                    "kind": m['kind'],
                    "scope": "project" if m['project_id'] == project_id else "global",
                    "project_id": m['project_id']
                })
            
            # Mark memories as used
            # for m in memories:
            #     mark_memory_used(m['id'])

        messages = [{"role": "system", "content": PLANNER_SYSTEM}]
        messages.extend(history)

        # Determine max_steps based on user input
        max_steps = 1 if not needs_tools(req.user_message) else 6

        # Run agent loop with tool support
        print(f">>> /chat START (project_id: {project_id})")
        if memory_trace:
            print(f">>> MEMORY: {len(memory_trace)} loaded - {sum(1 for m in memory_trace if m['scope']=='project')} project, {sum(1 for m in memory_trace if m['scope']=='global')} global")
        outcome = run_agent_loop(
            tools=TOOLS,
            messages=messages,
            max_steps=max_steps,
            max_seconds=100,
            memory_block=memory_block,
            project_id=project_id,
            memory_trace=memory_trace
        )
        print(f">>> /chat END (status: {outcome.status})")
        
        # Save final answer to history
        add_message(req.thread_id, "assistant", outcome.final_text)
        
        # Convert memories to JSON-serializable dicts
        used_memories_list = [dict(m) for m in memories] if memories else []
        
        return {
            "assistant_message": outcome.final_text,
            "status": outcome.status,
            "used_memories": used_memories_list,
            "tool_calls": outcome.tool_logs if outcome.tool_logs else None,
            "reason": outcome.reason,
        }
    except Exception as e:
        # Log and return error
        import traceback
        error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return {
            "assistant_message": f"I encountered an error: {str(e)}",
            "used_memories": [],
            "tool_calls": None,
        }
@app.get("/memories")
def list_memories(limit: int = 100):
    conn = db()
    rows = conn.execute(
        "SELECT id, key, value, importance, created_at FROM memories ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.delete("/memories/{memory_id}")
def delete_memory(memory_id: int):
    conn = db()
    conn.execute("DELETE FROM memories WHERE id=?", (memory_id,))
    conn.commit()
    conn.close()
    return {"deleted": memory_id}
