# StudyMate AI Production Improvement Tasks

## Goal

Transform the current prototype into a production-ready, reliable, visual, state-driven adaptive learning system matching the StudyMate AI design:

`User -> Profiler -> Knowledge -> Learning Path -> Planner -> Teaching -> Examiner -> Manager -> CEO`

The mastery loop must return weak topics to Teaching and continue until the learner reaches **85% mastery**.

Production quality means reliable behavior, safe failure handling, maintainable code,
clear documentation, and tests for important paths. It does not mean adding
unnecessary frameworks, abstractions, services, or features.

## Simplicity Rule

- [ ] Prefer the smallest implementation that is clear, testable, and production-safe.
- [ ] Reuse the standard library, existing project helpers, and already-installed libraries before adding dependencies.
- [ ] If a maintained library solves the problem in a few lines, use it instead of recreating it.
- [ ] Do not introduce an abstraction until there is a real repeated use case or a clear testing/reliability benefit.
- [ ] Do not split a small feature into many files without a concrete reason.
- [ ] Avoid speculative features, premature optimization, microservices, and unnecessary configuration.
- [ ] Keep production safeguards; simplicity must not remove validation, security, observability, or recovery.

## Implementation Order

Work rule: complete only one subtask at a time. The next subtask may start only
after the user explicitly says to continue. The active subtask is marked
`[>]`; completed subtasks are marked `[x]`.

## Progress Tracking Rule

After completing each task:

1. Immediately tick every exact checklist item completed by the code change using `[x]`.
2. Leave unfinished items as `[ ]`; never tick an item only because work is planned.
3. Add the validation commands and results under `Validation recorded`.
4. Mark the progress-table task `Complete` only when all required items for that task are ticked.
5. Update the progress table and next task after each completed task.
6. Do not mark any item or task complete until its required validation has passed.

This checklist is the source of truth for implementation progress. Code changes
must be reflected here in the same change.

### Current Progress

| Task | Status | Validation |
|---|---|---|
| 1. Establish a safe baseline | Complete | Unit tests, startup validation, and session guard checks passed |
| 2. Define the workflow state | In progress: 2.4 complete; waiting for approval | 12 workflow tests passed and source compilation passed |
| 3. Implement the eight-agent orchestration | In progress: 3.4 complete; waiting for approval | 16 workflow tests passed and source compilation passed |
| 4. Improve knowledge grounding | In progress: 4.4 complete; waiting for approval | 20 workflow tests passed and source compilation passed |
| 5. Implement the 85% adaptive mastery loop | In progress: 5.4 complete; waiting for approval | 28 workflow tests passed and source compilation passed |
| 6. Build the visual user experience | In progress: 6.3 complete; waiting for approval | 30 tests passed and UI/source compilation passed |
| 7. Add persistence and recovery | In progress: 7.3 complete; waiting for approval | 35 tests passed and source compilation passed |
| 8. Add automated tests | In progress: 8.4 complete; waiting for approval | 46 tests passed and source compilation passed |
| 9. Update documentation | Complete | README claims, setup, workflow, and limitations aligned |
| 10. Production readiness | Complete | 52 tests passed and source compilation passed |

Keep this table current after every implementation task so progress is visible in this file.

### 1. Establish a safe baseline

- [x] Inspect the current source, dependencies, environment configuration, and UI entry points.
- [x] Exclude `.venv`, `venv`, caches, generated files, and secrets from source validation.
- [x] Confirm the current application starts with documented setup steps.
- [x] Record existing behavior before changing it.
- [x] Define the minimum production scope, supported runtime, deployment target, and required user flows.

### 2. Define the workflow state

#### 2.1 Extend the typed workflow state model

- [x] Extend typed models for learner profile, certification, skills, agent results, scores, weak topics, and learning cycles.
- [x] Add focused tests for the new model fields and defaults.
- [x] Run the focused workflow test suite and record the result.

#### 2.2 Define workflow stages

- [x] Define explicit workflow states for all eight agents and the final report card.
- [x] Add tests confirming every required stage exists.

#### 2.3 Define valid transitions

- [x] Define valid state transitions and invalid-transition errors.
- [x] Add tests for valid sequential transitions and rejected skips.

#### 2.4 Replace implicit workflow state

