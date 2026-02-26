# Kyber Command

A localized multi-agent coordination hub. Power specialized droids with local LLMs (Ollama). Monitor their activity via Chainlit and Arize Phoenix. Human-in-the-loop safeguards ensure no agent modifies your files without clearance.

## Architecture

- **Supervisor**: Routes queries to Researcher (general info) or Coder (Python/filesystem)
- **Researcher**: Answers factual questions, no tools
- **Coder**: Handles code and files with `read_file`, `write_file`, `list_directory`—file writes require approval
- **Persistence**: SQLite (`state.db`) via LangGraph SqliteSaver
- **Observability**: Phoenix at http://localhost:6006 for tracing

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) running at `http://localhost:11434`
- Model: `llama3.1:8b` (or configure in `config.yaml`)

## Quick Start

```bash
# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Ensure Ollama is running and has a model
ollama pull llama3.1:8b

# 4. (Optional) Start Phoenix for observability
phoenix serve
# Then open http://localhost:6006

# 5. Run the hub
chainlit run app.py --port 8080
```

Open http://localhost:8080 in your browser.

## Usage

1. **Ask a question** – The Supervisor routes to Researcher or Coder.
2. **File operations** – If the Coder proposes a file write, you'll see **Approve**, **Modify**, or **Reject** buttons before it runs.
3. **Sessions** – Conversations persist in `state.db` across restarts.

## Configuration

Edit `config.yaml` to:

- Change Ollama base URL and default model
- Customize agent system prompts
- Set SQLite path and Phoenix endpoint

## Project Structure

```
kyber-command/
├── agents/
│   ├── state.py        # Pydantic/TypedDict state
│   ├── supervisor.py   # Router agent
│   ├── researcher.py   # General info agent
│   └── coder.py        # Code/files agent (HITL tools)
├── config.yaml         # Dynamic configuration
├── graph_engine.py     # LangGraph definition + SqliteSaver
├── app.py              # Chainlit entry (chat + HITL UI)
├── observability.py    # Phoenix instrumentation
├── requirements.txt
└── README.md
```

## Observability

With Phoenix running (`phoenix serve`), all agent "thought chains" are traced at http://localhost:6006. The app uses OpenInference instrumentation for LangChain/LangGraph.
