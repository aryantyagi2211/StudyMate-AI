# StudyMate AI Production Coding Instructions

Follow these instructions every time you modify this project.

## Production Target

Treat this project as a production system, not only a prototype:

- Make behavior reliable, observable, secure, testable, and maintainable.
- Handle invalid input, unavailable services, timeouts, retries, and recovery explicitly.
- Protect secrets and learner data.
- Keep documentation and deployment instructions aligned with the real code.
- Do not promise or document integrations that are not implemented.

Production quality does **not** mean over-engineering. Choose the simplest design
that satisfies the actual requirement and can be operated safely.

## Simplicity and Anti-Overengineering

- Prefer two clear lines and a suitable existing library over dozens of custom lines.
- Reuse the standard library, existing helpers, and current dependencies first.
- Add a dependency only when it materially improves correctness, security, or maintainability.
- Do not build custom versions of mature library functionality.
- Do not add a framework, service, abstraction layer, repository pattern, event bus, cache, queue, or database speculatively.
- Keep small features local and direct; extract shared code only when duplication is real.
- Avoid speculative configurability and future-proofing.
- Do not trade away validation, security, logging, tests, or recovery in the name of brevity.
- Before finalizing, remove unnecessary code, files, dependencies, and configuration.

## Before Coding

- Read the relevant files, callers, data models, configuration, and tests first.
- Search for existing helpers and patterns before adding new logic.
- Confirm the requested behavior and identify all affected surfaces.
- Do not assume that a prompt or free-form model response is reliable input.
- Do not expose, print, commit, or copy secrets from `.env` or local credentials.

## Code Changes

- Make precise, surgical changes related to the requested task.
- Preserve existing behavior unless the task intentionally changes it.
- Prefer typed models, explicit validation, and deterministic application logic.
- Keep agent responsibilities separate:
  - Profiler: learner context
  - Knowledge: baseline assessment
  - Learning Path: topic/resource selection
  - Adaptive Planner: schedule
  - Teaching: explanations and remediation
  - Examiner: assessment
  - Manager: performance analysis
  - CEO: workflow decision
- Keep workflow transitions in application code, not hidden inside prompts.
- Use one shared constant for the mastery threshold: 85%.
- Treat external API, search, and model responses as untrusted input.
- Validate JSON shape, required fields, score ranges, skill names, and question options.
- Surface errors clearly; do not silently swallow failures or return success-shaped fallbacks.
- Use repository-standard logging and user notifications.
- Avoid broad exception handlers unless they re-raise or provide a specific recovery path.
- Use bounded timeouts and retries for external services; never retry indefinitely.
- Validate required configuration at startup and provide actionable messages.
- Avoid unnecessary casts and preserve type safety.
- Add comments only for non-obvious decisions.
- Follow existing naming, formatting, and localization conventions.

## Adaptive Learning Rules

- Calculate scores in code, not by parsing prose from an agent.
- Select weak topics from structured per-skill results.
- Repeat Teaching -> Examiner -> Manager -> CEO when mastery is below 85%.
- Stop and create a report card when mastery is 85% or higher.
- Enforce a maximum-cycle safeguard to prevent infinite loops.
- Track cycle number, taught topics, exam attempts, scores, weak topics, and final status.

## UI and API Rules

- Keep the visual workflow consistent with the StudyMate AI design.
- Show the active agent, completed stages, mastery percentage, weak topics, and cycle status.
- Keep backend state isolated per user/session.
- Validate all user input at the boundary.
- Do not let malformed websocket/API messages crash the session.
- Keep user-facing messages clear and actionable.
- Expose only the endpoints and data required by the product.
- Keep session data isolated for concurrent users.
- Provide a minimal health/readiness check where the application is deployed as a service.

## Testing Rules

After each change:

1. Run the smallest relevant test or validation command.
2. Test the normal path and the failure path.
3. Test exact threshold boundaries, especially 84%, 85%, and 86%.
4. Test malformed model output and unavailable external services when relevant.
5. Run a broader test/build check when multiple modules are affected.
6. Do not consider the task complete until the expected behavior is verified.
7. Check that the implementation is not over-engineered for the current requirement.

At minimum, maintain tests for:

- workflow state transitions
- profile and input validation
- deterministic score calculation
- weak-topic selection
- adaptive loop termination and continuation
- malformed agent responses
- persistence and session recovery
- web/API integration
- configuration validation and service failure handling

## Documentation Rules

- Update directly related documentation with behavior changes.
- After every completed implementation task, update `task.md`:
  - immediately tick each exact checklist item completed by the change
  - leave unfinished items unticked
  - record validation commands and results
  - mark the progress row complete only when all task items are complete
  - update the next task
- `task.md` is the source of truth for progress; code changes and checklist changes must stay synchronized.
- Never tick an item or mark a task complete before its validation passes.
- Document only integrations that are actually implemented.
- Keep setup instructions accurate for Windows and the supported Python version.
- Never include real API keys, tokens, passwords, or private data.

## Completion Checklist

- [ ] Relevant code and dependencies were inspected.
- [ ] Existing patterns were reused.
- [ ] The change is scoped and type-safe.
- [ ] Success and failure behavior were tested.
- [ ] Related tests were added or updated.
- [ ] Related documentation was updated.
- [ ] No secrets or unrelated files were changed.
- [ ] The solution is production-safe without unnecessary complexity.
