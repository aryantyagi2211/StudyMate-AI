"""
main.py — StudyMate AI session runner with pixel-style UI
Profiler -> Knowledge Checker -> Learning Path -> Teaching -> Exam loop
"""

import asyncio
import hashlib
import json
import os
import re
import time

from agents import (
    AGENT_REGISTRY,
    ceo_agent, profiler_agent, knowledge_checker,
    learning_path_agent, adaptive_planner, teaching_agent,
    examiner_agent, manager_insights_agent,
)
from tasks import (
    task_ceo, task_profiler, task_knowledge_checker,
    task_learning_path, task_adaptive_plan, task_teaching,
    task_examiner, task_manager_insights,
    set_learner_data, use_demo_data,
)
import tasks
import ui
from workflow import (
    AgentOrchestrator,
    AgentRequest,
    AgentResult,
    MASTERY_THRESHOLD,
    WorkflowStage,
    WorkflowState,
    build_report_card,
    build_remediation_prompt,
    get_max_learning_cycles,
    score_assessment,
    validate_generated_questions,
)


def ask(msg):
    """Keep asking until we get a non-empty answer."""
    while True:
        val = ui.input_prompt(msg).strip()
        if val:
            return val
        ui.warn("Cannot be empty.")

def collect_profile():
    ui.header("PROFILE SETUP")
    name = ask("What's your name?")
    role = ask("What's your role? (e.g., Cloud Engineer, Developer)")
    cert = ask("Which certification? (e.g., AWS-SAA, CCNA, CISSP)").upper()
    ui.ok(f"Setting up your journey for {cert}...")
    return name, role, cert


def choose_mode():
    """Let user choose between custom data or demo mode"""
    ui.header("STUDYMATE AI")
    ui.option_list([
        ("1", "Custom Data (enter your own info)"),
        ("2", "Demo Mode (use sample student)"),
    ])
    print()
    while True:
        choice = ui.input_prompt("Your choice (1 or 2)").strip()
        if choice == "1":
            name, role, cert = collect_profile()
            set_learner_data(name, role, cert)
            ui.ok(f"Profile created for {name}!")
            return "custom"
        elif choice == "2":
            use_demo_data()
            ui.ok(f"Loading demo: {tasks.LEARNER['name']} ({tasks.LEARNER['role']}, {tasks.LEARNER['certification']})")
            return "demo"
        ui.warn("Please enter 1 or 2")


def build_prompt(task, context=""):
    """Turn a task dict into the message we send to an agent"""
    description = task.get("description", "")
    if not description:
        return ""
    prompt = description() if callable(description) else description
    if context:
        prompt = (
            f"Here's what's happened so far in this session:\n{context}\n\n"
            f"---\n\n{prompt}"
        )
    prompt += f"\n\nExpected output: {task.get('expected_output', '')}"
    return prompt


async def run_step(agent, prompt, session=None, agent_name="Agent"):
    """Send one message to an agent and return its reply as plain text.
    Shows a pixel loader while agent is generating."""
    task, stop = await ui.start_loader(f"{agent_name} is generating...")
    try:
        response = await agent.run(prompt, session=session)
        if hasattr(response, 'text'):
            return response.text
        elif hasattr(response, 'content'):
            return str(response.content)
        return str(response)
    finally:
        stop.set()
        await task


def validate_runtime_config():
    """Report a clear startup error before the app enters the AI session."""
    try:
        from agents import validate_runtime_config as _validate
        _validate()
    except Exception as exc:
        ui.warn(str(exc))
        raise


# ── JSON parsing helpers ──────────────────────────────────────────────────

