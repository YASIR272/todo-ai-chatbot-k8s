# K8sCommandGenSkill — Skill Prompt Template

**File**: `k8s_command_gen_skill.md`
**Skill**: Generate safe, validated kubectl and Helm command sequences for a requested Kubernetes operation on the local Minikube cluster.

---

## Invocation

Invoke this skill with:

```
Use K8sCommandGenSkill with the following inputs:
- Action: <deploy | upgrade | scale | inspect | restart | teardown | port-forward>
- Target: <backend | frontend | both | cluster>
- Safe-only: <yes | no — if yes, only read/inspect commands; no writes>
- kubectl-ai: <yes | no — include kubectl-ai natural language equivalents>
- Extra context: <any special flags, replica counts, image tags>
```

---

## Input Template

```
ACTION: deploy | upgrade | scale | inspect | restart | teardown | port-forward
TARGET: backend | frontend | both | cluster
SAFE_ONLY: yes | no
KUBECTL_AI: yes | no
EXTRA_CONTEXT: <optional — e.g. "scale to 2 replicas", "new image tag 1.0.1">
```

---

## Output Format

This skill always produces:

```
[SKILL: K8sCommandGenSkill]
Action: <value>
Target: <value>
Safe-only: <value>

[PRE-CHECKS]
<context verification and state capture commands — always read before write>

[COMMANDS]
<numbered sequence of commands with expected outputs>
Each command includes:
  - Step number and description
  - Exact command (copy-pasteable)
  - Expected output or pass condition

[KUBECTL-AI EQUIVALENTS]
<natural language kubectl-ai commands for the same operations>
(only if KUBECTL_AI: yes)

[VERIFICATION]
<commands to confirm the operation succeeded>
Expected outputs for each verification step.

[ROLLBACK]
<commands to undo the operation if verification fails>
(only for write operations — deploy, upgrade, scale, teardown)
```

---

## Skill Rules

1. **Minikube context enforced** — EVERY command sequence MUST begin with `kubectl config current-context` and assert output is `minikube`.
2. **Read before write** — For any write operation (deploy, upgrade, scale, teardown), the pre-checks MUST capture current state before making changes.
3. **No destructive commands without warning** — `helm uninstall`, `kubectl delete namespace`, `minikube delete` MUST be preceded by a `# WARNING:` block.
4. **No hardcoded secrets in commands** — API keys and DB URLs MUST use `<placeholder>` notation. Never embed real values.
5. **imagePullPolicy: Never enforced** — Deploy sequences MUST include `minikube image load` before `helm install`. Never assume registry pull.
6. **Helm for all K8s resources** — All resource creation via `helm install` / `helm upgrade`. Direct `kubectl apply -f` only for debugging/inspection.
7. **Scale limit: max 3 replicas** — Any scaling command for Phase IV MUST cap at 3 replicas (Minikube resource constraint).
8. **Expected outputs required** — Every command includes its expected output or `[CAPTURE AND VERIFY]` if unknown at generation time.
9. **No `--force` or `--grace-period=0`** — NEVER generate commands that bypass Kubernetes safety mechanisms.
10. **kubectl-ai prompts must be unambiguous** — Natural language kubectl-ai prompts MUST be specific and scoped (e.g., `"scale the todo-chatbot-backend deployment to 2 replicas"` not `"scale backend"`).

---

## Phase IV Command Reference

### Helm Release
```
Release name:     todo-chatbot
Chart path:       helm/todo-chatbot/
Namespace:        default
Backend service:  todo-chatbot-backend  (ClusterIP, port 8000)
Frontend service: todo-chatbot-frontend (NodePort, port 80)
```

### Pod Label Selectors
```
Backend pods:  -l app=todo-chatbot-backend
Frontend pods: -l app=todo-chatbot-frontend
```

### Image Names
```
Backend:  todo-backend:1.0.0
Frontend: todo-frontend:1.0.0
```

---

## Full Skill Example

**Invocation:**

```
Use K8sCommandGenSkill with the following inputs:
- Action: deploy
- Target: both
- Safe-only: no
- kubectl-ai: yes
- Extra context: first-time deploy from clean state; secrets must be supplied
```

**Output:**

