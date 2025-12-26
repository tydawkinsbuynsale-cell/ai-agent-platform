from __future__ import annotations

from evals.task_schema import EvalTask


# Basic read test
read_file_task = EvalTask(
    name="read_file",
    description="Agent reads a file in REVIEWER mode",
    user_input="Read docs/patch_test.txt",
    mode="reviewer",
    assertion="result['verification']['success'] == True and result['code_modified'] == False"
)

# Block write in REVIEWER mode
block_write_task = EvalTask(
    name="block_write_reviewer",
    description="Agent blocks write in REVIEWER mode",
    user_input="Append 'test' to docs/patch_test.txt",
    mode="reviewer",
    assertion="result['verification']['success'] == False and 'not allowed in REVIEWER mode' in str(result['observations'])"
)

# Allow write in BUILDER mode
builder_write_task = EvalTask(
    name="builder_write",
    description="Agent writes in BUILDER mode",
    user_input="apply patch",
    mode="builder",
    assertion="result['code_modified'] == True and result['verification']['success'] == True"
)

# Memory read test
memory_read_task = EvalTask(
    name="memory_read",
    description="Agent reads project facts",
    user_input="Read project facts from memory",
    mode="reviewer",
    assertion="result['verification']['success'] == True and any('memory.read_project_facts' in str(obs) for obs in result['observations'])"
)

# Memory retrieval test
retrieval_task = EvalTask(
    name="retrieval",
    description="Keyword retrieval runs during planning",
    user_input="Show me information about the project",
    mode="reviewer",
    assertion="any(step['phase'] == 'RETRIEVAL' for step in result['trace']['steps'])"
)

# Memory write-back test
memory_writeback_task = EvalTask(
    name="memory_writeback",
    description="Successful verified change appends decision to memory",
    user_input="verified patch with memory",
    mode="builder",
    assertion="result['verification']['success'] == True and any(step['phase'] == 'MEMORY_WRITE' for step in result['trace']['steps'])"
)

# Limits enforcement test
limit_max_steps_task = EvalTask(
    name="limit_max_steps",
    description="Agent aborts if plan exceeds max steps",
    user_input="generate too many steps",
    mode="reviewer",
    assertion="'max_steps' in str(result)"
)

# Memory hygiene test
memory_hygiene_task = EvalTask(
    name="memory_hygiene",
    description="Memory hygiene prunes decisions when oversized",
    user_input="trigger hygiene",
    mode="builder",
    assertion="any('memory.hygiene' in str(obs) for obs in result['observations'])"
)

# Parallel checks test
parallel_checks_task = EvalTask(
    name="parallel_checks",
    description="Both dev.run_linter and dev.run_tests executed in parallel",
    user_input="apply patch",
    mode="builder",
    assertion="'dev.run_linter' in str(result['observations']) and 'dev.run_tests' in str(result['observations'])"
)

ALL_TASKS = [
    read_file_task,
    block_write_task,
    builder_write_task,
    memory_read_task,
    retrieval_task,
    memory_writeback_task,
    limit_max_steps_task,
    memory_hygiene_task,
    parallel_checks_task,
]