def parse_mcq_json(raw_text):
    """Pull the question list out of whatever the agent returned."""
    if not raw_text:
        return []
    text = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    # Try to find the JSON object in the text
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end > start:
        text = text[start:end + 1]
    try:
        return json.loads(text).get("questions", [])
    except (json.JSONDecodeError, AttributeError):
        # One more shot — grab anything that looks like a JSON block
        match = re.search(r'\{[\s\S]*"questions"[\s\S]*\}', raw_text)
        if match:
            try:
                return json.loads(match.group()).get("questions", [])
            except (json.JSONDecodeError, AttributeError):
                pass
        return []


# ── Knowledge Assessment ──────────────────────────────────────────────────

KC_MAX_RETRIES = 3


def _validate_question_quality(questions, cert_name):
    feedback = []
    if len(questions) < 10:
        feedback.append(f"Only {len(questions)} questions — need exactly 10.")
    vague_count = 0
    for i, q in enumerate(questions[:10]):
        q_text = q.get("question", "").strip()
        opts = q.get("options", [])
        if not q_text or len(q_text) < 15:
            feedback.append(f"Q{i+1}: question too short or empty.")
        if len(opts) < 4:
            feedback.append(f"Q{i+1}: only {len(opts)} options, need 4.")
        opts_lower = [o.lower().strip() for o in opts if o]
        if len(opts_lower) >= 2 and set(opts_lower[:2]) <= {"true", "false", "yes", "no"}:
            feedback.append(f"Q{i+1}: binary True/False or Yes/No options — needs genuine 4-option MCQ.")
        if q_text.lower().startswith(("what is", "define", "explain", "what are")):
            vague_count += 1
    if vague_count > 3:
        feedback.append(f"{vague_count} questions start with 'what is'/'define' etc. Make them scenario-based.")
    feedback.extend(validate_generated_questions(
        questions[:10],
        cert_name,
        tasks.CERT.get("skills", []) if tasks.CERT else [],
    ))
    specific_terms = ["service", "api", "function", "instance", "bucket",
                      "policy", "role", "cluster", "container", "database",
                      "network", "storage", "compute", "iam", "vpc", "s3",
                      "lambda", "azure", "gcp", "aws"]
    specific_count = sum(
        1 for q in questions[:10]
        if any(term in q.get("question", "").lower() for term in specific_terms)
    )
    if specific_count < 5 and len(questions) >= 5:
        feedback.append("Questions are too generic — they don't reference specific technologies.")
    return {
        "passed": not feedback,
        "feedback": "\n".join(feedback) if feedback else "Questions meet quality standards."
    }


