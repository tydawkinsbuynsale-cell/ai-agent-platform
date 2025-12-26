from __future__ import annotations

import sys
from pathlib import Path

from agent.registry import build_registry
from agent.core.agent_loop import AgentMode
from evals.deterministic_eval_agent import DeterministicEvalAgent
from evals.tasks.basic_tasks import ALL_TASKS
from evals.fixtures import reset_patch_test_file, reset_memory_files


def run_eval(task):
    """Run a single eval task."""
    reset_patch_test_file()
    reset_memory_files()
    
    mode = AgentMode.BUILDER if task.mode == "builder" else AgentMode.REVIEWER
    agent = DeterministicEvalAgent(build_registry(), mode)
    
    # Run agent and catch exceptions for error-testing evals
    try:
        result = agent.run(task.user_input)
    except Exception as e:
        result = e
    
    # Evaluate assertion
    try:
        passed = eval(task.assertion, {"result": result})
    except Exception as e:
        print(f"[FAIL] {task.name}: Assertion error: {e}")
        return False
    
    if passed:
        print(f"[PASS] {task.name}: {task.description}")
        return True
    else:
        print(f"[FAIL] {task.name}: Assertion failed")
        print(f"   Assertion: {task.assertion}")
        return False


def main():
    print("Running evaluation suite...")
    print()
    
    passed = 0
    failed = 0
    
    for task in ALL_TASKS:
        if run_eval(task):
            passed += 1
        else:
            failed += 1
        print()
    
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
