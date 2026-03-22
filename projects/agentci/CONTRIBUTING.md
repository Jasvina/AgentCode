# Contributing to AgentCI

Thanks for contributing.

## Project principles

- Keep the core dependency-light and local-first
- Prefer portable JSON artifacts over framework-specific lock-in
- Make demos and tests as important as the core API
- Design around reproducibility, not just observability

## Good first contributions

- Add adapters for more agent runtimes
- Add trace fixtures from real agent workflows
- Improve diff readability for nested payloads
- Add pytest helpers and CI recipes
- Write docs for common integration patterns

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Demo commands

```bash
PYTHONPATH=src python examples/math_agent.py
PYTHONPATH=src python examples/langgraph_integration.py
PYTHONPATH=src python examples/openai_agents_integration.py
```

## Pull request checklist

- Add or update tests
- Update docs for user-facing changes
- Keep APIs small and composable
- Prefer explicit episode fields over hidden magic