async def run_knowledge_assessment():
    """Run the interactive knowledge checker with quality validation loop.
    Retries up to KC_MAX_RETRIES times, creating fresh sessions to force new
    web searches each time until questions pass quality gates."""
    ui.header("KNOWLEDGE CHECKER")

    questions = []
    retries = 0
    additional_instructions = ""

    while retries < KC_MAX_RETRIES:
        retries += 1
        if retries > 1:
            ui.info(f"Regenerating higher quality questions (attempt {retries}/{KC_MAX_RETRIES})...")

        assessment_prompt = build_prompt(task_knowledge_checker)
        if additional_instructions:
            assessment_prompt += f"\n\n--- QUALITY FEEDBACK FROM PREVIOUS ATTEMPT ---\n{additional_instructions}\n\nUse this feedback to find BETTER search results and generate improved questions."

        # Fresh session every retry — forces a new web search
        kc_session = knowledge_checker.create_session()
        try:
            raw = await run_step(
                knowledge_checker,
                assessment_prompt,
                session=kc_session,
                agent_name="Knowledge Checker",
            )
        except Exception as exc:
            ui.warn(f"Knowledge assessment service unavailable: {exc}")
            return {
                "total": 0,
                "correct": 0,
                "percentage": 0,
                "skill_scores": {},
                "weak_skills": [],
                "summary": "Knowledge assessment is unavailable. Please retry when the AI provider is available.",
                "sources": knowledge_checker.get_last_sources(),
            }
        questions = parse_mcq_json(raw)

        if not questions or len(questions) < 5:
            additional_instructions = (
                "The previous output was not usable. Search the web for "
                f"SPECIFIC {tasks.LEARNER['certification']} exam topics, "
                f"services, and real exam questions. Generate exactly 10 "
                f"well-structured MCQs with 4 options each."
            )
            continue

        quality = _validate_question_quality(questions, tasks.LEARNER['certification'])
        if quality["passed"]:
            ui.ok(f"High-quality questions generated (attempt {retries})!")
            break
        else:
            additional_instructions = quality["feedback"]
            ui.warn(f"Quality check failed — {quality['feedback'][:80]}...")

    if not questions or len(questions) < 5:
        ui.warn("Could not generate valid questions after multiple attempts. Using fallback.")
        return {
            "total": 0,
            "correct": 0,
            "percentage": 0,
            "skill_scores": {},
            "weak_skills": [],
            "sources": knowledge_checker.get_last_sources(),
        }

    ui.ok(f"Assessment ready! {len(questions)} questions to test your knowledge.")
    ui.info("Answer each question by typing A, B, C, or D\n")

    results = []
    correct_count = 0

    for q in questions:
        ui.display_question(
            q.get('id', '?'),
            q.get('skill', 'General'),
            q.get('question', ''),
            q.get('options', [])
        )

        while True:
            answer = ui.input_prompt("Your answer (A/B/C/D)").strip().upper()
            if answer in ['A', 'B', 'C', 'D']:
                break
            ui.warn("Please enter A, B, C, or D")

        correct_answer = q.get('correct_answer', '').strip().upper()
        is_correct = (answer == correct_answer)

        if is_correct:
            correct_count += 1
            ui.ok("Correct!")
        else:
            ui.fail(f"Incorrect. The correct answer is: {correct_answer}")

        if q.get('explanation'):
            ui.info(q['explanation'])

        results.append({
            "id": q.get('id'),
            "skill": q.get('skill', 'General'),
            "correct": is_correct
        })

    # Calculate scores deterministically in application code.
    mastery = score_assessment(results)
    total = mastery.total
    percentage = mastery.percentage
    skill_scores = mastery.skill_scores

    # Results display
    ui.header("ASSESSMENT RESULTS")
    ui.score_display(correct_count, total, "Overall")
    print()
    ui.section("Skill Breakdown")
    assessment_summary = []
    for skill, scores in skill_scores.items():
        skill_pct = int((scores['correct'] / scores['total']) * 100)
        if skill_pct >= 80:
            level = "STRONG"
        elif skill_pct >= 60:
            level = "MEDIUM"
        else:
            level = "WEAK"
        bar = ui.progress_bar(scores['correct'], scores['total'], 12,
                              ui.C.GRN if skill_pct >= 80 else ui.C.YLW if skill_pct >= 60 else ui.C.RED)
        print(f'    {ui.c(skill, ui.C.WHT):30s} {bar}  {ui.c(level, ui.C.BLD)}')
        assessment_summary.append(f"{skill}: {skill_pct}% ({level})")

    return {
        "total": total, "correct": correct_count,
        "percentage": percentage, "skill_scores": skill_scores,
        "weak_skills": mastery.weak_skills,
        "summary": "\n".join(assessment_summary),
        "sources": knowledge_checker.get_last_sources(),
    }


# ── Interactive Exam ──────────────────────────────────────────────────────

