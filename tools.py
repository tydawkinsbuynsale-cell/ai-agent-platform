"""
Tool functions for the AI assistant
"""
import subprocess
from datetime import datetime
from pathlib import Path
import requests


def calculator(expression: str) -> str:
    """Evaluate a mathematical expression safely."""
    try:
        # Only allow safe math operations
        allowed_chars = "0123456789+-*/(). "
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters in expression"
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


def current_time() -> str:
    """Get the current date and time."""
    now = datetime.now()
    return now.strftime("%A, %B %d, %Y at %I:%M %p")


def web_search(query: str) -> str:
    """Search the web using DuckDuckGo API."""
    try:
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        # Try to get the abstract or related topics
        if data.get("Abstract"):
            return data["Abstract"]
        elif data.get("RelatedTopics") and len(data["RelatedTopics"]) > 0:
            results = []
            for topic in data["RelatedTopics"][:3]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append(topic["Text"])
            if results:
                return "\n".join(results)
        
        return "No results found. Try a different search query."
    except Exception as e:
        return f"Search error: {str(e)}"


def weather(location: str) -> str:
    """Get weather information for a location using wttr.in."""
    try:
        url = f"https://wttr.in/{location}?format=%l:+%C+%t+%h+%w"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.text.strip()
        return f"Could not fetch weather for {location}"
    except Exception as e:
        return f"Weather error: {str(e)}"


def list_files(path: str = ".") -> str:
    """List files and directories in the specified path."""
    try:
        base_dir = Path.cwd()
        p = (base_dir / path).resolve()
        if not p.exists() or not p.is_dir():
            return "Invalid directory"
        files = [f.name for f in p.iterdir()]
        return "\n".join(files) if files else "Empty directory"
    except Exception as e:
        return f"Error listing files: {str(e)}"


def read_file(path: str) -> str:
    """Read the contents of a file."""
    try:
        base_dir = Path.cwd()
        p = (base_dir / path).resolve()
        if not p.exists() or not p.is_file():
            return "File not found"
        content = p.read_text(encoding="utf-8", errors="ignore")
        # Limit output size to prevent overwhelming the context
        if len(content) > 5000:
            return content[:5000] + "\n... (content truncated, file is too long)"
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


def write_file(path: str, content: str) -> str:
    """Write content to a file. Creates the file if it doesn't exist."""
    try:
        base_dir = Path.cwd()
        p = (base_dir / path).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"File written successfully: {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


def run_command(cmd: str) -> str:
    """Run a safe command. Only allows: ls, pwd, dir, python scripts."""
    try:
        allowed = ["ls", "pwd", "dir", "python"]
        if not any(cmd.strip().startswith(a) for a in allowed):
            return "Command not allowed. Only ls, pwd, dir, and python commands are permitted."
        
        # Split command into list for safer execution
        cmd_list = cmd.split()
        
        result = subprocess.run(
            cmd_list,
            cwd=None,
            capture_output=True,
            text=True,
            timeout=20
        )
        output = (result.stdout + result.stderr)[:8000]
        return output if output else "Command executed successfully (no output)"
    except subprocess.TimeoutExpired:
        return "Command timed out after 20 seconds"
    except Exception as e:
        return f"Error running command: {str(e)}"


def save_memory(kind: str, text: str, importance: int = 5, scope: str = "global") -> str:
    """
    Save information to long-term memory.
    Args:
        kind: Type of memory ("preference", "project", or "fact")
        text: The information to remember
        importance: Priority level (1-5, where 5 is highest)
        scope: "project" for project-scoped, "global" for all projects (default)
    """
    # This tool is gated - actual saving happens in app.py after validation
    return f"Memory save requested: [{kind}] {text} (importance: {importance}, scope: {scope})"
