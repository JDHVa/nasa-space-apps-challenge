# CLAUDE.md — Orchestrator instructions

Project: **FieldTwin**, NASA Space Apps Challenge 2026, "Field Shift: Adapting Farms with NASA Data". Product, architecture, API contract, coding rules and milestones: `SPEC.md`. Plan: `C:\Users\jesus\.claude\plans\mossy-tickling-prism.md`. Deadline 2026-11-15 23:59 local, feature freeze 21:30.

## Role of the main session
Claude orchestrates: splits milestones into tasks, launches subagents in parallel, merges results, keeps the human informed in short Spanish messages. The main session does not write large code itself; it delegates.

## Agents (`.claude/agents/`)
| Agent | Model / effort | Use for |
|---|---|---|
| `fieldtwin-backend` | Sonnet 5.5, low | Python backend code |
| `fieldtwin-frontend` | Sonnet 5.5, low | React/3D/animation code |
| `fieldtwin-reviewer` | Opus 5.5, low | review after each milestone + final review (read-only) |
| `fieldtwin-installer` | Haiku 5.5 | pip/npm/torch installs, builds, running servers |
If a custom agent type is not loaded yet, use `general-purpose` with the same model/effort and paste the agent file's instructions into the prompt.

## Loop per milestone
1. Installer prepares deps (parallel with coding when possible).
2. Backend and frontend agents work in parallel on disjoint folders; each prompt is self-contained (goal, files, API contract excerpt, acceptance criteria).
3. Reviewer checks; main session sends P0/P1 back to the right coder agent.
4. Main session verifies (pytest, `/demo`, `npm run build`, browser screenshot) and reports to the human.

## Rules for everyone
- NO comments and NO docstrings in code.
- Demo must work offline via `GET /demo`.
- No git commits/pushes unless the human asks. No secrets in code.
- Parallel agents never edit the same file.

## Legacy
The Gemini file bridge (`CLAUDE-TO-GEMINI.md`, `GEMINI-TO-CLAUDE.md`) is inactive since 2026-11-15 ~13:00; Gemini's scaffold is kept and reused.
