from __future__ import annotations

from typing import Any, Iterable, Mapping

from ..trace import EpisodeRecorder

MESSAGE_TYPES = {"message_output_item", "message", "assistant_message"}
TOOL_CALL_TYPES = {"tool_call_item", "tool_call"}
TOOL_RESULT_TYPES = {"tool_result_item", "tool_result"}


def _extract_text(item: Mapping[str, Any]) -> str:
    content = item.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
                continue
            if not isinstance(block, dict):
                continue
            text = block.get("text") or block.get("output_text") or block.get("content")
            if text:
                parts.append(str(text))
        return "\n".join(parts)
    return str(item.get("text") or item.get("output_text") or item.get("output") or "")


def _to_arguments(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    return {"value": value}


class OpenAIAgentsEventAdapter:
    def __init__(self, recorder: EpisodeRecorder) -> None:
        self.recorder = recorder
        self.pending_tool_calls: dict[str, dict[str, Any]] = {}

    def record_item(self, item: Mapping[str, Any], prompt: str = "") -> None:
        item_type = str(item.get("type") or "note")
        metadata = {
            "framework": "openai_agents",
            "item_type": item_type,
        }

        if item_type in MESSAGE_TYPES:
            metadata["role"] = str(item.get("role") or "assistant")
            self.recorder.model_call(
                prompt=prompt or str(item.get("prompt") or ""),
                response=_extract_text(item),
                metadata=metadata,
                name=str(item.get("agent") or "assistant"),
            )
            return

        if item_type in TOOL_CALL_TYPES:
            call_id = str(item.get("call_id") or item.get("id") or item.get("name") or "tool")
            pending = {
                "tool_name": str(item.get("name") or "tool"),
                "arguments": _to_arguments(item.get("arguments") or item.get("input")),
                "metadata": metadata,
            }
            self.pending_tool_calls[call_id] = pending
            if "output" in item or "result" in item:
                self.recorder.tool_call(
                    tool_name=pending["tool_name"],
                    arguments=pending["arguments"],
                    output=item.get("output", item.get("result")),
                    status=str(item.get("status") or "ok"),
                    metadata=metadata,
                )
            return

        if item_type in TOOL_RESULT_TYPES:
            call_id = str(item.get("call_id") or item.get("id") or item.get("name") or "tool")
            pending = self.pending_tool_calls.pop(call_id, {})
            tool_name = str(pending.get("tool_name") or item.get("name") or "tool")
            arguments = pending.get("arguments") or _to_arguments(item.get("arguments") or item.get("input"))
            self.recorder.tool_call(
                tool_name=tool_name,
                arguments=arguments,
                output=item.get("output", item.get("result")),
                status=str(item.get("status") or "ok"),
                metadata=metadata,
            )
            return

        self.recorder.note(
            "openai_event",
            {
                "framework": "openai_agents",
                "item_type": item_type,
                "payload": dict(item),
            },
        )

    def record_items(self, items: Iterable[Mapping[str, Any]], prompt: str = "") -> None:
        for item in items:
            self.record_item(item, prompt=prompt)


def record_openai_agent_items(
    recorder: EpisodeRecorder,
    items: Iterable[Mapping[str, Any]],
    prompt: str = "",
) -> EpisodeRecorder:
    adapter = OpenAIAgentsEventAdapter(recorder)
    adapter.record_items(items, prompt=prompt)
    return recorder