```
[SKILL: K8sCommandGenSkill]
Action: deploy
Target: both
Safe-only: no

[PRE-CHECKS]
# Step 0a: Verify Minikube context
kubectl config current-context
# Expected: minikube

# Step 0b: Verify Minikube is running
minikube status
# Expected: host Running, kubelet Running, apiserver Running

# Step 0c: Check no existing release
helm list
# Expected: empty table (no todo-chatbot release yet)

[COMMANDS]
# Step 1: Start Minikube (if not running)
minikube start --cpus=2 --memory=4096 --driver=docker
# Expected: "Done! kubectl is now configured to use minikube cluster"

# Step 2: Build Docker images (from project root)
docker build -t todo-backend:1.0.0 -f docker/backend/Dockerfile .
# Expected: exit code 0, "Successfully tagged todo-backend:1.0.0"

docker build \
  --build-arg VITE_API_BASE_URL=http://todo-chatbot-backend:8000 \
  -t todo-frontend:1.0.0 \
  -f docker/frontend/Dockerfile \
  src/frontend/
# Expected: exit code 0, "Successfully tagged todo-frontend:1.0.0"

# Step 3: Load images into Minikube
minikube image load todo-backend:1.0.0
minikube image load todo-frontend:1.0.0
minikube image ls | grep todo
# Expected: both todo-backend:1.0.0 and todo-frontend:1.0.0 listed

# Step 4: Deploy via Helm
helm install todo-chatbot helm/todo-chatbot \
  --set secrets.databaseUrl="<your-neon-postgresql-url>" \
  --set secrets.groqApiKey="<your-groq-api-key>" \
  --set secrets.betterAuthSecret="<your-jwt-secret>"
# Expected: STATUS: deployed

# Step 5: Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=todo-chatbot-backend --timeout=120s
kubectl wait --for=condition=ready pod -l app=todo-chatbot-frontend --timeout=120s
# Expected: "condition met" for both

[KUBECTL-AI EQUIVALENTS]
# Inspect pods after deploy
kubectl-ai "show me all pods in the default namespace and their status"

# Check deployment details
kubectl-ai "describe the todo-chatbot-backend deployment"

# Check services
kubectl-ai "show me all services and their types and ports"

[VERIFICATION]
kubectl get pods
# Expected:
# NAME                                       READY   STATUS    RESTARTS   AGE
# todo-chatbot-backend-xxxxxxxxx-xxxxx       1/1     Running   0          60s
# todo-chatbot-frontend-xxxxxxxxx-xxxxx      1/1     Running   0          60s

kubectl get services
# Expected:
# todo-chatbot-backend    ClusterIP   10.x.x.x   <none>   8000/TCP
# todo-chatbot-frontend   NodePort    10.x.x.x   <none>   80:3xxxx/TCP

minikube service todo-chatbot-frontend --url
# Expected: http://192.168.x.x:3xxxx (opens in browser)

[ROLLBACK]
# If deploy fails — clean uninstall:
# WARNING: This removes all todo-chatbot Kubernetes resources.
helm uninstall todo-chatbot
kubectl get all
# Expected: only service/kubernetes remains
```

---

## Scale Action Example

**Invocation:**

```
Use K8sCommandGenSkill with the following inputs:
- Action: scale
- Target: backend
- Safe-only: no
- kubectl-ai: yes
- Extra context: scale to 2 replicas
```

**Output:**

```
[SKILL: K8sCommandGenSkill]
Action: scale
Target: backend
Safe-only: no

[PRE-CHECKS]
kubectl config current-context
# Expected: minikube

kubectl get deployment todo-chatbot-backend -o jsonpath='{.spec.replicas}'
# Capture: current replica count (should be 1 for Phase IV default)

[COMMANDS]
# Step 1: Scale to 2 replicas (Phase IV max: 3)
kubectl scale deployment todo-chatbot-backend --replicas=2
# Expected: deployment.apps/todo-chatbot-backend scaled

# Step 2: Wait for new pod
kubectl wait --for=condition=ready pod -l app=todo-chatbot-backend --timeout=60s
# Expected: condition met

[KUBECTL-AI EQUIVALENTS]
kubectl-ai "scale the todo-chatbot-backend deployment to 2 replicas"

[VERIFICATION]
kubectl get pods -l app=todo-chatbot-backend
# Expected: 2 pods with STATUS Running

[ROLLBACK]
kubectl scale deployment todo-chatbot-backend --replicas=1
```
