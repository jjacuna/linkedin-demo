# Scrum Workflow

## Phase 1: Discovery (Every New Project)
Output a Project Brief before ANY code:
- **Goal**: What are we building and why?
- **Stack**: Technologies with justification
- **Architecture**: Frontend, backend, database, APIs
- **Risks**: Blockers, technical debt, unknowns
- **Railway Readiness**: Deployment strategy, Dockerfile needs, env vars

## Phase 2: Sprint Planning
Break into sprints with prioritized stories:
```
Sprint [#] — [Goal]
├── Story 1: [feature] — Priority: [H/M/L] — Est: [hours]
├── Story 2: [feature] — Priority: [H/M/L] — Est: [hours]
└── Story 3: [feature] — Priority: [H/M/L] — Est: [hours]
```
Deliver one sprint at a time. Get user approval before next sprint.

## Phase 3: Build
- Each sprint ends with working, tested, deployable code
- Follow DRY, SOLID, separation of concerns
- Include error handling, input validation, loading states

## Phase 4: Sub-Agent Delegation (5+ Features)
For large projects, delegate by role:
```
📋 DELEGATION
├── [Frontend] → Build landing page — Status: ✅
├── [Backend] → Create auth API — Status: 🔄
├── [Security] → Audit auth flow — Status: ⏳
└── [DevOps] → Railway config — Status: ⏳
```
Each sub-agent builds, tests, reports back. Tech Lead integrates.

## Phase 5: Review & Retrospective
After each sprint:
- What worked, what didn't, what to improve
- Update backlog based on learnings
- Carry unfinished stories to next sprint
