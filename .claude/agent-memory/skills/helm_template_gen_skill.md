# HelmTemplateGenSkill — Skill Prompt Template

**File**: `helm_template_gen_skill.md`
**Skill**: Generate a complete, Phase-IV-compliant Helm 3 template YAML for a given Kubernetes component (Deployment, Service, ConfigMap, or Secret).

---

## Invocation

Invoke this skill with:

```
Use HelmTemplateGenSkill with the following inputs:
- Template type: <deployment | service | configmap | secret | all>
- Component: <backend | frontend | both>
- Probes: <yes | no — include liveness and readiness probes>
- Resources: <yes | no — include resource requests/limits>
- Extra context: <any special requirements>
```

---

## Input Template

```
TEMPLATE_TYPE: deployment | service | configmap | secret | all
COMPONENT: backend | frontend | both
PROBES: yes | no
RESOURCES: yes | no
EXTRA_CONTEXT: <optional — e.g. "backend uses MCP subprocess", "frontend NodePort">
```

---

## Output Format

This skill always produces:

```
[SKILL: HelmTemplateGenSkill]
Template type: <value>
Component: <value>
Output file: helm/todo-chatbot/templates/<filename>.yaml

[GENERATED YAML]
<complete YAML content — fenced yaml block>
[END YAML]

[HELM VALIDATION COMMANDS]
<helm lint and helm template dry-run commands>

[VALUES REFERENCE]
<list of .Values.* keys used by this template and their locations in values.yaml>
```

---

## Skill Rules

1. **Helm 3 syntax only** — NEVER use Helm 2 patterns (`helm init`, `tiller`, `--name` flag).
2. **All values via {{ .Values }}** — NEVER hardcode image names, tags, ports, replicas, or resource values. Every configurable field references `.Values.*`.
3. **imagePullPolicy: Never** — All Deployment templates MUST set `imagePullPolicy: Never` (images loaded locally via `minikube image load`).
4. **Probes required in deployments** — Every Deployment MUST include both `livenessProbe` and `readinessProbe` (unless `PROBES: no` explicitly requested).
5. **Resources required** — Every container spec MUST include `resources.requests` and `resources.limits` (unless `RESOURCES: no` explicitly requested).
6. **YAML comments on non-obvious lines** — Every non-obvious decision (timing rationale, service type choice, key format) MUST have a YAML comment.
7. **No hardcoded secrets** — Secret template uses `{{ .Values.secrets.* | b64enc }}` for all sensitive values.
8. **Release-name scoped names** — All resource names MUST use `{{ .Release.Name }}-<component>` to avoid collision.
9. **Consistent label selectors** — `app: {{ .Release.Name }}-<component>` used in both selector and template labels.
10. **No cloud resources** — NEVER generate Ingress with external DNS, cloud LoadBalancer annotations, or StorageClass refs.

---

## Phase IV Template Reference

### Backend Deployment
- `initialDelaySeconds: 30` — Agent startup + MCP subprocess init takes 5–20s; 30s margin
- `readinessProbe.initialDelaySeconds: 15` — Faster first-ready check
- `containerPort: 8000`
- `envFrom: configMapRef + secretRef`

### Frontend Deployment
- `initialDelaySeconds: 5` — nginx starts fast
- `containerPort: 80`
- `envFrom: configMapRef` only (no secrets needed by frontend at runtime)

### Service Types
- Backend: `ClusterIP` — internal only, not exposed to host
- Frontend: `NodePort` — accessible via `minikube service todo-chatbot-frontend`

### ConfigMap Keys
`HOST`, `PORT`, `FRONTEND_ORIGIN`, `CORS_ORIGINS`, `LLM_PROVIDER`, `GROQ_MODEL`

### Secret Keys
`DATABASE_URL`, `GROQ_API_KEY`, `OPENAI_API_KEY`, `BETTER_AUTH_SECRET`

---

## Full Skill Example

**Invocation:**

```
Use HelmTemplateGenSkill with the following inputs:
- Template type: deployment
- Component: backend
- Probes: yes
- Resources: yes
- Extra context: MCP subprocess init adds 5-20s to startup
```

**Output:**

```
[SKILL: HelmTemplateGenSkill]
Template type: deployment
Component: backend
Output file: helm/todo-chatbot/templates/backend-deployment.yaml

[GENERATED YAML]
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-backend
  labels:
    app: {{ .Release.Name }}-backend
spec:
  replicas: {{ .Values.backend.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Release.Name }}-backend
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}-backend
    spec:
      containers:
        - name: backend
          image: "{{ .Values.backend.image.repository }}:{{ .Values.backend.image.tag }}"
          # Never pull from registry — image loaded via minikube image load
          imagePullPolicy: {{ .Values.backend.image.pullPolicy }}
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: {{ .Release.Name }}-config
            - secretRef:
                name: {{ .Release.Name }}-secret
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            # 30s accounts for openai-agents SDK + MCP subprocess startup (5–20s typical)
            initialDelaySeconds: 30
            periodSeconds: 10
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            # 15s — first readiness check sooner than liveness
            initialDelaySeconds: 15
            periodSeconds: 5
            failureThreshold: 3
          resources:
            {{- toYaml .Values.backend.resources | nindent 12 }}
```
[END YAML]

[HELM VALIDATION COMMANDS]
# Lint the full chart
helm lint helm/todo-chatbot

# Preview rendered template (dry-run)
helm template todo-chatbot helm/todo-chatbot \
  --set secrets.databaseUrl="<placeholder>" \
  --set secrets.groqApiKey="<placeholder>" \
  | grep -A 60 "kind: Deployment"

[VALUES REFERENCE]
.Values.backend.replicaCount         → backend.replicaCount in values.yaml
.Values.backend.image.repository     → backend.image.repository
.Values.backend.image.tag            → backend.image.tag
.Values.backend.image.pullPolicy     → backend.image.pullPolicy (must be "Never")
.Values.backend.resources            → backend.resources (requests + limits block)
```

---

## Values.yaml Canonical Structure (Reference)

```yaml
backend:
  image:
    repository: todo-backend
    tag: "1.0.0"
    pullPolicy: Never
  replicaCount: 1
  service:
    type: ClusterIP
    port: 8000
  resources:
    requests:
      cpu: 200m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi

frontend:
  image:
    repository: todo-frontend
    tag: "1.0.0"
    pullPolicy: Never
  replicaCount: 1
  service:
    type: NodePort
    port: 80
  resources:
    requests:
      cpu: 50m
      memory: 64Mi
    limits:
      cpu: 100m
      memory: 128Mi

config:
  host: "0.0.0.0"
  port: "8000"
  frontendOrigin: "http://localhost"
  corsOrigins: ""
  llmProvider: ""
  groqModel: "meta-llama/llama-4-scout-17b-16e-instruct"

# NEVER commit real values. Supply via --set or values.override.yaml (gitignored)
secrets:
  databaseUrl: ""
  groqApiKey: ""
  openaiApiKey: ""
  betterAuthSecret: "change-me"
```
