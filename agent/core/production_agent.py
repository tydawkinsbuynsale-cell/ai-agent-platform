from __future__ import annotations

from typing import Dict, List

from agent.core.agent_loop import Agent, AgentMode
from agent.core.llm_planner import build_planner_prompt, parse_plan_json
from agent.core.policy import enforce_post_change_checks
from agent.core.strict_verifier import strict_verify
from agent.llm.openai_http import OpenAIHTTPClient
from agent.tools.base import ToolInputError


class ProductionAgent(Agent):
    def __init__(self, tools, mode: AgentMode) -> None:
        super().__init__(tools, mode)
        self.llm = OpenAIHTTPClient()

    def plan(self, user_input: str) -> Dict:
        tools = self.tools.get_tool_schemas()
        prompt = build_planner_prompt(user_input, tools)

        last_text = None
        for attempt in range(self.limits.max_planner_attempts):
            resp = self.llm.complete(prompt)
            last_text = resp.text
            try:
                plan = parse_plan_json(resp.text)
                return enforce_post_change_checks(plan)
            except ToolInputError:
                # Ask the model to repair its prior output into valid schema JSON only
                prompt = (
                    "Return ONLY valid JSON matching the required schema. No markdown.\n\n"
                    "Required schema:\n"
                    '{"goal":"string","steps":[{"tool":"tool.name","args":{},"acceptance":"string"}]}\n\n'
                    "Previous output (fix it):\n"
                    + last_text
                )

        raise ToolInputError(f"Planner failed to produce valid JSON after retries. Last output: {last_text!r}")

    def verify(self, goal: str, observations: List[Dict]) -> Dict:
        return strict_verify(goal, observations, self._code_modified)