- [x] Replace implicit state inferred from free-form AI text with structured state.
- [x] Validate the integration without changing the user-facing flow.

### 3. Implement the eight-agent orchestration

#### 3.1 Separate agent responsibilities

- [x] Keep the eight agents separate and give each one a single responsibility.
- [x] Register the eight agents and their responsibility descriptions in one central registry.
- [x] Add a focused test confirming unique agents and non-empty responsibilities.

#### 3.2 Add the central orchestrator

- [x] Add a central orchestrator that invokes registered agents in the design order.
- [x] Add a focused test confirming ordered dispatch and state advancement.

#### 3.3 Validate agent handoffs

- [x] Pass structured input and output between agents.
- [x] Validate every agent response before moving to the next state.
- [x] Add tests for structured requests, valid responses, and rejected responses.

#### 3.4 Handle orchestration failures

- [x] Add clear error handling and user-visible recovery messages.
- [x] Preserve the current workflow stage when an agent fails.
- [x] Add a focused test for provider failure reporting and recovery guidance.

### 4. Improve knowledge grounding

#### 4.1 Identify authoritative sources

- [x] Use authoritative certification sources whenever available.
- [x] Add certification-specific official-domain search filters.
- [x] Remove exam-dump wording from generated search queries.
- [x] Add a focused test for authoritative-domain prioritization.

#### 4.2 Preserve source references

- [x] Keep retrieved source references with generated explanations and questions.
- [x] Preserve deduplicated title, URL, and snippet records on each agent.
- [x] Save knowledge-assessment and learning-path source references in session memory.
- [x] Add a focused test for the source-reference shape.

#### 4.3 Validate generated content

- [x] Validate that generated questions match the selected certification and skills.
- [x] Reject missing or unconfigured question skills.
- [x] Reject questions that do not reference their declared skill or certification.
- [x] Add focused tests for valid and invalid generated content.

#### 4.4 Handle unavailable knowledge services

- [x] Add a safe fallback when search or model services are unavailable.
- [x] Return no fake source record when search credentials or results are unavailable.
- [x] Return an explicit knowledge-assessment retry message when the model service fails.
- [x] Never claim Microsoft Foundry IQ integration unless it is actually implemented and tested.
- [x] Update README claims to describe only the implemented SerpAPI search behavior.

### 5. Implement the 85% adaptive mastery loop

#### 5.1 Centralize mastery scoring

- [x] Use one shared mastery threshold constant set to `85`.
- [x] Calculate overall and per-skill scores deterministically in application code.
- [x] Identify weak topics from structured assessment results.

#### 5.2 Focus remediation

- [x] Send only weak topics back to the Teaching Agent.
- [x] Prevent unrelated certification skills from being included in remediation prompts.
- [x] Add focused tests for weak-skill-only and empty-remediation prompts.

#### 5.3 Run the adaptive cycle

- [x] Run Teaching -> Examiner -> Manager -> CEO for each cycle.
- [x] Persist each adaptive-stage transition in structured workflow state.
- [x] Allow completed cycles to return to Teaching for the next cycle.
- [x] Stop at 85% mastery and generate the report card.

#### 5.4 Guard cycle limits

- [x] Add a configurable maximum-cycle safeguard and explain when it is reached.
- [x] Validate the cycle-limit configuration before starting the adaptive loop.

### 6. Build the visual user experience

#### 6.1 Display the workflow

- [x] Add a dashboard matching the design image while retaining the existing terminal interaction.
- [x] Display all eight agent cards in the design order.
- [x] Show the current active agent and completed agents from workflow headers.
- [x] Show mastery percentage and progress bar from score events.

#### 6.2 Display completion states

- [x] Display the adaptive loop and final report card clearly.
- [x] Show the final report card for both mastery success and cycle-limit outcomes.

#### 6.3 Support small screens

- [x] Keep the interface usable on smaller screens.
- [x] Adapt terminal boxes, headers, questions, and learning-path output to the detected terminal width.
- [x] Add a narrow-terminal regression test.

### 7. Add persistence and recovery

#### 7.1 Version saved state

- [x] Store session state using a documented, versioned schema.
- [x] Validate the schema version and required top-level fields before resume.

#### 7.2 Isolate session data

