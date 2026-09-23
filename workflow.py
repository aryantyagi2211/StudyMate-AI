"""Small, deterministic helpers for the StudyMate learning workflow."""

from dataclasses import dataclass, field
from enum import Enum
import os
from typing import Any, Awaitable, Callable

MASTERY_THRESHOLD = 85
MAX_LEARNING_CYCLES = 5
MAX_LEARNING_CYCLES_ENV = "STUDYMATE_MAX_LEARNING_CYCLES"


class WorkflowStage(str, Enum):
    PROFILER = "profiler"
    KNOWLEDGE = "knowledge"
    LEARNING_PATH = "learning_path"
    PLANNER = "planner"
    TEACHING = "teaching"
    EXAMINER = "examiner"
    MANAGER = "manager"
    CEO = "ceo"
    REPORT_CARD = "report_card"


AGENT_STAGES = (
    WorkflowStage.PROFILER,
    WorkflowStage.KNOWLEDGE,
    WorkflowStage.LEARNING_PATH,
    WorkflowStage.PLANNER,
    WorkflowStage.TEACHING,
    WorkflowStage.EXAMINER,
    WorkflowStage.MANAGER,
    WorkflowStage.CEO,
)

WORKFLOW_ORDER = [
    *AGENT_STAGES,
    WorkflowStage.REPORT_CARD,
]

VALID_TRANSITIONS = {
    current: next_stage
    for current, next_stage in zip(WORKFLOW_ORDER, WORKFLOW_ORDER[1:])
}


class AgentExecutionError(RuntimeError):
    """Raised when an agent cannot produce a valid handoff."""


