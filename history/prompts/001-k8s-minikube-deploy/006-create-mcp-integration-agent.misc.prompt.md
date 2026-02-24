---
id: 006
title: Create MCP Integration Agent
stage: misc
date: 2026-02-23
surface: agent
model: claude-sonnet-4-6
feature: 001-k8s-minikube-deploy
branch: 1-k8s-minikube-deploy
user: developer
command: manual
labels: ["mcp","openai-agents-sdk","fastapi","agent-memory","integration"]
links:
  spec: specs/001-k8s-minikube-deploy/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - .claude/agent-memory/mcp-integration/mcp_integration_agent.md
tests:
  - null
---

## Prompt

In my current Claude project for the Todo AI Chatbot (full-stack with Phase III MCP + Phase IV Kubernetes), go to the folder /phase-iv-k8s/agents (or /agents if that's where my agents are stored).

Create a new agent file called mcp_integration_agent.md. This file should contain a complete, self-contained system prompt for an agent named MCPIntegrationAgent.

The agent's ONLY responsibility is:
- Correctly integrate and use the project's custom MCP server (exposing the 5 task tools: add_task, list_tasks, complete_task, delete_task, update_task)
- Help generate / debug / explain code that connects this MCP server to the OpenAI Agents SDK (Agent + Runner)
- Ensure the integration follows the exact Phase III architecture:
  - Stateless chat endpoint (/api/{user_id}/chat)
  - Fetch conversation history from DB → append user message → run agent → store assistant message + tool calls
  - Agent uses MCP tools exclusively for all task operations (NEVER direct DB access)
  - Tools receive user_id as string for multi-user isolation
  - Agent must follow the exact "Agent Behavior Specification" (natural language command mappings, always confirm actions, friendly responses, error handling)
  - Support chaining (e.g., list_tasks first if ambiguous delete)
  - Handle tool call results → generate human-readable confirmations

Core rules the agent MUST follow 100%:
1. ONLY talk about MCP + OpenAI Agents SDK integration
2. NEVER suggest direct database calls in agent code
3. Always reference the official MCP Python SDK and OpenAI Agents SDK docs
4. Output code snippets using Python (FastAPI + agents SDK style)
5. Include safety: validate user_id, handle "task not found" gracefully, log tool calls
6. Response structure: [ANALYSIS][RECOMMENDED CODE][INTEGRATION STEPS][VERIFICATION][EXAMPLES][QUESTIONS]

Key references to hard-code:
- MCP tools signatures (from Phase III): add_task, list_tasks, complete_task, delete_task, update_task
- update_task: user_id (str), task_id (int), title (str opt), description (str opt) → {"task_id": int, "status": "updated", "title": str}

## Response snapshot

Created `.claude/agent-memory/mcp-integration/mcp_integration_agent.md` — a complete, self-contained system prompt for MCPIntegrationAgent.

Key sections included:

1. **Identity** — Scope-locked to MCP + OpenAI Agents SDK integration for this project only.

2. **10 Core Rules** — Scope lock, no direct DB calls, SDK citations, Python only, user_id safety, structured response format, tool-calls-before-response, user_id injection via ChatContext, singleton lifecycle, agentic generation only.

3. **Phase III Architecture Reference** — Exact project structure, complete chat endpoint flow (9 steps: validate → get/create conversation → load history → store user msg → build input_messages → Runner.run() → store assistant msg → return response), key constants (AGENT_TIMEOUT_SECONDS=30, MAX_HISTORY_MESSAGES=50).

4. **MCP Tool Signatures (exact, from mcp_server.py)** — All 5 tools with exact Python signatures, validation rules, return JSON shapes, and error return shapes. Includes note about _parse_task_id() handling LLM string→int for task_id.

5. **Agent Setup Reference (from agent.py)** — MCPServerStdio init with sys.executable + absolute path pattern, ChatContext dataclass, dynamic_instructions callable, Agent instantiation (Groq + OpenAI paths), Runner.run() pattern with asyncio.wait_for.

6. **Agent Behavior Specification** — Full routing table (11 natural language → tool call mappings), chaining rule (list first if task referenced by name), response confirmation templates for all 5 tools + error cases.

7. **Response Format** — [ANALYSIS][RECOMMENDED CODE][INTEGRATION STEPS][VERIFICATION][EXAMPLES][QUESTIONS] with descriptions.

8. **Full Example** — Complete startup_agent() / dynamic_instructions / Agent setup code, 3 integration steps, 3 curl verification examples (add/list/delete-by-name chain), 3 examples with chaining.

9. **Common Debugging Scenarios** — 5 named symptoms with causes and fixes: no tools called, RuntimeError not initialized, task not found wrong user_id, task_id as string, CrashLoopBackOff in K8s from relative path.

All code is grounded in the actual source files (mcp_server.py, agent.py, routes/chat.py) read directly — no guessing.

## Outcome

- ✅ Impact: MCPIntegrationAgent created at .claude/agent-memory/mcp-integration/mcp_integration_agent.md — 6th agent in the agent-memory directory
- 🧪 Tests: File existence confirmed via Write tool success
- 📁 Files: .claude/agent-memory/mcp-integration/mcp_integration_agent.md
- 🔁 Next prompts: Run /sp.tasks to generate implementation task list; run /sp.implement to generate Dockerfiles + Helm charts
- 🧠 Reflection: Grounded all tool signatures and architecture details directly from reading mcp_server.py, agent.py, and routes/chat.py before writing — eliminates hallucination risk for the exact return shapes and validation logic.

## Evaluation notes (flywheel)

- Failure modes observed: None — source files read before writing
- Graders run and results (PASS/FAIL): File creation PASS
- Prompt variant (if applicable): null
- Next experiment: Invoke MCPIntegrationAgent with "debug CrashLoopBackOff caused by MCP path" to validate the debugging scenarios section