- [x] Prevent one user session from sharing state with another user.
- [x] Namespace saved state by a hashed `STUDYMATE_SESSION_ID`.

#### 7.3 Resume and restart safely

- [x] Support safe resume and restart.
- [x] Handle corrupted or outdated saved state explicitly.

#### 7.4 Keep storage minimal

- [x] Keep progress data outside source-controlled files when appropriate.
- [x] Use the simplest storage appropriate for the deployment size; do not add a database or queue without a demonstrated need.

### 8. Add automated tests

#### 8.1 Test profile and state validation

- [x] Test profile validation and certification selection.
- [x] Test agent state transitions.

#### 8.2 Test mastery behavior

- [x] Test score calculations and the exact 85% boundary.
- [x] Test weak-topic selection.
- [x] Test loop continuation and successful termination.
- [x] Test maximum-cycle behavior.

#### 8.3 Test failure and recovery

- [x] Test malformed agent output and service failures.
- [x] Test session save, resume, and corruption.

#### 8.4 Test web behavior

- [x] Prevent concurrent web sessions from sharing the process-global prototype state.
- [x] Test key API/websocket endpoints and important UI states.

### Validation recorded

- [x] Project source compilation passed while excluding virtual environments.
- [x] Six workflow unit tests passed, including the runtime-config validation check.
- [x] Web session isolation guard is implemented; source compilation and workflow tests pass.
- [x] Browser smoke test confirmed the dashboard renders at `/`.
- [x] Runtime config validation rejects an empty provider configuration with a clear ValueError.
- [x] Subtask 2.1: seven workflow tests passed after adding typed workflow models.
- [x] Subtask 2.2: eight workflow tests passed after formalizing the eight agent stages and report-card stage.
- [x] Subtask 2.3: ten workflow tests passed after enforcing sequential transitions and rejecting skipped/backward transitions.
- [x] Subtask 2.4: twelve workflow tests passed and `workflow.py`/`main.py` compiled after adding structured workflow-state checkpoints and resume serialization.
- [x] Subtask 3.1: thirteen workflow tests passed and `agents.py` compiled after registering eight unique agents with single responsibilities.
- [x] Subtask 3.2: fourteen workflow tests passed and `workflow.py`, `main.py`, and `agents.py` compiled after adding central agent dispatch.
- [x] Subtask 3.3: fifteen workflow tests passed and `workflow.py`/`main.py` compiled after adding structured agent requests and response validation.
- [x] Subtask 3.4: sixteen workflow tests passed and `workflow.py`/`main.py` compiled after adding explicit orchestration failure reporting and user recovery guidance.
- [x] Subtask 4.1: seventeen workflow tests passed and `agents.py` compiled after adding official certification source-domain filtering.
- [x] Subtask 4.2: eighteen workflow tests passed and `agents.py`/`main.py` compiled after preserving source references with knowledge and learning-path outputs.
- [x] Subtask 4.3: nineteen workflow tests passed and `workflow.py`/`main.py` compiled after validating generated questions against certification skills.
- [x] Subtask 4.4: twenty workflow tests passed and `agents.py`/`main.py` compiled after adding explicit unavailable-service fallbacks and removing unsupported Foundry IQ claims.
- [x] Subtask 5.2: twenty-two workflow tests passed and `workflow.py`/`main.py` compiled after restricting teaching remediation prompts to weak skills only.
- [x] Subtask 5.3: twenty-four workflow tests passed and `workflow.py`/`main.py` compiled after tracking Teaching -> Examiner -> Manager -> CEO transitions for each adaptive cycle.
- [x] 5.3 report-card completion: twenty-six workflow tests passed and `workflow.py`/`main.py` compiled after adding deterministic report-card generation at 85% mastery.
- [x] Subtask 5.4: twenty-eight workflow tests passed and `workflow.py`/`main.py` compiled after adding `STUDYMATE_MAX_LEARNING_CYCLES` validation and clear limit messaging.
- [x] Subtask 6.2: `ui.py` and `main.py` compiled after adding explicit adaptive-loop and final report-card displays.
- [x] Subtask 6.3: thirty tests passed and `ui.py`/`main.py` compiled after adding responsive terminal-width handling and narrow-screen regression coverage.
- [x] Subtask 7.1: thirty-two tests passed and `main.py` compiled after adding schema version `1`, required-field validation, and saved-session documentation.
- [x] Subtask 7.2: thirty-three tests passed and `main.py` compiled after adding hashed session-file namespacing and session-isolation coverage.
- [x] Subtask 7.3: thirty-five tests passed and `main.py` compiled after adding explicit corrupted/outdated-session handling and safe restart behavior.
- [x] Subtask 7.4: runtime session/progress files were added to `.gitignore`, README storage guidance was updated, and no database or queue was introduced.
- [x] Subtask 8.1: thirty-seven tests passed and `tasks.py`/`main.py` compiled after adding learner-profile validation, certification-selection coverage, and workflow transition tests.
- [x] Subtask 8.2: forty-one tests passed and `workflow.py`/`main.py` compiled after adding weak-topic, loop-continuation, successful-termination, and maximum-cycle tests.
- [x] Subtask 8.3: forty-three tests passed and `workflow.py`/`main.py` compiled after adding malformed-agent-output, provider-failure, save/resume, and corrupted-session tests.
- [x] Subtask 8.4: forty-six tests passed and `web_app.py`/`ui.py` compiled after adding root endpoint, WebSocket startup/error, and structured UI-event tests.
- [x] Task 9: README claims, environment configuration, local setup, test/start commands, workflow state model, limitations, and fallback behavior were aligned with the implemented application.
- [x] Subtask 10.1: forty-nine tests passed and `web_app.py` compiled after adding safe web logging plus `/healthz` and `/readyz` endpoints.
- [x] Subtask 10.2: fifty tests passed and `agents.py`/`tools/web_search.py` compiled after adding bounded model/search timeouts, configurable retry limits, and actionable provider validation.
- [x] Subtask 10.3: fifty-one tests passed and `main.py`/`web_app.py` compiled after adding atomic session writes, oversized-input rejection, and minimal deployment/rollback guidance.
- [x] Subtask 10.4: fifty-two tests passed and the application compiled after removing unused prototype dependencies, correcting provider configuration documentation, validating WebSocket message types, and documenting bounded runtime cost assumptions.

