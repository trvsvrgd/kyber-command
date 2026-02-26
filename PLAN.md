# Execution Plan

## Current Objective
Establish a tested, modular foundation for Kyber Command and refactor existing code into verified components.

## Roadmap & Progress
- [x] **Phase 1: Foundation (Testing)**
    - [x] Task 1.1: Initialize pytest and `tests/` layout
    - [x] Task 1.2: Add `pytest` (and optionally `pytest-asyncio`) to `requirements.txt`
    - [x] Task 1.3: Add `pyproject.toml` or `pytest.ini` for test discovery
    - [x] Task 1.4: Create `tests/conftest.py` with config/graph fixtures
    - [x] Task 1.5: Add unit tests for `agents/state.py`, `load_config()`, `_route_after_supervisor`, `_should_continue_coder`
    - [x] Task 1.6: Add tests for Coder tools (`read_file`, `list_directory`; mock `write_file` HITL)
    - [x] Task 1.7: Run `pytest tests/ -v` and verify all pass
- [ ] **Phase 2: Modular Refactor**
    - [ ] Task 2.1: Extract config loading to shared module; remove duplicate `load_config` in `observability.py`
    - [ ] Task 2.2: Refactor `graph_engine.py` for easier injection of mock LLMs in tests
    - [ ] Task 2.3: Add integration-style tests for graph routing (supervisor → researcher/coder)
- [ ] **Phase 3: Validation**
    - [ ] Task 3.1: Ensure `chainlit run app.py --port 8080` starts without errors
    - [ ] Task 3.2: Document manual HITL flow for smoke test (optional)

# Alternative Development Plan Proposed by Gemini after I asked it to propose enhancements to the codebase and must be merged with the above plan

## Phase 1: Interactive HITL (High Priority)
- [ ] **Feature**: Implement interactive 'Modify' action in `app.py`.
    - Use `cl.AskUserMessage` to allow users to provide corrected code snippets.
    - Update `_resume_with_decision` to accept the modified content from the user session.
- [ ] **UI**: Add a "Diff" view in the approval message to show exactly what `write_file` will change.

## Phase 2: Agent Intelligence & Context
- [ ] **Droid**: Create a `SecurityAgent` node to run `bandit` or `safety` checks on proposed code changes.
- [ ] **Knowledge**: Integrate a local RAG (using `ChromaDB` or `FAISS`) to index the current working directory so the Researcher can answer "Where is the X logic defined?".

## Phase 3: Observability & UX
- [ ] **Visualization**: Add a `cl.on_chat_start` task to generate the LangGraph Mermaid diagram and display it in a Chainlit tab.
- [ ] **Dynamic Config**: Implement a settings menu in the UI to swap Ollama models (e.g., switching from `llama3.1:8b` to `codellama`) without restarting the app.

## Phase 4: Stability
- [ ] **Persistence**: Add a "Session Manager" to the UI to allow users to clear `state.db` or switch between different conversation threads.
- [ ] **Validation**: Add Pydantic validation for all tool inputs in `coder.py` to prevent malformed file paths.
## Notes & Pivot Log
- No testing framework existed at audit—Phase 1 prioritizes pytest setup per VOS.
- Coder's `write_file` uses `interrupt()`; unit tests will need to mock or skip HITL paths.