async def run_exam_interactive():
    """Run interactive exam with 10 MCQ questions, one by one.
    Supports optional timed mode (60s per question)."""
    ui.header("FINAL EXAM - 10 QUESTIONS")

    EXAM_Q_COUNT = 10
    time_limit = 0

    timed_choice = ui.input_prompt("Timed exam? (yes/no, default: no)").strip().lower()
    if timed_choice in ("yes", "y"):
        time_limit = EXAM_Q_COUNT * 60
        ui.info(f"Timed mode: {time_limit // 60} minutes for {EXAM_Q_COUNT} questions.")
        ui.info("Time starts NOW!\n")

    ui.info("All multiple-choice questions with 4 options (A/B/C/D).")
    ui.info("Difficulty: [EASY] (1-3), [MEDIUM] (4-7), [HARD] (8-10)\n")

    examiner_session = examiner_agent.create_session()

    start_prompt = f"""Start the certification exam for {tasks.LEARNER['name']}.

Skills to test: {', '.join(tasks.CERT['skills'])}

You will ask exactly {EXAM_Q_COUNT} MCQ questions. Begin by asking Question 1.
Present each question in a clean, readable format:

Question 1: [EASY]
[question text here]
A) [option A]
B) [option B]
C) [option C]
D) [option D]

Remember to:
- Show difficulty level as [EASY] / [MEDIUM] / [HARD]
- Provide 4 options labeled A, B, C, D
- Ask ONE question at a time
- Do NOT use JSON format — display naturally
- After the student answers, tell them if correct/incorrect with brief explanation
"""

    reply = await run_step(examiner_agent, start_prompt, session=examiner_session, agent_name="Examiner")
    ui.agent_output("Examiner", reply)

    results = {'total': 0, 'correct': 0, 'answers': [], 'timed_out': False}
    start_time = time.time()

    for question_num in range(1, EXAM_Q_COUNT + 1):
        if time_limit:
            elapsed = time.time() - start_time
            remaining = time_limit - elapsed
            if remaining <= 0:
                ui.warn("TIME'S UP!")
                results['timed_out'] = True
                break
            mins, secs = divmod(int(remaining), 60)
            ui.info(f"Time remaining: {mins}:{secs:02d}")

        while True:
            answer = ui.input_prompt("Your answer (A/B/C/D)").strip().upper()
            if answer in ['A', 'B', 'C', 'D']:
                break
            ui.warn("Please enter A, B, C, or D")

        reply = await run_step(examiner_agent, answer, session=examiner_session, agent_name="Examiner")
        ui.agent_output("Examiner", reply)

        if "[✓]" in reply or "correct" in reply.lower():
            results['correct'] += 1

        results['total'] += 1
        results['answers'].append({'question_num': question_num, 'answer': answer, 'feedback': reply})

    summary_prompt = f"""Summarize the exam results for {tasks.LEARNER['name']}:
- MCQ Score: {results['correct']}/{results['total']}
- Overall Performance
- Skills that need more work
- Keep it short (3-4 sentences)"""

    if results['timed_out']:
        summary_prompt += "\n\nThe student ran out of time. Note that not all questions were answered."

    final_summary = await run_step(examiner_agent, summary_prompt, session=examiner_session, agent_name="Examiner")
    ui.header("FINAL EXAM RESULTS")
    ui.result_box(final_summary)

    _record_exam(tasks.LEARNER['certification'], results['correct'], results['total'])
    return final_summary


# ── Progress Tracking ───────────────────────────────────────────────────

PROGRESS_FILE = ".studymate_progress.json"


def _load_progress():
    try:
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"sessions": []}