### 9. Update documentation

#### 9.1 Align README claims

- [x] Update the README to describe only implemented integrations and behavior.

#### 9.2 Document configuration and setup

- [x] Document environment variables without exposing secrets.
- [x] Document local setup, development, testing, and production startup.

#### 9.3 Document workflow and limitations

- [x] Document the eight-agent workflow and state model.
- [x] Document known limitations and fallback behavior.

### 10. Production readiness

#### 10.1 Add observability and health checks

- [x] Add structured application logging without logging secrets or sensitive learner data.
- [x] Add health/readiness checks for the web app and required external services.

#### 10.2 Harden external services

- [x] Add timeouts, bounded retries, and clear failure responses for external APIs.
- [x] Validate configuration at startup with actionable error messages.

#### 10.3 Protect and deploy safely

- [x] Protect user/session data and isolate concurrent sessions.
- [x] Add a minimal deployment and rollback procedure.

#### 10.4 Perform release review

- [x] Review dependencies, exposed endpoints, and secret handling before release.
- [x] Keep performance and cost within the chosen production target without premature optimization.

## Required Validation For Every Change

For every file or code change:

1. Read the affected code and its callers before editing.
2. Make the smallest complete change that solves the task.
3. Run the narrowest relevant formatter, linter, type check, or test.
4. Run an integration check when the change crosses module or UI boundaries.
5. Confirm the application still starts.
6. Confirm the changed behavior works in both success and failure cases.
7. Update related documentation and tests.
8. Record the completed task and validation result in this checklist.
9. Check that the solution is no more complex than necessary.

## Definition of Done

- [ ] The visual workflow matches the design order.
- [ ] Agent communication uses validated structured data.
- [ ] The loop repeats weak-topic learning until 85% mastery or a documented safeguard.
- [ ] The report card accurately reflects the final scores.
- [ ] Tests pass for normal, malformed, unavailable-service, and recovery scenarios.
- [ ] Documentation matches the actual implementation.
- [ ] Production startup, health checks, logging, configuration, and failure handling are documented.
- [ ] The implementation uses the smallest reasonable design and has no unnecessary dependencies or abstractions.
