# Kyber Command - Agent Instructions

## Cursor Cloud specific instructions

### Overview

Kyber Command is a Python multi-agent hub using LangGraph + Chainlit + Ollama. See `README.md` for architecture and quick start.

### Services

| Service | How to start | Default port |
|---------|-------------|-------------|
| **Ollama** | `ollama serve` (background) | 11434 |
| **Chainlit app** | `source .venv/bin/activate && chainlit run app.py --port 8080 -h` | 8080 |
| **Phoenix** (optional) | `source .venv/bin/activate && phoenix serve` | 6006 |

### Running commands

- **Activate venv**: `source /workspace/.venv/bin/activate`
- **Tests**: `pytest tests/ -v` (15 tests; no Ollama needed)
- **Lint**: `ruff check .` (if ruff is installed, otherwise standard Python linting)
- **App**: `chainlit run app.py --port 8080 -h` (the `-h` flag runs headless without opening a browser)

### Known issues / gotchas

1. **SqliteSaver async incompatibility**: The installed `langgraph-checkpoint-sqlite>=2.0.0` resolves to v3.x, which does not support async methods. The code in `graph_engine.py` was updated to use `MemorySaver` as a workaround. If reverting to `SqliteSaver`, use `AsyncSqliteSaver` from `langgraph.checkpoint.sqlite.aio` instead.

2. **Ollama model warm-up**: First inference after `ollama serve` loads the model into RAM (~4.9 GB for llama3.1:8b). Expect 30-90 seconds for the first call; subsequent calls are fast (~2-10s on CPU).

3. **Chainlit streaming with subgraphs**: The `app.py` streaming code (`astream` with `subgraphs=True`) may not correctly parse events from newer LangGraph versions, causing responses to not display in the UI. The graph engine itself works correctly — verify with `graph.invoke()` directly if UI display fails.

4. **Phoenix/OpenTelemetry**: The app logs trace export failures to `localhost:4317` when Phoenix isn't running. These are harmless warnings and don't affect functionality.

5. **Ollama must be running before starting Chainlit**: The graph is built at module load time in `app.py`, which creates LLM objects. While Ollama connectivity isn't checked at startup, all chat messages will fail if Ollama isn't running.
