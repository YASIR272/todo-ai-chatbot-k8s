# API Contract: Todo Chatbot Backend

**Feature**: 001-k8s-minikube-deploy
**Date**: 2026-02-23
**Source**: `src/backend/main.py`, `src/backend/routes/`
**Base URL** (K8s internal): `http://todo-chatbot-backend:8000`
**Base URL** (local dev): `http://localhost:8000`

> This contract documents the existing Phase III API as-is. No new endpoints
> are added in Phase IV. This file exists to inform Helm probe configuration
> and README documentation.

---

## Health & Root Endpoints

### `GET /`

**Purpose**: Basic liveness check — confirms the FastAPI app is running.
**Auth**: None
**Response**:
```json
{
  "message": "Todo Chatbot API is running",
  "version": "2.0.0"
}
```
**Status**: `200 OK`
**Used by**: Helm liveness probe (alternative target)

---

### `GET /health`

**Purpose**: Full health check including database connectivity.
**Auth**: None
**Response (healthy)**:
```json
{
  "status": "healthy",
  "database": "connected"
}
```
**Response (degraded)**:
```json
{
  "status": "degraded",
  "database": "disconnected"
}
```
**Status**: `200 OK` (both cases — K8s probe only checks HTTP status)
**Used by**: Helm readiness and liveness probes on port `8000`
**Implementation**: Executes `SELECT 1` against the configured database engine.

---

## Chat Endpoint

### `POST /api/{user_id}/chat`

**Purpose**: Send a natural language message to the AI agent. The agent uses
MCP tools to create, list, complete, or delete tasks, then returns a response.
**Auth**: `Authorization: Bearer <token>` header (optional in demo mode)
**Path params**: `user_id` — identifies the user's task namespace

**Request body**:
```json
{
  "message": "Add a task to buy groceries",
  "conversation_id": null
}
```

**Response**:
```json
{
  "response": "I've added 'Buy groceries' to your task list.",
  "conversation_id": 42,
  "tool_calls": [
    {
      "tool": "add_task",
      "input": {"title": "Buy groceries", "user_id": "demo-user"},
      "output": {"id": 7, "title": "Buy groceries", "completed": false}
    }
  ]
}
```
**Status**: `200 OK`
**Error**: `400` if message is empty; `500` if LLM provider not configured

---

## Task Endpoints

### `GET /api/{user_id}/tasks`

**Query params**: `status`, `sort`, `order`, `limit`, `offset`
**Response**: Array of Task objects
**Status**: `200 OK`

### `POST /api/{user_id}/tasks`

**Request body**: `{"title": "...", "description": "...", "priority": "medium"}`
**Response**: Created Task object
**Status**: `201 Created`

### `GET /api/{user_id}/tasks/{task_id}`

**Response**: Single Task object or `404 Not Found`

### `PUT /api/{user_id}/tasks/{task_id}`

**Request body**: Partial Task fields to update
**Response**: Updated Task object

### `DELETE /api/{user_id}/tasks/{task_id}`

**Response**: `204 No Content`

### `PATCH /api/{user_id}/tasks/{task_id}/complete`

**Purpose**: Toggle task completion status
**Response**: Updated Task object

---

## MCP Tool Signatures (internal — via stdio subprocess)

These are used by the AI agent internally, not exposed as HTTP endpoints.
Documented here for completeness.

| Tool | Input | Output |
|------|-------|--------|
| `add_task` | `{title, description?, priority?, user_id}` | Task object |
| `list_tasks` | `{user_id, status?, limit?}` | Array of Task objects |
| `complete_task` | `{task_id, user_id}` | Updated Task object |
| `delete_task` | `{task_id, user_id}` | `{success: true}` |
| `update_task` | `{task_id, user_id, title?, description?, priority?}` | Updated Task object |

---

## Frontend API Integration

The frontend (`src/frontend/src/config.ts`) constructs the API URL as:

```typescript
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV ? "http://localhost:8000" : "<hf-spaces-url>");
```

For K8s deployment, `VITE_API_BASE_URL` is supplied as a Docker `--build-arg`:

```bash
docker build \
  --build-arg VITE_API_BASE_URL=http://todo-chatbot-backend:8000 \
  -t todo-frontend:1.0.0 \
  -f docker/frontend/Dockerfile \
  src/frontend/
```

The frontend calls `POST ${API_BASE_URL}/api/${userId}/chat` for all chat
interactions, where `userId` is read from `localStorage` (defaults to
`"demo-user"`).
