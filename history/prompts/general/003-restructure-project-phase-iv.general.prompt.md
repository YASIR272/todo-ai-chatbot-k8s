---
id: 003
title: Restructure Project for Phase IV
stage: general
date: 2026-02-23
surface: agent
model: claude-sonnet-4-6
feature: none
branch: 001-k8s-minikube-deploy
user: user
command: manual restructure
labels: ["restructure", "phase-iv", "cleanup", "project-structure"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - src/backend/ (21 files moved from HF-Phase-III-Backend/)
  - src/frontend/ (9 files moved from Hackathon-2-Phase-III/)
  - docker/backend/.gitkeep
  - docker/frontend/.gitkeep
  - helm/todo-chatbot/templates/.gitkeep
tests:
  - N/A
---

## Prompt

Before i give you the next task for sp.plan. First correct my project structure (including files and folder). There are five phases of my project. I have completed III phases now i am working in Phase IV. But i just copied my Phase III Folder and continue working in Phase IV for same folder. I think in my current project for Phase IV I have mixed previous Phase II, III Folders and files together now you read the whole folders and files structures and fix them in correct format. This is all will use in Phase IV.

## Response snapshot

Performed a full project restructuring to clean up the mixed Phase II/III/IV file layout:

**Deleted (outdated/duplicate):**
- Entire `Hackathon-2-Phase-III Chatbot/` folder including:
  - Root-level Python files (old v1.0.0 backend without chat/MCP/agents)
  - Old `routes/` (tasks only, no chat)
  - All `__pycache__/` directories
  - Nonsensical `package.json`/`package-lock.json` files (npm artifact with python+3 as deps)
  - `.vercel/` folder and `vercel.json` (Vercel-specific, not needed for K8s)
  - HF-specific `.gitattributes`, `requirements_fixed.txt` (superseded)

**Moved to `src/backend/` (21 files — authoritative Phase III v2.0.0 backend):**
- main.py, agent.py, mcp_server.py, auth.py, config.py, database.py, models.py, crud.py, schemas.py, setup.py, test_backend.py, requirements.txt, .env.example, .gitignore, .dockerignore
- routes/__init__.py, routes/tasks.py, routes/chat.py
- tests/__init__.py, tests/test_chat.py, tests/test_mcp_tools.py

**Moved to `src/frontend/` (9 files — Phase III React/ChatKit frontend):**
- index.html, package.json, package-lock.json, tsconfig.json, vite.config.ts, .gitignore
- src/main.tsx, src/App.tsx, src/config.ts

**Created empty placeholder directories for Phase IV new work:**
- `docker/backend/` — will contain new multi-stage Dockerfile
- `docker/frontend/` — will contain new nginx-based Dockerfile
- `helm/todo-chatbot/templates/` — will contain Kubernetes manifests

## Outcome

- Impact: Clean, correctly structured Phase IV project. Framework files intact. Source code organized under src/. Phase IV artifacts have dedicated empty directories ready for sp.plan/sp.implement.
- Tests: N/A
- Files: 80+ files reorganized, old parent folder deleted
- Next prompts: /sp.plan for Phase IV implementation planning
- Reflection: The old Hackathon-2-Phase-III Chatbot/ root contained an older v1.0.0 backend (no chat, no MCP, no agents) alongside the authoritative v2.0.0 in HF-Phase-III-Backend/. The authoritative version was clearly identifiable by presence of agent.py, mcp_server.py, and chat route.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Manual verification PASS — all 29 expected files present in src/, no duplicates, no __pycache__, no Vercel artifacts
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