@dataclass
class AgentRequest:
    stage: WorkflowStage
    prompt: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentOrchestrator:
    state: "WorkflowState"
    agents: dict[str, Any]
    runner: Callable[[Any, AgentRequest], Awaitable[Any]]
    on_error: Callable[[WorkflowStage, str], None] | None = None

    async def run_stage(
        self,
        stage: WorkflowStage,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> "AgentResult":
        if stage not in AGENT_STAGES:
            raise ValueError(f"Only agent stages can be dispatched: {stage.value}")
        if self.state.current_stage != stage:
            raise ValueError(
                f"Cannot dispatch {stage.value} while workflow is at "
                f"{self.state.current_stage.value}."
            )
        try:
            agent = self.agents[stage.value]
        except KeyError as exc:
            raise ValueError(f"No agent registered for stage: {stage.value}") from exc
        request = AgentRequest(stage=stage, prompt=prompt, context=context or {})
        try:
            response = await self.runner(agent, request)
        except Exception as exc:
            message = f"{stage.value} agent failed: {exc}"
            if self.on_error:
                self.on_error(stage, message)
            raise AgentExecutionError(message) from exc
        if isinstance(response, str):
            response = AgentResult(stage=stage, content=response)
        if not isinstance(response, AgentResult):
            message = f"Invalid response type from {stage.value} agent."
            if self.on_error:
                self.on_error(stage, message)
            raise AgentExecutionError(message)
        if response.stage != stage:
            message = (
                f"Agent response stage mismatch: expected {stage.value}, "
                f"received {response.stage.value}."
            )
            if self.on_error:
                self.on_error(stage, message)
            raise AgentExecutionError(message)
        if not response.success or not response.content.strip():
            message = f"Agent handoff from {stage.value} is invalid."
            if self.on_error:
                self.on_error(stage, message)
            raise AgentExecutionError(message)
        self.state.complete_current_stage()
        return response

    def complete_stage(self, stage: WorkflowStage) -> None:
        if self.state.current_stage != stage:
            raise ValueError(
                f"Cannot complete {stage.value} while workflow is at "
                f"{self.state.current_stage.value}."
            )
        self.state.complete_current_stage()


@dataclass
class MasteryResult:
    total: int
    correct: int
    percentage: int
    skill_scores: dict[str, dict[str, int]] = field(default_factory=dict)
    weak_skills: list[str] = field(default_factory=list)

    @property
    def mastered(self) -> bool:
        return self.percentage >= MASTERY_THRESHOLD and not self.weak_skills


@dataclass
class LearnerProfile:
    name: str
    role: str
    certification: str


@dataclass
class Certification:
    code: str
    full_name: str
    skills: list[str] = field(default_factory=list)
    recommended_hours: int | None = None
    passing_score: int | None = None
    exam_format: str | None = None
    difficulty: str | None = None


@dataclass
class AgentResult:
    stage: WorkflowStage
    content: str
    success: bool = True
    error: str | None = None


@dataclass
class LearningCycle:
    number: int
    taught_skills: list[str] = field(default_factory=list)
    score: MasteryResult | None = None
    weak_skills: list[str] = field(default_factory=list)


@dataclass
class WorkflowState:
    current_stage: WorkflowStage = WorkflowStage.PROFILER
    completed_stages: list[WorkflowStage] = field(default_factory=list)
    cycle_count: int = 0
    current_score: int = 0
    weak_skills: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_stage": self.current_stage.value,
            "completed_stages": [stage.value for stage in self.completed_stages],
            "cycle_count": self.cycle_count,
            "current_score": self.current_score,
            "weak_skills": list(self.weak_skills),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowState":
        try:
            current_stage = WorkflowStage(data["current_stage"])
            completed_stages = [
                WorkflowStage(stage) for stage in data.get("completed_stages", [])
            ]
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Invalid workflow state data") from exc
        return cls(
            current_stage=current_stage,
            completed_stages=completed_stages,
            cycle_count=int(data.get("cycle_count", 0)),
            current_score=int(data.get("current_score", 0)),
            weak_skills=[str(skill) for skill in data.get("weak_skills", [])],
        )

    def complete_current_stage(self) -> None:
        if self.current_stage not in WORKFLOW_ORDER:
            raise ValueError(f"Unknown workflow stage: {self.current_stage}")
        if self.current_stage not in self.completed_stages:
            self.completed_stages.append(self.current_stage)
        next_stage = WORKFLOW_ORDER.index(self.current_stage) + 1
        if next_stage < len(WORKFLOW_ORDER):
            self.current_stage = WORKFLOW_ORDER[next_stage]

    def begin_adaptive_cycle(self) -> None:
        """Position the workflow at Teaching for the next adaptive cycle."""
        if self.current_stage == WorkflowStage.TEACHING:
            return
        if self.current_stage == WorkflowStage.REPORT_CARD:
            self.current_stage = WorkflowStage.TEACHING
            return
        raise ValueError(
            "Adaptive cycles can only start from the teaching or report-card stage."
        )

    def complete_adaptive_stage(self, stage: WorkflowStage) -> None:
        """Complete one of the four stages that make up an adaptive cycle."""
        if stage not in (
            WorkflowStage.TEACHING,
            WorkflowStage.EXAMINER,
            WorkflowStage.MANAGER,
            WorkflowStage.CEO,
        ):
            raise ValueError(f"{stage.value} is not an adaptive cycle stage.")
        if self.current_stage != stage:
            raise ValueError(
                f"Cannot complete {stage.value} while workflow is at "
                f"{self.current_stage.value}."
            )
        self.complete_current_stage()

    def mark_stage_complete(self, stage: WorkflowStage) -> None:
        if stage not in WORKFLOW_ORDER:
            raise ValueError(f"Unknown workflow stage: {stage}")
        if stage not in self.completed_stages:
            self.completed_stages.append(stage)
        self.current_stage = stage

    def advance(self, next_stage: WorkflowStage) -> None:
        if next_stage not in WORKFLOW_ORDER:
            raise ValueError(f"Unknown workflow stage: {next_stage}")
        if VALID_TRANSITIONS.get(self.current_stage) != next_stage:
            raise ValueError(
                f"Invalid transition from {self.current_stage.value} to {next_stage.value}. "
                "Stages must progress in the defined workflow order."
            )
        self.mark_stage_complete(next_stage)

    def update_assessment(self, result: MasteryResult) -> None:
        self.current_score = result.percentage
        self.weak_skills = list(result.weak_skills)
        self.cycle_count = max(self.cycle_count, 1 if result.total else 0)


def score_assessment(results: list[dict[str, Any]]) -> MasteryResult:
    """Calculate overall and per-skill scores from validated answer results."""
    total = len(results)
    correct = sum(1 for result in results if result.get("correct") is True)
    skill_scores: dict[str, dict[str, int]] = {}

    for result in results:
        skill = str(result.get("skill") or "General").strip() or "General"
        scores = skill_scores.setdefault(skill, {"correct": 0, "total": 0})
        scores["total"] += 1
        if result.get("correct") is True:
            scores["correct"] += 1

    weak_skills = [
        skill for skill, scores in skill_scores.items()
        if scores["correct"] * 100 < MASTERY_THRESHOLD * scores["total"]
    ]
    percentage = int(correct * 100 / total) if total else 0
    return MasteryResult(
        total=total,
        correct=correct,
        percentage=percentage,
        skill_scores=skill_scores,
        weak_skills=weak_skills,
    )


def validate_generated_questions(
    questions: list[dict[str, Any]],
    certification: str,
    skills: list[str],
) -> list[str]:
    """Return content-validation errors for generated certification questions."""
    errors = []
    normalized_skills = [skill.strip().lower() for skill in skills if skill.strip()]
    cert = certification.strip().lower()

    for index, question in enumerate(questions, start=1):
        skill = str(question.get("skill") or "").strip().lower()
        question_text = str(question.get("question") or "").strip().lower()
        if not skill:
            errors.append(f"Q{index}: missing skill.")
            continue
        if normalized_skills and not any(
            configured in skill or skill in configured
            for configured in normalized_skills
        ):
            errors.append(
                f"Q{index}: skill '{question.get('skill')}' is not in the "
                f"{certification} skill list."
            )
        if cert and cert not in question_text and not any(
            token in question_text for token in skill.split()
        ):
            errors.append(
                f"Q{index}: question does not reference its declared skill "
                f"or certification {certification}."
            )
    return errors


def build_remediation_prompt(weak_skills: list[str]) -> str:
    """Build a teaching prompt focused only on identified weak skills."""
    skills = [str(skill).strip() for skill in weak_skills if str(skill).strip()]
    if not skills:
        return "No weak skills identified. Do not start a remediation topic."
    return (
        "Teach only these weak skills, in the listed order: "
        + ", ".join(dict.fromkeys(skills))
        + ". Do not teach unrelated certification skills."
    )


def build_report_card(
    score: int,
    cycles: int,
    weak_skills: list[str],
) -> dict[str, Any]:
    """Create a deterministic final report card for a completed learning loop."""
    mastered = score >= MASTERY_THRESHOLD and not weak_skills
    return {
        "score": score,
        "mastery_threshold": MASTERY_THRESHOLD,
        "cycles": cycles,
        "weak_skills": list(weak_skills),
        "status": "MASTERED" if mastered else "NEEDS MORE PRACTICE",
    }


def get_max_learning_cycles(configured_value: int | str | None = None) -> int:
    """Return a validated cycle limit from an explicit value or environment."""
    raw_value = configured_value
    if raw_value is None:
        raw_value = os.getenv(MAX_LEARNING_CYCLES_ENV, str(MAX_LEARNING_CYCLES))
    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{MAX_LEARNING_CYCLES_ENV} must be a positive integer."
        ) from exc
    if value < 1:
        raise ValueError(f"{MAX_LEARNING_CYCLES_ENV} must be a positive integer.")
    return value


def can_start_next_cycle(result: MasteryResult, cycle: int) -> bool:
    """Return whether another remediation cycle may run."""
    return not result.mastered and cycle < MAX_LEARNING_CYCLES
