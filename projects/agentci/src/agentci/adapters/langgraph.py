from __future__ import annotations

import json
from typing import Any, Iterable, Mapping

from ..trace import EpisodeRecorder

MODEL_EVENTS = {"on_chat_model_end", "on_llm_end", "model"}
TOOL_EVENTS = {"on_tool_end", "tool"}


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def _to_arguments(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    return {"value": value}


class LangGraphEventAdapter:
    def __init__(self, recorder: EpisodeRecorder, default_node: str = "graph") -> None:
        self.recorder = recorder
        self.default_node = default_node

    def record_event(self, event: Mapping[str, Any]) -> None:
        event_name = str(event.get("event") or event.get("type") or "note")
        node_name = str(event.get("node") or event.get("name") or self.default_node)
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        metadata = {
            "framework": "langgraph",
            "event": event_name,
            "node": node_name,
        }

        if event_name in MODEL_EVENTS:
            prompt = data.get("input", event.get("input", ""))
            response = data.get("output", event.get("output", ""))
            usage = data.get("usage")
            if usage is not None:
                metadata["usage"] = usage
            self.recorder.model_call(
                prompt=_to_text(prompt),
                response=_to_text(response),
                metadata=metadata,
                name=node_name,
            )
            return

        if event_name in TOOL_EVENTS:
            tool_name = str(event.get("tool_name") or node_name)
            arguments = _to_arguments(data.get("input", event.get("input")))
            output = data.get("output", event.get("output"))
            status = str(event.get("status") or data.get("status") or "ok")
            self.recorder.tool_call(
                tool_name=tool_name,
                arguments=arguments,
                output=output,
                status=status,
                metadata=metadata,
            )
            return

        note_payload = {
            "framework": "langgraph",
            "event": event_name,
            "node": node_name,
            "data": data or dict(event),
        }
        self.recorder.note(node_name, note_payload)

    def record_events(self, events: Iterable[Mapping[str, Any]]) -> None:
        for event in events:
            self.record_event(event)


def record_langgraph_events(recorder: EpisodeRecorder, events: Iterable[Mapping[str, Any]]) -> EpisodeRecorder:
    adapter = LangGraphEventAdapter(recorder)
    adapter.record_events(events)
    return recorder
