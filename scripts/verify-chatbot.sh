#!/usr/bin/env bash
# verify-chatbot.sh — Smoke-test the todo-chatbot Helm deployment on Minikube
# Run from the project root after `helm install todo-chatbot helm/todo-chatbot ...`

set -euo pipefail

RELEASE="todo-chatbot"
TIMEOUT="120s"
DEMO_USER="demo-user"

echo "=== Phase IV Chatbot Verification ==="
echo ""

# ── 1. Cluster context ────────────────────────────────────────────────────────
echo "[1/7] Checking cluster context..."
CTX=$(kubectl config current-context)
if [[ "$CTX" != "minikube" ]]; then
  echo "ERROR: Expected context 'minikube', got '$CTX'" && exit 1
fi
echo "    OK — context: $CTX"

# ── 2. Images in Minikube ─────────────────────────────────────────────────────
echo "[2/7] Checking images are loaded in Minikube..."
minikube image ls | grep -q "todo-backend"  || { echo "ERROR: todo-backend image not found. Run: minikube image load todo-backend:1.0.0"; exit 1; }
minikube image ls | grep -q "todo-frontend" || { echo "ERROR: todo-frontend image not found. Run: minikube image load todo-frontend:1.0.0"; exit 1; }
echo "    OK — both images present"

# ── 3. Helm release status ────────────────────────────────────────────────────
echo "[3/7] Checking Helm release..."
STATUS=$(helm list --filter "^${RELEASE}$" --short)
if [[ -z "$STATUS" ]]; then
  echo "ERROR: Helm release '${RELEASE}' not found. Run helm install first." && exit 1
fi
echo "    OK — release: $STATUS"

# ── 4. Pods running ───────────────────────────────────────────────────────────
echo "[4/7] Waiting for pods to be Ready (timeout: ${TIMEOUT})..."
kubectl wait --for=condition=ready pod -l app=${RELEASE}-backend  --timeout=${TIMEOUT}
kubectl wait --for=condition=ready pod -l app=${RELEASE}-frontend --timeout=${TIMEOUT}
echo "    OK — all pods Ready"
kubectl get pods -l "app in (${RELEASE}-backend,${RELEASE}-frontend)"

# ── 5. Services exist ─────────────────────────────────────────────────────────
echo ""
echo "[5/7] Checking Services..."
kubectl get service ${RELEASE}-backend ${RELEASE}-frontend
echo "    OK"

# ── 6. Backend health endpoint ────────────────────────────────────────────────
echo ""
echo "[6/7] Testing backend /health endpoint..."
BACKEND_POD=$(kubectl get pod -l app=${RELEASE}-backend -o jsonpath='{.items[0].metadata.name}')
HEALTH=$(kubectl exec "$BACKEND_POD" -- \
  python -c "import urllib.request, json; r=urllib.request.urlopen('http://localhost:8000/health'); print(r.read().decode())")
echo "    Response: $HEALTH"
echo "$HEALTH" | python -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='healthy', 'status not healthy'" \
  && echo "    OK — backend healthy"

# ── 7. Chat endpoint smoke test ───────────────────────────────────────────────
echo ""
echo "[7/7] Testing chat endpoint (add task)..."
CHAT_RESPONSE=$(kubectl exec "$BACKEND_POD" -- \
  python -c "
import urllib.request, json
req = urllib.request.Request(
  'http://localhost:8000/api/${DEMO_USER}/chat',
  data=json.dumps({'message': 'Add a task to verify the deployment', 'conversation_id': None}).encode(),
  headers={'Content-Type': 'application/json'},
  method='POST'
)
r = urllib.request.urlopen(req)
print(r.read().decode())
")
echo "    Response: $CHAT_RESPONSE"
echo "$CHAT_RESPONSE" | python -c "import sys,json; d=json.load(sys.stdin); assert 'response' in d, 'no response field'" \
  && echo "    OK — chat endpoint functional"

echo ""
echo "=== All checks passed ==="
echo ""
echo "Access the frontend:"
minikube service ${RELEASE}-frontend --url
