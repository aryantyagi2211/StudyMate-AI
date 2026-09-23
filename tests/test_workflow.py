import unittest
import asyncio
import importlib
import json
import tempfile
from unittest.mock import patch

import agents
search_tool = importlib.import_module("tools.web_search")
from workflow import (
    AgentResult,
    AgentExecutionError,
    AgentRequest,
    AGENT_STAGES,
    AgentOrchestrator,
    Certification,
    LearnerProfile,
    LearningCycle,
    MASTERY_THRESHOLD,
    MAX_LEARNING_CYCLES,
    WorkflowState,
    WorkflowStage,
    build_report_card,
    build_remediation_prompt,
    can_start_next_cycle,
    get_max_learning_cycles,
    score_assessment,
    validate_generated_questions,
)


class WorkflowTests(unittest.TestCase):
    def test_profile_validation_rejects_missing_required_fields(self):
        import tasks

        with self.assertRaisesRegex(ValueError, "name"):
            tasks.validate_learner_data("", "Developer", "AZ-204")
        with self.assertRaisesRegex(ValueError, "certification"):
            tasks.validate_learner_data("Test Learner", "Developer", " ")

    def test_certification_selection_supports_known_and_custom_certifications(self):
        import tasks

        tasks.set_learner_data("Test Learner", "Developer", "AZ-204")
        self.assertEqual(tasks.LEARNER["certification"], "AZ-204")
        self.assertIn("skills", tasks.CERT)

        tasks.set_learner_data("Test Learner", "Developer", "CUSTOM-101")
        self.assertEqual(tasks.CERT["full_name"], "CUSTOM-101 Certification")
        self.assertTrue(tasks.CERT["skills"])

    def test_saved_session_has_versioned_schema(self):
        import main

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as handle:
            json.dump(
                {
                    "schema_version": main.SESSION_SCHEMA_VERSION,
                    "learner": {
                        "name": "Test Learner",
                        "role": "Developer",
                        "certification": "AZ-204",
                    },
                    "cert": {},
                    "memory": {},
                },
                handle,
            )
            path = handle.name
        try:
            with patch.object(main, "SESSION_FILE", path):
                self.assertEqual(main.load_state()["schema_version"], 1)
        finally:
            import os
            os.remove(path)

    def test_saved_session_rejects_unknown_schema_version(self):
        import main

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as handle:
            json.dump({"schema_version": 99}, handle)
            path = handle.name
        try:
            with patch.object(main, "SESSION_FILE", path):
                with self.assertRaisesRegex(ValueError, "Unsupported saved session schema"):
                    main.load_state()
        finally:
            import os
            os.remove(path)

    def test_corrupted_saved_session_is_rejected_explicitly(self):
        import main

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as handle:
            handle.write("{not valid json")
            path = handle.name
        try:
            with patch.object(main, "SESSION_FILE", path):
                with self.assertRaisesRegex(ValueError, "corrupted"):
                    main.load_state()
        finally:
            import os
            os.remove(path)

    def test_saved_session_requires_learner_identity_fields(self):
        import main

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as handle:
            json.dump(
                {
                    "schema_version": main.SESSION_SCHEMA_VERSION,
                    "learner": {},
                    "cert": {},
                    "memory": {},
                },
                handle,
            )
            path = handle.name
        try:
            with patch.object(main, "SESSION_FILE", path):
                with self.assertRaisesRegex(ValueError, "learner data is missing"):
                    main.load_state()
        finally:
            import os
            os.remove(path)

    def test_session_ids_produce_isolated_files(self):
        import main

        first = main.session_file_for("user-one")
        second = main.session_file_for("user-two")
        self.assertNotEqual(first, second)
        self.assertNotIn("user-one", first)
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            main.session_file_for(" ")

    def test_mastery_threshold_is_85_percent(self):
        self.assertEqual(MASTERY_THRESHOLD, 85)

    def test_exactly_85_percent_is_mastered_when_no_skill_is_weak(self):
        result = score_assessment(
            [{"skill": "Storage", "correct": True}] * 17
            + [{"skill": "Storage", "correct": False}] * 3
        )
        self.assertEqual(result.percentage, 85)
        self.assertTrue(result.mastered)

    def test_below_85_percent_identifies_weak_skills(self):
        result = score_assessment([
            {"skill": "Functions", "correct": True},
            {"skill": "Functions", "correct": False},
        ])
        self.assertEqual(result.percentage, 50)
        self.assertEqual(result.weak_skills, ["Functions"])
        self.assertFalse(result.mastered)

    def test_weak_topic_selection_uses_per_skill_threshold(self):
        result = score_assessment(
            [{"skill": "Storage", "correct": True}] * 17
            + [{"skill": "Storage", "correct": False}] * 3
            + [{"skill": "Functions", "correct": True}] * 4
            + [{"skill": "Functions", "correct": False}],
        )
        self.assertEqual(result.weak_skills, ["Functions"])
        self.assertEqual(result.skill_scores["Storage"], {"correct": 17, "total": 20})

    def test_empty_assessment_is_not_mastered(self):
        result = score_assessment([])
        self.assertEqual((result.total, result.correct, result.percentage), (0, 0, 0))
        self.assertFalse(result.mastered)

    def test_cycle_limit_prevents_infinite_loop(self):
        result = score_assessment([{"skill": "Storage", "correct": False}])
        self.assertTrue(can_start_next_cycle(result, MAX_LEARNING_CYCLES - 1))
        self.assertFalse(can_start_next_cycle(result, MAX_LEARNING_CYCLES))

    def test_cycle_limit_can_be_configured_and_validated(self):
        self.assertEqual(get_max_learning_cycles("3"), 3)
        with self.assertRaisesRegex(ValueError, "positive integer"):
            get_max_learning_cycles("0")
        with self.assertRaisesRegex(ValueError, "positive integer"):
            get_max_learning_cycles("invalid")

    def test_non_mastered_result_continues_before_cycle_limit(self):
        result = score_assessment([{"skill": "Storage", "correct": False}])
        self.assertFalse(result.mastered)
        self.assertTrue(can_start_next_cycle(result, 1))

    def test_mastered_result_terminates_before_cycle_limit(self):
        result = score_assessment(
            [{"skill": "Storage", "correct": True}] * 17
            + [{"skill": "Storage", "correct": False}] * 3
        )
        self.assertTrue(result.mastered)
        self.assertFalse(can_start_next_cycle(result, 1))

    def test_maximum_cycle_behavior_stops_unmastered_result(self):
        result = score_assessment([{"skill": "Storage", "correct": False}])
        self.assertFalse(can_start_next_cycle(result, MAX_LEARNING_CYCLES))

    def test_cycle_limit_reads_environment_configuration(self):
        with patch.dict("os.environ", {"STUDYMATE_MAX_LEARNING_CYCLES": "7"}):
            self.assertEqual(get_max_learning_cycles(), 7)

    def test_incomplete_runtime_config_is_rejected_with_clear_error(self):
        with patch.object(agents, "PROVIDER_WEIGHTS", []):
            with self.assertRaisesRegex(ValueError, "GROQ_API_KEY|ROUTER_API_KEY"):
                agents.validate_runtime_config()

    def test_external_service_limits_are_bounded(self):
        self.assertGreater(agents.MODEL_TIMEOUT_SECONDS, 0)
        self.assertGreaterEqual(agents.MODEL_MAX_RETRIES, 1)
        self.assertGreater(search_tool.SEARCH_TIMEOUT_SECONDS, 0)

    def test_typed_workflow_models_store_required_learning_data(self):
        learner = LearnerProfile("Arjun Sharma", "Cloud Engineer", "AZ-204")
        certification = Certification(
            code="AZ-204",
            full_name="Developing Solutions for Microsoft Azure",
            skills=["API Development", "Azure Functions"],
        )
        result = AgentResult(WorkflowStage.PROFILER, "Learner profile collected")
        cycle = LearningCycle(1, taught_skills=["Azure Functions"])

        self.assertEqual(learner.certification, "AZ-204")
        self.assertEqual(certification.skills, ["API Development", "Azure Functions"])
        self.assertTrue(result.success)
        self.assertEqual(result.stage, WorkflowStage.PROFILER)
        self.assertEqual(cycle.number, 1)
        self.assertEqual(cycle.weak_skills, [])

    def test_workflow_defines_eight_agents_and_report_card(self):
        self.assertEqual(len(AGENT_STAGES), 8)
        self.assertEqual(
            AGENT_STAGES,
            (
                WorkflowStage.PROFILER,
                WorkflowStage.KNOWLEDGE,
                WorkflowStage.LEARNING_PATH,
                WorkflowStage.PLANNER,
                WorkflowStage.TEACHING,
                WorkflowStage.EXAMINER,
                WorkflowStage.MANAGER,
                WorkflowStage.CEO,
            ),
        )

    def test_workflow_allows_only_the_next_stage(self):
        state = WorkflowState()
        state.advance(WorkflowStage.KNOWLEDGE)
        self.assertEqual(state.current_stage, WorkflowStage.KNOWLEDGE)
        self.assertEqual(state.completed_stages, [WorkflowStage.KNOWLEDGE])

    def test_workflow_rejects_skipped_and_backward_transitions(self):
        state = WorkflowState()
        with self.assertRaisesRegex(ValueError, "Invalid transition"):
            state.advance(WorkflowStage.PLANNER)

        state.advance(WorkflowStage.KNOWLEDGE)
        with self.assertRaisesRegex(ValueError, "Invalid transition"):
            state.advance(WorkflowStage.PROFILER)

    def test_workflow_state_round_trips_and_advances_structurally(self):
        state = WorkflowState()
        state.complete_current_stage()
        restored = WorkflowState.from_dict(state.to_dict())

        self.assertEqual(restored.current_stage, WorkflowStage.KNOWLEDGE)
        self.assertEqual(restored.completed_stages, [WorkflowStage.PROFILER])

    def test_adaptive_cycle_advances_teaching_examiner_manager_and_ceo(self):
        state = WorkflowState(current_stage=WorkflowStage.TEACHING)

        for stage, expected_next in (
            (WorkflowStage.TEACHING, WorkflowStage.EXAMINER),
            (WorkflowStage.EXAMINER, WorkflowStage.MANAGER),
            (WorkflowStage.MANAGER, WorkflowStage.CEO),
            (WorkflowStage.CEO, WorkflowStage.REPORT_CARD),
        ):
            state.complete_adaptive_stage(stage)
            self.assertEqual(state.current_stage, expected_next)

        state.begin_adaptive_cycle()
        self.assertEqual(state.current_stage, WorkflowStage.TEACHING)

    def test_adaptive_cycle_rejects_non_cycle_stage(self):
        state = WorkflowState(current_stage=WorkflowStage.PLANNER)
        with self.assertRaisesRegex(ValueError, "can only start"):
            state.begin_adaptive_cycle()
        with self.assertRaisesRegex(ValueError, "not an adaptive cycle stage"):
            state.complete_adaptive_stage(WorkflowStage.PLANNER)

    def test_invalid_saved_workflow_state_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Invalid workflow state data"):
            WorkflowState.from_dict({"current_stage": "not-a-stage"})

    def test_each_agent_has_one_registered_responsibility(self):
        self.assertEqual(set(agents.AGENT_REGISTRY), set(agents.AGENT_RESPONSIBILITIES))
        self.assertEqual(len(agents.AGENT_REGISTRY), 8)
        self.assertEqual(
            len({agent.name for agent in agents.AGENT_REGISTRY.values()}),
            8,
        )
        self.assertTrue(all(agents.AGENT_RESPONSIBILITIES.values()))

    def test_certification_search_prioritizes_authoritative_domains(self):
        domains = agents.get_authoritative_source_domains("AZ-204")
        self.assertIn("learn.microsoft.com", domains)
        query = agents.add_authoritative_source_filter("AZ-204 official guide", "AZ-204")
        self.assertIn("site:learn.microsoft.com", query)
        self.assertNotIn("exam dumps", query.lower())

    def test_agents_retain_deduplicated_source_reference_shape(self):
        agent = agents.SimpleAgent(
            name="Source Test Agent",
            description="test",
            instructions="test",
            enable_tools=True,
        )
        agent.last_sources = [{
            "title": "Azure Functions documentation",
            "link": "https://learn.microsoft.com/azure/azure-functions/",
            "snippet": "Official documentation",
        }]
        sources = agent.get_last_sources()
        self.assertEqual(sources[0]["link"], "https://learn.microsoft.com/azure/azure-functions/")
        self.assertEqual(set(sources[0]), {"title", "link", "snippet"})

    def test_generated_questions_must_match_certification_skills(self):
        valid = [{
            "skill": "Azure Functions",
            "question": "For AZ-204, which Azure Functions option supports this workload?",
        }]
        invalid = [{
            "skill": "Unrelated Topic",
            "question": "Which answer should be selected?",
        }]
        self.assertEqual(
            validate_generated_questions(
                valid,
                "AZ-204",
                ["API Development", "Azure Functions"],
            ),
            [],
        )
        errors = validate_generated_questions(
            invalid,
            "AZ-204",
            ["API Development", "Azure Functions"],
        )
        self.assertEqual(len(errors), 2)

    def test_search_without_credentials_returns_no_fake_source(self):
        with patch.object(search_tool, "SERPAPI_KEY", None):
            self.assertEqual(search_tool.web_search("AZ-204 official guide"), [])

    def test_teaching_remediation_prompt_contains_only_weak_skills(self):
        prompt = build_remediation_prompt(["Azure Functions", "Storage"])
        self.assertIn("Azure Functions", prompt)
        self.assertIn("Storage", prompt)
        self.assertNotIn("ALL skills", prompt)
        self.assertIn("Do not teach unrelated", prompt)

    def test_empty_remediation_prompt_does_not_request_general_teaching(self):
        prompt = build_remediation_prompt([])
        self.assertIn("No weak skills identified", prompt)
        self.assertNotIn("teach all", prompt.lower())

    def test_report_card_is_generated_at_mastery_threshold(self):
        report = build_report_card(85, 2, [])
        self.assertEqual(report["status"], "MASTERED")
        self.assertEqual(report["mastery_threshold"], 85)
        self.assertEqual(report["cycles"], 2)

    def test_report_card_requires_no_weak_skills(self):
        report = build_report_card(90, 1, ["Storage"])
        self.assertEqual(report["status"], "NEEDS MORE PRACTICE")
        self.assertEqual(report["weak_skills"], ["Storage"])

    def test_orchestrator_dispatches_registered_agents_in_order(self):
        calls = []

        async def runner(agent, request):
            calls.append((agent, request))
            return f"done:{agent}"

        state = WorkflowState()
        orchestrator = AgentOrchestrator(
            state=state,
            agents={"profiler": "profiler-agent", "knowledge": "knowledge-agent"},
            runner=runner,
        )
        result = asyncio.run(
            orchestrator.run_stage(WorkflowStage.PROFILER, "profile prompt")
        )

        self.assertIsInstance(result, AgentResult)
        self.assertEqual(result.content, "done:profiler-agent")
        self.assertEqual(calls[0][0], "profiler-agent")
        self.assertIsInstance(calls[0][1], AgentRequest)
        self.assertEqual(calls[0][1].prompt, "profile prompt")
        self.assertEqual(calls[0][1].stage, WorkflowStage.PROFILER)
        self.assertEqual(state.current_stage, WorkflowStage.KNOWLEDGE)

    def test_orchestrator_rejects_invalid_agent_handoff_without_advancing(self):
        async def runner(agent, request):
            return AgentResult(WorkflowStage.KNOWLEDGE, "")

        state = WorkflowState()
        orchestrator = AgentOrchestrator(
            state=state,
            agents={"profiler": "profiler-agent"},
            runner=runner,
        )
        with self.assertRaisesRegex(AgentExecutionError, "Agent response stage mismatch"):
            asyncio.run(orchestrator.run_stage(WorkflowStage.PROFILER, "prompt"))
        self.assertEqual(state.current_stage, WorkflowStage.PROFILER)

    def test_orchestrator_rejects_non_string_and_empty_agent_output(self):
        async def invalid_type_runner(agent, request):
            return {"content": "not a valid handoff"}

        async def empty_runner(agent, request):
            return AgentResult(WorkflowStage.PROFILER, "   ")

        for runner, message in (
            (invalid_type_runner, "Invalid response type"),
            (empty_runner, "Agent handoff"),
        ):
            state = WorkflowState()
            orchestrator = AgentOrchestrator(
                state=state,
                agents={"profiler": "profiler-agent"},
                runner=runner,
            )
            with self.assertRaisesRegex(AgentExecutionError, message):
                asyncio.run(orchestrator.run_stage(WorkflowStage.PROFILER, "prompt"))
            self.assertEqual(state.current_stage, WorkflowStage.PROFILER)

    def test_orchestrator_reports_runner_failure_without_advancing(self):
        errors = []

        async def runner(agent, request):
            raise TimeoutError("provider timed out")

        state = WorkflowState()
        orchestrator = AgentOrchestrator(
            state=state,
            agents={"profiler": "profiler-agent"},
            runner=runner,
            on_error=lambda stage, message: errors.append((stage, message)),
        )
        with self.assertRaisesRegex(AgentExecutionError, "provider timed out"):
            asyncio.run(orchestrator.run_stage(WorkflowStage.PROFILER, "prompt"))

        self.assertEqual(state.current_stage, WorkflowStage.PROFILER)
        self.assertEqual(errors[0][0], WorkflowStage.PROFILER)

    def test_save_and_load_state_round_trip(self):
        import main
        import tasks

        tasks.set_learner_data("Test Learner", "Developer", "AZ-204")
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as handle:
            path = handle.name
        try:
            with patch.object(main, "SESSION_FILE", path):
                main.save_state({"workflow_state": {"current_stage": "profiler"}})
                restored = main.load_state()
            self.assertEqual(restored["learner"]["name"], "Test Learner")
            self.assertEqual(restored["memory"]["workflow_state"]["current_stage"], "profiler")
        finally:
            import os
            os.remove(path)

if __name__ == "__main__":
    unittest.main()