def _save_progress(data):
    try:
        with open(PROGRESS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def _record_exam(cert, score, total):
    data = _load_progress()
    data["sessions"].append({
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "cert": cert,
        "score": score,
        "total": total,
        "pct": int(score / total * 100) if total > 0 else 0,
    })
    _save_progress(data)


def _show_progress():
    data = _load_progress()
    if not data["sessions"]:
        return
    grouped = {}
    for s in data["sessions"]:
        grouped.setdefault(s["cert"], []).append(s)
    ui.header("YOUR PROGRESS")
    for cert, entries in grouped.items():
        print(f"  {ui.c(cert, ui.C.CYN)}:")
        for e in entries:
            pct = e["pct"]
            filled = pct // 5
            bar = (ui.c("#" * filled, ui.C.GRN if pct >= 80 else ui.C.YLW if pct >= 60 else ui.C.RED)
                   + ui.c("." * (20 - filled), ui.C.GRY))
            print(f"    {e['date']}  [{bar}] {pct}%")
        if len(entries) > 1:
            trend = entries[-1]["pct"] - entries[0]["pct"]
            sign = "+" if trend > 0 else ""
            print(f"    {ui.c('Trend:', ui.C.WHT)} {sign}{trend}%")
        print()


# ── Session Save/Resume ─────────────────────────────────────────────────

SESSION_FILE = ".studymate_session.json"
SESSION_SCHEMA_VERSION = 1
SESSION_ID_ENV = "STUDYMATE_SESSION_ID"


def session_file_for(session_id):
    """Return a filesystem-safe session path for an isolated session ID."""
    normalized = str(session_id).strip()
    if not normalized:
        raise ValueError(f"{SESSION_ID_ENV} must not be empty.")
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return f".studymate_session.{digest}.json"


configured_session_id = os.getenv(SESSION_ID_ENV)
if configured_session_id:
    SESSION_FILE = session_file_for(configured_session_id)


def _build_saved_state(memory):
    return {
        "schema_version": SESSION_SCHEMA_VERSION,
        "learner": tasks.LEARNER,
        "cert": tasks.CERT,
        "memory": memory,
    }


def save_state(memory):
    state = _build_saved_state(memory)
    temp_file = f"{SESSION_FILE}.tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(temp_file, SESSION_FILE)
    except OSError:
        try:
            os.remove(temp_file)
        except FileNotFoundError:
            pass
        raise


def _load_workflow_state(memory):
    saved_state = memory.get("workflow_state")
    if saved_state is None:
        return WorkflowState()
    return WorkflowState.from_dict(saved_state)


def _save_workflow_state(memory, workflow_state):
    memory["workflow_state"] = workflow_state.to_dict()


def load_state():
    try:
        with open(SESSION_FILE) as f:
            state = json.load(f)
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("Saved session is corrupted and cannot be resumed.") from exc
    if not isinstance(state, dict):
        raise ValueError("Saved session must be a JSON object.")
    if state.get("schema_version") != SESSION_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported saved session schema version: "
            f"{state.get('schema_version', 'missing')}."
        )
    for field in ("learner", "cert", "memory"):
        if field not in state:
            raise ValueError(f"Saved session is missing required field: {field}.")
    if not isinstance(state["learner"], dict) or not isinstance(state["cert"], dict):
        raise ValueError("Saved session learner and certification data are invalid.")
    if not isinstance(state["memory"], dict):
        raise ValueError("Saved session memory data is invalid.")
    for field in ("name", "role", "certification"):
        if not str(state["learner"].get(field, "")).strip():
            raise ValueError(f"Saved session learner data is missing: {field}.")
    return state


def clear_state():
    try:
        os.remove(SESSION_FILE)
    except FileNotFoundError:
        pass


# ── Main Session ──────────────────────────────────────────────────────────

