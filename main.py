"""
main.py — StudyMate AI session runner with pixel-style UI
Profiler -> Knowledge Checker -> Learning Path -> Teaching -> Exam loop
"""

import asyncio
import json
import re

from agents import (
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


def get_custom_data():
    """Ask user for their custom data one by one"""
    ui.header("PROFILE SETUP")
    name = ui.input_prompt("What's your name?").strip()
    while not name:
        ui.warn("Name cannot be empty.")
        name = ui.input_prompt("What's your name?").strip()

    role = ui.input_prompt("What's your role? (e.g., Cloud Engineer, Developer)").strip()
    while not role:
        ui.warn("Role cannot be empty.")
        role = ui.input_prompt("What's your role?").strip()

    cert = ui.input_prompt("Which certification? (e.g., AWS-SAA, CCNA, CISSP)").strip().upper()
    while not cert:
        ui.warn("Certification cannot be empty.")
        cert = ui.input_prompt("Which certification?").strip().upper()

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
            name, role, cert = get_custom_data()
            set_learner_data(name, role, cert)
            ui.ok(f"Profile created for {name}!")
            return "custom"
        elif choice == "2":
            use_demo_data()
            import tasks
            ui.ok(f"Loading demo: {tasks.LEARNER['name']} ({tasks.LEARNER['role']}, {tasks.LEARNER['certification']})")
            return "demo"
        ui.warn("Please enter 1 or 2")


def build_prompt(task, context=""):
    """Turn a task dict into the message we send to an agent"""
    description = task["description"]() if callable(task["description"]) else task["description"]
    prompt = description
    if context:
        prompt = (
            f"Here's what's happened so far in this session:\n{context}\n\n"
            f"---\n\n{prompt}"
        )
    prompt += f"\n\nExpected output: {task['expected_output']}"
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


# ── JSON parsing helpers ──────────────────────────────────────────────────

def parse_mcq_json(raw_text):
    """Try to extract MCQ questions from the agent's reply."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    start_idx = cleaned.find('{')
    end_idx = cleaned.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        cleaned = cleaned[start_idx:end_idx + 1]
    try:
        data = json.loads(cleaned)
        return data.get("questions", [])
    except (json.JSONDecodeError, AttributeError) as e:
        ui.warn(f"Could not parse JSON: {e}")
        json_pattern = r'\{[\s\S]*"questions"[\s\S]*\}'
        match = re.search(json_pattern, raw_text)
        if match:
            try:
                data = json.loads(match.group())
                return data.get("questions", [])
            except:
                pass
        return []


def parse_exam_json(raw_text):
    """Try to pull a list of questions out of the agent's reply."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    json_matches = re.findall(r'\{[\s\S]*?"questions"[\s\S]*?\}', cleaned)
    if json_matches:
        cleaned = json_matches[0]
    try:
        data = json.loads(cleaned)
        questions = data.get("questions", [])
        valid = [q for q in questions if "question" in q and ("options" in q or "type" in q)]
        return valid
    except (json.JSONDecodeError, AttributeError) as e:
        ui.warn(f"JSON Parse Error: {e}")
        return []


def to_option_text(value, options):
    letters = {chr(65 + i): option for i, option in enumerate(options)}
    return letters.get(value.strip().upper(), value)


# ── Knowledge Assessment ──────────────────────────────────────────────────

async def run_knowledge_assessment():
    """Run the interactive knowledge checker with 10 MCQs presented one by one."""
    ui.header("KNOWLEDGE CHECKER")

    assessment_prompt = build_prompt(task_knowledge_checker)
    raw = await run_step(knowledge_checker, assessment_prompt, agent_name="Knowledge Checker")
    questions = parse_mcq_json(raw)

    if not questions or len(questions) < 5:
        ui.warn("Couldn't generate proper assessment. Raw response:")
        print(raw)
        return {"total": 0, "correct": 0, "percentage": 0, "skill_scores": {}}

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

    # Calculate scores
    total = len(results)
    percentage = int((correct_count / total) * 100) if total > 0 else 0

    skill_scores = {}
    for r in results:
        skill = r['skill']
        if skill not in skill_scores:
            skill_scores[skill] = {'correct': 0, 'total': 0}
        skill_scores[skill]['total'] += 1
        if r['correct']:
            skill_scores[skill]['correct'] += 1

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
            rec = "Just a quick refresher needed."
        elif skill_pct >= 60:
            level = "MEDIUM"
            rec = "Understands basics but needs more practice."
        else:
            level = "WEAK"
            rec = "Needs focused teaching from the ground up."
        bar = ui.progress_bar(scores['correct'], scores['total'], 12,
                              ui.C.GRN if skill_pct >= 80 else ui.C.YLW if skill_pct >= 60 else ui.C.RED)
        print(f'    {ui.c(skill, ui.C.WHT):30s} {bar}  {ui.c(level, ui.C.BLD)}')
        assessment_summary.append(f"{skill}: {skill_pct}% ({level})")

    return {
        "total": total, "correct": correct_count,
        "percentage": percentage, "skill_scores": skill_scores,
        "summary": "\n".join(assessment_summary)
    }


# ── Interactive Exam ──────────────────────────────────────────────────────

async def run_exam_interactive():
    """Run interactive exam with 10 MCQ questions, one by one."""
    ui.header("FINAL EXAM - 10 QUESTIONS")
    ui.info("All multiple-choice questions with 4 options (A/B/C/D).")
    ui.info("Difficulty: [EASY] (1-3), [MEDIUM] (4-7), [HARD] (8-10)\n")

    examiner_session = examiner_agent.create_session()

    EXAM_Q_COUNT = 10

    start_prompt = f"""Start the certification exam for {tasks.LEARNER['name']}.

Skills to test: {', '.join(tasks.CERT['skills'])}

You will ask exactly {EXAM_Q_COUNT} MCQ questions. Begin by asking Question 1.
Remember to:
- Show difficulty level
- Provide 4 options (A/B/C/D) with correct_answer
- Ask ONE question at a time
- Use JSON format for easy parsing:
  {{"question": "...", "options": ["...", "..."], "correct_answer": "A", "skill": "...", "difficulty": "EASY"}}"""

    reply = await run_step(examiner_agent, start_prompt, session=examiner_session, agent_name="Examiner")
    ui.agent_output("Examiner", reply)

    results = {'total': EXAM_Q_COUNT, 'correct': 0, 'answers': []}

    for question_num in range(1, EXAM_Q_COUNT + 1):
        while True:
            answer = ui.input_prompt("Your answer (A/B/C/D)").strip().upper()
            if answer in ['A', 'B', 'C', 'D']:
                break
            ui.warn("Please enter A, B, C, or D")

        reply = await run_step(examiner_agent, answer, session=examiner_session, agent_name="Examiner")
        ui.agent_output("Examiner", reply)

        if "[✓]" in reply or "correct" in reply.lower():
            results['correct'] += 1

        results['answers'].append({'question_num': question_num, 'answer': answer, 'feedback': reply})

    summary_prompt = f"""Summarize the exam results for {tasks.LEARNER['name']}:
- MCQ Score: {results['correct']}/{EXAM_Q_COUNT}
- Overall Performance
- Skills that need more work
- Keep it short (3-4 sentences)"""

    final_summary = await run_step(examiner_agent, summary_prompt, session=examiner_session, agent_name="Examiner")
    ui.header("FINAL EXAM RESULTS")
    ui.result_box(final_summary)
    return final_summary
    return final_summary


# ── Main Session ──────────────────────────────────────────────────────────

async def run_studymate():
    mode = choose_mode()
    memory = {}

    ui.separator()
    ui.info(f"Launching multi-agent system for {tasks.LEARNER['name']}...")

    # ── Profiler ──
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

    # ── Knowledge Checker ──
    assessment_results = await run_knowledge_assessment()
    memory["knowledge"] = assessment_results["summary"]

    # ── Learning Path ──
    ui.header("LEARNING PATH")
    memory["learning_path"] = await run_step(
        learning_path_agent, build_prompt(task_learning_path, memory["knowledge"]),
        agent_name="Learning Path"
    )
    ui.display_learning_path(memory["learning_path"])

    cont = ui.input_prompt("Continue to Adaptive Planner? (yes/no)").strip().lower()
    if cont not in ['yes', 'y']:
        ui.warn("Session paused.")
        return

    # ── Adaptive Planner ──
    ui.header("ADAPTIVE PLANNER")
    planner_session = adaptive_planner.create_session()
    reply = await run_step(adaptive_planner, build_prompt(task_adaptive_plan, memory["learning_path"]), session=planner_session, agent_name="Adaptive Planner")
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

    # ── Adaptive Learning Loop ──
    max_iterations = 5
    iteration = 0
    passing_score = 80
    weak_skills = []
    ceo_session = ceo_agent.create_session()

    while iteration < max_iterations:
        iteration += 1
        ui.header(f"LEARNING CYCLE {iteration}")

        # Teaching Agent
        ui.header(f"TEACHING SESSION #{iteration}")
        ui.info("One topic at a time. [doubt] to ask questions, [next] to continue.\n")
        teaching_session = teaching_agent.create_session()

        if weak_skills:
            focus_prompt = f"Weak skills to teach (in order): {', '.join(weak_skills)}."
        else:
            focus_prompt = memory["knowledge"]

        reply = await run_step(teaching_agent, build_prompt(task_teaching, focus_prompt), session=teaching_session, agent_name="Teaching Agent")
        ui.agent_output("Teaching Agent", reply)

        teaching_complete = False
        while not teaching_complete:
            ui.teaching_options()
            choice = ui.input_prompt("Your choice (doubt / next)").strip().lower()

            if choice in ("doubt", "d"):
                doubt_input = ui.input_prompt("Describe your doubt (or 'cancel')").strip()
                if doubt_input.lower() == "cancel":
                    continue
                reply = await run_step(teaching_agent, f"I have a doubt: {doubt_input}", session=teaching_session, agent_name="Teaching Agent")
                ui.agent_output("Teaching Agent", reply)

                while True:
                    satisfied = ui.input_prompt("Is your doubt cleared? (yes / no)").strip().lower()
                    if satisfied.startswith("y"):
                        break
                    elif satisfied.startswith("n"):
                        more_input = ui.input_prompt("What's still unclear? (or 'cancel')").strip()
                        if more_input.lower() == "cancel":
                            break
                        reply = await run_step(
                            teaching_agent,
                            f"I'm still confused about: {more_input}. Please explain differently with another example.",
                            session=teaching_session, agent_name="Teaching Agent"
                        )
                        ui.agent_output("Teaching Agent", reply)
                    else:
                        ui.warn("Please answer 'yes' or 'no'")

            elif choice in ("next", "n"):
                reply = await run_step(teaching_agent, "I understand this topic. Go to the NEXT topic.", session=teaching_session, agent_name="Teaching Agent")
                ui.agent_output("Teaching Agent", reply)
                if "all topics complete" in reply.lower():
                    teaching_complete = True
                    ui.ok("All weak skills have been taught!")
            else:
                ui.warn("Please type 'doubt' or 'next'")

        memory["teaching"] = reply

        # Examiner
        memory["exam"] = await run_exam_interactive()

        # Manager Insights
        ui.header("MANAGER INSIGHTS")
        memory["insights"] = await run_step(
            manager_insights_agent,
            build_prompt(task_manager_insights, f"{memory['exam']}\n\nIteration: {iteration}"),
            agent_name="Manager Insights"
        )
        ui.result_box(memory["insights"])

        # CEO Decision
        ui.header(f"CEO DECISION - Cycle {iteration}")
        score_match = re.search(r'(\d+)%', memory["insights"])
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
- If score >= 80% and no major weak areas: CONGRATULATE and say they're ready to advance
- If score < 80% or weak skills exist: Say we'll do another teaching cycle on [specific skills]

Keep response SHORT (2-3 sentences)."""

        ceo_decision = await run_step(ceo_agent, decision_prompt, session=ceo_session, agent_name="CEO")
        ui.agent_output("CEO", ceo_decision)

        if current_score >= passing_score and not weak_skills:
            ui.header("STUDENT PASSED")
            break
        else:
            ui.score_display(current_score, 100, "Current Score")
            if weak_skills:
                ui.info(f"Focusing on: {', '.join(weak_skills)}")
            ui.info(f"Starting Learning Cycle {iteration + 1}...")
            await asyncio.sleep(2)

    # Final CEO Decision
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

    ui.header("SESSION COMPLETE")
    ui.ok("Thank you for using StudyMate AI!")


if __name__ == "__main__":
    asyncio.run(run_studymate())
