"""
Tests du workflow - AI Orchestrator v6.1
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.workflow import (
    TaskSpec, AcceptanceCriteria, TaskPlan, PlanStep,
    VerificationReport, CheckResult,
    JudgeVerdict, WorkflowState, WorkflowPhase,
    WorkflowResponse
)


class TestAcceptanceCriteria:
    def test_create_with_checks(self):
        ac = AcceptanceCriteria(checks=["test passes", "lint clean"])
        assert len(ac.checks) == 2


class TestTaskSpec:
    def test_minimal_spec(self):
        spec = TaskSpec(
            objective="Create a file",
            acceptance=AcceptanceCriteria(checks=["file exists"])
        )
        assert spec.objective == "Create a file"
    
    def test_full_spec(self):
        spec = TaskSpec(
            objective="Refactor module",
            assumptions=["Code is Python"],
            acceptance=AcceptanceCriteria(checks=["tests pass"]),
            risks=["May break imports"],
            out_of_scope=["Frontend"]
        )
        assert len(spec.assumptions) == 1


class TestTaskPlan:
    def test_plan_with_steps(self):
        plan = TaskPlan(steps=[
            PlanStep(id="1", action="Read file", tools=["read_file"]),
            PlanStep(id="2", action="Modify", tools=["write_file"]),
        ])
        assert len(plan.steps) == 2
    
    def test_get_step_by_id(self):
        plan = TaskPlan(steps=[
            PlanStep(id="step1", action="First"),
        ])
        step = plan.get_step("step1")
        assert step.action == "First"


class TestVerificationReport:
    def test_passed_report(self):
        report = VerificationReport(
            passed=True,
            checks_run=["run_tests"],
            results=[CheckResult(name="run_tests", passed=True, output="OK")]
        )
        assert report.passed is True
    
    def test_failed_report(self):
        report = VerificationReport(
            passed=False,
            checks_run=["run_tests"],
            results=[CheckResult(name="run_tests", passed=False, error="Failed")],
            failures=["run_tests: Failed"]
        )
        assert report.passed is False


class TestJudgeVerdict:
    def test_pass_verdict(self):
        verdict = JudgeVerdict(status="PASS", confidence=0.95)
        assert verdict.status == "PASS"
    
    def test_fail_verdict(self):
        verdict = JudgeVerdict(
            status="FAIL",
            confidence=0.9,
            issues=["Test failed"],
            suggested_fixes=["Fix it"]
        )
        assert verdict.status == "FAIL"
        assert len(verdict.issues) == 1


class TestWorkflowState:
    def test_initial_state(self):
        state = WorkflowState(id="test", original_request="Create")
        assert state.phase == WorkflowPhase.SPEC
        assert state.repair_cycles == 0


class TestWorkflowPhase:
    def test_all_phases_exist(self):
        phases = [
            WorkflowPhase.SPEC, WorkflowPhase.PLAN,
            WorkflowPhase.EXECUTE, WorkflowPhase.VERIFY,
            WorkflowPhase.REPAIR, WorkflowPhase.COMPLETE,
            WorkflowPhase.FAILED,
        ]
        assert len(phases) == 7


class TestWorkflowResponse:
    def test_minimal_response(self):
        response = WorkflowResponse(
            response="Done",
            model_used="qwen2.5"
        )
        assert response.response == "Done"
    
    def test_full_response(self):
        response = WorkflowResponse(
            response="Created",
            model_used="qwen2.5",
            verification=VerificationReport(passed=True, checks_run=[], results=[]),
            verdict=JudgeVerdict(status="PASS"),
            workflow_phase=WorkflowPhase.COMPLETE,
        )
        assert response.verdict.status == "PASS"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