async def run_studymate():
    try:
        saved = load_state()
    except ValueError as exc:
        ui.warn(f"Cannot resume saved session: {exc}")
        ui.info("The saved session will be discarded so you can start safely.")
        clear_state()
        saved = None
    if saved:
        cont = ui.input_prompt("Resume previous session? (yes/no)").strip().lower()
        if cont in ("yes", "y"):
            tasks.set_learner_data(saved["learner"]["name"], saved["learner"]["role"], saved["learner"]["certification"])
            tasks.CERT = saved["cert"]
            memory = saved["memory"]
            ui.ok(f"Resuming session for {tasks.LEARNER['name']}.")
        else:
            clear_state()
            choose_mode()
            memory = {}
    else:
        choose_mode()
        memory = {}

    workflow_state = _load_workflow_state(memory)
    planner_session = None

    async def run_registered_agent(agent, request: AgentRequest):
        session = planner_session if agent is adaptive_planner else None
        return await run_step(
            agent,
            request.prompt,
            session=session,
            agent_name=agent.name,
        )

    def report_orchestration_error(stage, message):
        ui.warn(message)
        ui.info(
            f"{stage.value.title()} could not continue. "
            "Check the provider configuration or retry the session."
        )

    orchestrator = AgentOrchestrator(
        state=workflow_state,
        agents=AGENT_REGISTRY,
        runner=run_registered_agent,
        on_error=report_orchestration_error,
    )
    _show_progress()
    ui.separator()
    ui.info(f"Launching multi-agent system for {tasks.LEARNER['name']}...")

    # ── Profiler ──
    if "profile" not in memory:
        ui.header(f"PROFILER — Getting to know {tasks.LEARNER['name']}")
        profiler_session = profiler_agent.create_session()
        reply = await run_step(profiler_agent, build_prompt(task_profiler), session=profiler_session, agent_name="Profiler")
        ui.agent_output("Profiler", reply)
        ui.info("Reply below — type 'done' when ready to move on.\n")

        for _ in range(4):
            student_reply = ui.input_prompt("You").strip()
            if not student_reply or student_reply.lower() in ("done", "skip", "next"):
                break
            reply = await run_step(profiler_agent, student_reply, session=profiler_session, agent_name="Profiler")
            ui.agent_output("Profiler", reply)

        memory["profile"] = await run_step(
            profiler_agent,
            "In 2-3 sentences, summarize this student's motivation, mindset, and "
            "what direction we should set for their learning journey. This is for "
            "the next agent, not the student — no greetings, just the summary.",
            session=profiler_session, agent_name="Profiler",
        )
        if workflow_state.current_stage != WorkflowStage.PROFILER:
            raise ValueError("Workflow state does not match the profiler checkpoint.")
        workflow_state.complete_current_stage()
        _save_workflow_state(memory, workflow_state)
        save_state(memory)

    # ── Knowledge Checker ──
    if "knowledge" not in memory:
        assessment_results = await run_knowledge_assessment()
        memory["knowledge"] = assessment_results["summary"]
        memory["knowledge_sources"] = assessment_results.get("sources", [])
        if workflow_state.current_stage != WorkflowStage.KNOWLEDGE:
            raise ValueError("Workflow state does not match the knowledge checkpoint.")
        workflow_state.complete_current_stage()
        _save_workflow_state(memory, workflow_state)
        save_state(memory)

    # ── Learning Path ──
    if "learning_path" not in memory:
        ui.header("LEARNING PATH")
        learning_path_result = await orchestrator.run_stage(
            WorkflowStage.LEARNING_PATH,
            build_prompt(task_learning_path, memory["knowledge"]),
            context={"knowledge": memory["knowledge"]},
        )
        memory["learning_path"] = learning_path_result.content
        memory["learning_path_sources"] = learning_path_agent.get_last_sources()
        ui.display_learning_path(memory["learning_path"])

        cont = ui.input_prompt("Continue to Adaptive Planner? (yes/no)").strip().lower()
        if cont not in ['yes', 'y']:
            ui.warn("Session paused.")
            return

        _save_workflow_state(memory, workflow_state)
        save_state(memory)

    # ── Adaptive Planner ──
    if "plan" not in memory:
        ui.header("ADAPTIVE PLANNER")
        planner_session = adaptive_planner.create_session()
        planner_result = await orchestrator.run_stage(
            WorkflowStage.PLANNER,
            build_prompt(task_adaptive_plan, memory["learning_path"]),
            context={"learning_path": memory["learning_path"]},
        )
        reply = planner_result.content
        ui.agent_output("Adaptive Planner", reply)

        questions_answered = 0
        for _ in range(5):
            student_reply = ui.input_prompt("").strip()
            if not student_reply:
                ui.warn("Please provide an answer.")
                continue
            reply = await run_step(adaptive_planner, student_reply, session=planner_session, agent_name="Adaptive Planner")
            ui.agent_output("Adaptive Planner", reply)
            questions_answered += 1
            if any(word in reply.lower() for word in ["schedule", "daily study time", "best time:", "skip days:"]):
                break
            if questions_answered >= 3:
                reply = await run_step(adaptive_planner, "Based on my answers, please create my 1-week study schedule now.", session=planner_session, agent_name="Adaptive Planner")
                ui.agent_output("Adaptive Planner", reply)
                break

        memory["plan"] = reply
        _save_workflow_state(memory, workflow_state)
        save_state(memory)

    # ── Adaptive Learning Loop ──
    max_iterations = get_max_learning_cycles()
    passing_score = MASTERY_THRESHOLD
    current_score = memory.get("current_score", 0)
    weak_skills = memory.get("weak_skills", [])
    ceo_session = ceo_agent.create_session()
    iteration = memory.get("cycle_count", 0)

    while iteration < max_iterations:
        if current_score >= passing_score and not weak_skills:
            ui.header("STUDENT PASSED")
            break

        iteration += 1

        if iteration <= memory.get("cycle_count", 0):
            continue

        workflow_state.begin_adaptive_cycle()
        ui.header(f"LEARNING CYCLE {iteration}")
        ui.adaptive_cycle_status(iteration, max_iterations, current_score, weak_skills)

        # Teaching Agent
        ui.header(f"TEACHING SESSION #{iteration}")
        ui.info("One topic at a time. [doubt] to ask questions, [next] to continue.\n")
        teaching_session = teaching_agent.create_session()

        focus_prompt = build_remediation_prompt(weak_skills)

        reply = await run_step(teaching_agent, build_prompt(task_teaching, focus_prompt), session=teaching_session, agent_name="Teaching Agent")
        ui.agent_output("Teaching Agent", reply)

        teaching_complete = False
        while not teaching_complete:
            ui.teaching_options()
            choice = ui.input_prompt("Your choice (doubt / next)").strip().lower()

            if choice in ("doubt", "d"):
                doubt = ui.input_prompt("Describe your doubt (or 'cancel')").strip()
                if doubt.lower() == "cancel":
                    continue
                reply = await run_step(teaching_agent, f"I have a doubt: {doubt}", session=teaching_session, agent_name="Teaching Agent")
                ui.agent_output("Teaching Agent", reply)
                # Keep clarifying until the student is happy
                while True:
                    satisfied = ui.input_prompt("Is your doubt cleared? (yes / no)").strip().lower()
                    if satisfied.startswith("y"):
                        break
                    if not satisfied.startswith("n"):
                        ui.warn("Please answer 'yes' or 'no'")
                        continue
                    followup = ui.input_prompt("What's still unclear? (or 'cancel')").strip()
                    if followup.lower() == "cancel":
                        break
                    reply = await run_step(teaching_agent, f"I'm still confused about: {followup}. Please explain differently with another example.", session=teaching_session, agent_name="Teaching Agent")
                    ui.agent_output("Teaching Agent", reply)

            elif choice in ("next", "n"):
                reply = await run_step(teaching_agent, "I understand this topic. Go to the NEXT topic.", session=teaching_session, agent_name="Teaching Agent")
                ui.agent_output("Teaching Agent", reply)
                if "all topics complete" in reply.lower():
                    teaching_complete = True
                    ui.ok("All weak skills have been taught!")
            else:
                ui.warn("Please type 'doubt' or 'next'")

        memory["teaching"] = reply
        workflow_state.complete_adaptive_stage(WorkflowStage.TEACHING)
        _save_workflow_state(memory, workflow_state)
        save_state(memory)

        # Examiner
        memory["exam"] = await run_exam_interactive()
        workflow_state.complete_adaptive_stage(WorkflowStage.EXAMINER)
        _save_workflow_state(memory, workflow_state)
        save_state(memory)

        # Manager Insights
        ui.header("MANAGER INSIGHTS")
        memory["insights"] = await run_step(
            manager_insights_agent,
            build_prompt(task_manager_insights, f"{memory['exam']}\n\nIteration: {iteration}"),
            agent_name="Manager Insights"
        )
        ui.result_box(memory["insights"])
        workflow_state.complete_adaptive_stage(WorkflowStage.MANAGER)
        _save_workflow_state(memory, workflow_state)
        save_state(memory)

        # CEO Decision
        ui.header(f"CEO DECISION - Cycle {iteration}")
        score_match = re.search(r'(\d+)%', memory["insights"])
        if not score_match:
            ui.warn("Could not parse score from manager insights.")
        current_score = int(score_match.group(1)) if score_match else 0

        weak_skills = []
        if "weak" in memory["insights"].lower() or "struggle" in memory["insights"].lower():
            for skill in tasks.CERT['skills']:
                if skill.lower() in memory["insights"].lower():
                    weak_skills.append(skill)

        decision_prompt = f"""Iteration {iteration} complete.

Student score: {current_score}%
Weak skills: {', '.join(weak_skills) if weak_skills else 'None identified'}

Manager Insights:
{memory['insights']}

Make your decision:
- If score >= {MASTERY_THRESHOLD}% and no major weak areas: CONGRATULATE and say they're ready to advance
- If score < {MASTERY_THRESHOLD}% or weak skills exist: Say we'll do another teaching cycle on [specific skills]

Keep response SHORT (2-3 sentences)."""

        ceo_decision = await run_step(ceo_agent, decision_prompt, session=ceo_session, agent_name="CEO")
        ui.agent_output("CEO", ceo_decision)
        workflow_state.complete_adaptive_stage(WorkflowStage.CEO)

        # Save cycle progress
        memory["cycle_count"] = iteration
        memory["current_score"] = current_score
        memory["weak_skills"] = weak_skills
        save_state(memory)

        if current_score >= passing_score and not weak_skills:
            ui.header("STUDENT PASSED")
            break
        else:
            ui.score_display(current_score, 100, "Current Score")
            if weak_skills:
                ui.info(f"Focusing on: {', '.join(weak_skills)}")
            ui.info(f"Starting Learning Cycle {iteration + 1}...")
            await asyncio.sleep(2)

    if iteration >= max_iterations and not (current_score >= passing_score and not weak_skills):
        ui.warn(
            f"Maximum learning cycles reached ({max_iterations}). "
            "Mastery was not reached; review the weak skills and restart when ready."
        )

    # Final CEO Decision
    report_card_data = build_report_card(current_score, iteration, weak_skills)
    memory["report_card"] = report_card_data
    _save_workflow_state(memory, workflow_state)
    save_state(memory)
    ui.report_card(report_card_data)

    if "ceo_decision" not in memory:
        ui.header("FINAL DECISION")
        final_prompt = f"""Final session complete after {iteration} learning cycle(s).

Student's journey:
- Final score: {current_score}%
- Cycles completed: {iteration}
- Status: {'PASSED' if current_score >= passing_score else 'NEEDS MORE TIME'}

Provide your final decision and next steps for {tasks.LEARNER['name']}.
Keep it SHORT and encouraging (2-3 sentences)."""

        memory["ceo_decision"] = await run_step(ceo_agent, final_prompt, session=ceo_session, agent_name="CEO")
        ui.result_box(memory["ceo_decision"])
        clear_state()

    ui.header("SESSION COMPLETE")
    ui.ok("Thank you for using StudyMate AI!")


if __name__ == "__main__":
    try:
        asyncio.run(run_studymate())
    except KeyboardInterrupt:
        ui.warn("Session interrupted.")
    except Exception as e:
        ui.warn(f"Unexpected error: {e}")
