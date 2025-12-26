#!/usr/bin/env bash
set -euo pipefail
python -m evals.run_evals
python -m agent.smoke_test_llm_agent
