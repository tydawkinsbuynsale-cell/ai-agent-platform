from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Generic, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError


class ToolError(Exception):
    pass


class ToolInputError(ToolError):
    pass


class ToolExecutionError(ToolError):
    pass


InT = TypeVar("InT", bound=BaseModel)
OutT = TypeVar("OutT", bound=BaseModel)


@dataclass(frozen=True)
class ToolSpec(Generic[InT, OutT]):
    name: str
    description: str
    input_model: Type[InT]
    output_model: Type[OutT]
    handler: Any  # callable(input: InT) -> OutT


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"Tool already registered: {spec.name}")
        self._tools[spec.name] = spec

    def list_tools(self) -> Dict[str, str]:
        return {name: spec.description for name, spec in self._tools.items()}

    def call(self, tool_name: str, raw_args: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self._tools:
            raise ToolInputError(f"Unknown tool: {tool_name}")

        spec = self._tools[tool_name]

        try:
            validated_input = spec.input_model.model_validate(raw_args)
        except ValidationError as e:
            raise ToolInputError(f"Invalid args for {tool_name}: {e}") from e

        try:
            out_obj = spec.handler(validated_input)
        except ToolError:
            raise
        except Exception as e:
            raise ToolExecutionError(f"Tool {tool_name} failed: {e}") from e

        # Ensure output matches schema (catches handler mistakes)
        try:
            validated_output = spec.output_model.model_validate(out_obj.model_dump())
        except Exception as e:
            raise ToolExecutionError(f"Tool {tool_name} returned invalid output: {e}") from e

        return validated_output.model_dump()
