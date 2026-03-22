# Adapter guide

AgentCI keeps the core package dependency-light. The adapters in `src/agentci/adapters/` accept small, framework-shaped event envelopes and translate them into portable AgentCI episodes.

## LangGraphEventAdapter

The adapter accepts event dictionaries with these common fields:

```python
{
    "event": "on_chat_model_end" | "on_tool_end" | ...,
    "node": "planner",
    "tool_name": "search_docs",  # optional
    "status": "ok",              # optional
    "data": {
        "input": ...,             # prompt or tool args
        "output": ...,            # model response or tool output
        "usage": {...},           # optional metadata
    },
}
```

Recognized model events:

- `on_chat_model_end`
- `on_llm_end`
- `model`

Recognized tool events:

- `on_tool_end`
- `tool`

Anything else is recorded as a note step.

## OpenAIAgentsEventAdapter

The adapter accepts item dictionaries shaped like common Agents SDK output items:

```python
{
    "type": "message_output_item" | "tool_call_item" | "tool_result_item" | ...,
    "role": "assistant",          # for message items
    "name": "search_docs",        # for tool items
    "call_id": "call-1",          # optional for matching call/result
    "arguments": {"query": "..."},
    "output": "...",
    "content": [
        {"type": "output_text", "text": "..."}
    ],
}
```

The adapter keeps a tiny in-memory map of pending tool calls so a later `tool_result_item` can reuse the original arguments.

## Why this design

- No hard dependency on external frameworks
- Easy to unit test
- Easy to evolve toward deeper integrations later
