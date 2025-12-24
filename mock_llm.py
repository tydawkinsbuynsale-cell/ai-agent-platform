from dataclasses import dataclass
from typing import List

@dataclass
class Msg:
    role: str
    content: str

class MockLLM:
    """
    Deterministic planner/executor for offline testing.
    - Planner returns tool calls based on keywords.
    - Executor returns a simple final response using tool logs.
    """
    def __init__(self, mode: str):
        self.mode = mode  # "planner" or "executor"

    def chat(self, messages: List[Msg]) -> str:
        user_text = ""
        for m in reversed(messages):
            if m.role == "user":
                user_text = m.content
                break
        
        # Debug log
        with open("mock_debug.txt", "a") as f:
            f.write(f"[{self.mode}] messages count: {len(messages)}\n")
            f.write(f"[{self.mode}] user_text: {user_text[:500]}\n")
            
            # Extra debug for planner
            if self.mode == "planner":
                has_logs = "tool logs so far:" in user_text
                not_none = "none yet" not in user_text.lower()
                f.write(f"[planner] has_logs={has_logs}, not_none={not_none}\n")
            
            f.write("---\n")

        if self.mode == "planner":
            t = user_text.lower()
            
            # If we already have tool logs with results, return final
            if "tool logs so far:" in t and "none yet" not in t:
                return '{"final":"Answer the user using the tool results."}'
            
            # Check for save_memory triggers (MUST be before other tool checks)
            if any(kw in t for kw in ["from now on", "remember", "always", "store this", "save this"]):
                # Extract the preference/instruction
                if "bullet" in t or "bullet point" in t:
                    return '{"tool":"save_memory","args":{"kind":"preference","text":"Always answer in strict bullet points","importance":5}}'
                elif "remember" in t:
                    # Generic memory save
                    return '{"tool":"save_memory","args":{"kind":"fact","text":"User requested to remember something","importance":3}}'
                # If memory trigger but no specific pattern, still try to save
                return '{"tool":"save_memory","args":{"kind":"preference","text":"User preference or instruction","importance":3}}'
            
            if "read" in t and "ping.txt" in t:
                return '{"tool":"read_file","args":{"path":"ping.txt"}}'
            if "calculate" in t or "multiply" in t or "*" in t:
                # Extract simple math expressions
                import re
                match = re.search(r'(\d+)\s*[\*x×]\s*(\d+)', user_text)
                if match:
                    expr = f"{match.group(1)} * {match.group(2)}"
                    return f'{{"tool":"calculator","args":{{"expression":"{expr}"}}}}'
            if "time" in t or "date" in t:
                return '{"tool":"current_time","args":{}}'
            if "list" in t and "file" in t:
                return '{"tool":"list_files","args":{"path":"."}}'
            if "weather" in t:
                # Try to extract location
                words = user_text.split()
                for i, word in enumerate(words):
                    if word.lower() in ["in", "at", "for"]:
                        if i + 1 < len(words):
                            location = words[i + 1].strip(".,!?")
                            return f'{{"tool":"weather","args":{{"location":"{location}"}}}}'
            return '{"final":"Answer the user using available info."}'

        # executor
        # find tool logs in the last user messages
        tool_blob = ""
        for m in reversed(messages):
            if m.role == "user" and "Tool logs" in m.content:
                tool_blob = m.content
                break
        return f"(MOCK) Final answer based on tool logs:\n{tool_blob[:800]}"
