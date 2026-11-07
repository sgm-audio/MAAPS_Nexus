"""
Telemetry and KPI aggregation utilities.

This module powers the GUI Finance/Upgrade dashboards by capturing
workflow execution statistics, billable-hour estimates, and feature
usage counters in-memory. The workflow engine records events here,
and the high-level system API exposes aggregated metrics.
"""

from __future__ import annotations

import statistics
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


def _resolve_manual_hours(step_payload: Dict[str, Any]) -> float:
    """Best-effort manual effort estimate from workflow step definitions."""
    if "estimated_manual_hours" in step_payload:
        return float(step_payload["estimated_manual_hours"])

    if "estimated_manual_minutes" in step_payload:
        return float(step_payload["estimated_manual_minutes"]) / 60.0

    # Conservative default (6 minutes) if nothing provided
    return 0.1


@dataclass
class WorkflowTelemetry:
    """Snapshot of a workflow for KPI calculations."""

    workflow_id: str
    name: str
    context: Dict[str, Any]
    estimated_manual_hours: float
    steps_total: int
    started_at: float = field(default_factory=time.time)
    duration_seconds: float = 0.0
    completed: bool = False
    success: bool = False
    automated_steps: int = 0
    manual_steps: int = 0
    failures: int = 0


class TelemetryStore:
    """Thread-safe metric aggregator."""

    def __init__(self):
        self._lock = threading.Lock()
        self._workflows: Dict[str, WorkflowTelemetry] = {}
        self._projects: Dict[str, Dict[str, Any]] = {}
        self._revision_durations: list[float] = []
        self._feature_usage: Dict[str, int] = {}
        self._manual_interventions = 0

    # ------------------------------------------------------------------
    # Recording helpers
    # ------------------------------------------------------------------

    def workflow_started(self, workflow: Any):
        """Track workflow metadata when execution begins."""
        manual_hours = sum(
            _resolve_manual_hours(step.payload) for step in workflow.steps
        )
        record = WorkflowTelemetry(
            workflow_id=workflow.workflow_id,
            name=workflow.name,
            context=dict(workflow.context or {}),
            estimated_manual_hours=manual_hours,
            steps_total=len(workflow.steps),
            started_at=workflow.started_at or time.time(),
        )

        with self._lock:
            self._workflows[workflow.workflow_id] = record

    def workflow_completed(self, workflow: Any):
        """Mark completion/failure and update project + revision stats."""
        with self._lock:
            record = self._workflows.get(workflow.workflow_id)
            if not record:
                return

            record.completed = True
            record.success = workflow.status.name == "COMPLETED"
            if workflow.started_at and workflow.completed_at:
                record.duration_seconds = workflow.completed_at - workflow.started_at

            project_id = record.context.get("project_id") or workflow.workflow_id
            project = self._projects.setdefault(
                project_id,
                {
                    "workflows": [],
                    "client_fee": 0.0,
                    "last_completed_at": 0.0,
                },
            )
            project["workflows"].append(workflow.workflow_id)
            project["client_fee"] = max(
                project["client_fee"], float(record.context.get("client_fee", 0.0))
            )
            project["last_completed_at"] = workflow.completed_at or time.time()

            requested_at = record.context.get("revision_requested_at")
            if requested_at:
                delivered_at = workflow.completed_at or time.time()
                duration = max(delivered_at - requested_at, 0.0)
                self._revision_durations.append(duration)

    def record_step_execution(self, workflow_id: str, step: Any):
        """Update step-level counters for automation metrics."""
        with self._lock:
            record = self._workflows.get(workflow_id)
            if not record:
                return

            is_manual = step.payload.get("execution_mode") == "manual"
            if is_manual:
                record.manual_steps += 1
            else:
                record.automated_steps += 1

            if step.status.name == "FAILED":
                record.failures += 1
                self._manual_interventions += 1

    def record_feature_usage(self, feature_name: str):
        """Increment usage counters for Upgrade page messaging."""
        with self._lock:
            self._feature_usage[feature_name] = (
                self._feature_usage.get(feature_name, 0) + 1
            )

    # ------------------------------------------------------------------
    # KPI accessors
    # ------------------------------------------------------------------

    def get_finance_metrics(self, hourly_rate: float = 75.0) -> Dict[str, Any]:
        with self._lock:
            records = [rec for rec in self._workflows.values() if rec.completed]
            total_steps = sum(rec.steps_total for rec in records) or 1
            automated_steps = sum(rec.automated_steps for rec in records)
            manual_steps = sum(rec.manual_steps for rec in records)

            hours_saved = 0.0
            for rec in records:
                actual_hours = rec.duration_seconds / 3600.0
                hours_saved += max(rec.estimated_manual_hours - actual_hours, 0.0)

            revision_median = (
                statistics.median(self._revision_durations)
                if self._revision_durations
                else None
            )

            projects_delivered = len(self._projects)
            revenue = sum(p["client_fee"] for p in self._projects.values())

            return {
                "billable_hours_saved": hours_saved,
                "dollar_savings": hours_saved * hourly_rate,
                "projects_delivered": projects_delivered,
                "automation_rate": automated_steps / total_steps,
                "manual_intervention_ratio": (
                    self._manual_interventions / total_steps if total_steps else 0.0
                ),
                "revision_turnaround_seconds": revision_median,
                "estimated_revenue": revenue + hours_saved * hourly_rate,
                "total_steps_tracked": total_steps,
                "automated_steps": automated_steps,
                "manual_steps": manual_steps,
            }

    def get_upgrade_metrics(
        self,
        account_context: Optional[Dict[str, Any]] = None,
        finance_snapshot: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        account_context = account_context or {}
        finance_snapshot = finance_snapshot or self.get_finance_metrics(
            account_context.get("hourly_rate", 75.0)
        )

        feature_limits = account_context.get(
            "feature_limits",
            {
                "workflow_templates": 10,
                "emergent_intelligence": 25,
                "temporal_context": 15,
                "collaborations": 3,
            },
        )

        with self._lock:
            utilization = {}
            for feature, limit in feature_limits.items():
                usage = self._feature_usage.get(feature, 0)
                pct = min(usage / limit, 1.0) if limit else 0.0
                utilization[feature] = {
                    "used": usage,
                    "limit": limit,
                    "utilization": pct,
                }

            workflow_records = [
                rec for rec in self._workflows.values() if rec.completed
            ]
            success_count = sum(1 for rec in workflow_records if rec.success)
            total = len(workflow_records) or 1
            quality_score = success_count / total

            dollar_savings_per_day = finance_snapshot["dollar_savings"] / max(total, 1)
            upgrade_cost = account_context.get("upgrade_cost", 0.0)

            return {
                "feature_utilization": utilization,
                "quality_score": quality_score,
                "support_load_reduction": 1.0
                - finance_snapshot["manual_intervention_ratio"],
                "collaboration_capacity": {
                    "current": account_context.get("current_collaborators", 1),
                    "limit": account_context.get("collaborator_limit", 3),
                },
                "roi_projection_days": (
                    upgrade_cost / dollar_savings_per_day
                    if dollar_savings_per_day
                    else None
                ),
                "dollar_savings_per_day": dollar_savings_per_day,
            }


_TELEMETRY_STORE = TelemetryStore()


def get_telemetry_store() -> TelemetryStore:
    """Global accessor used by the workflow engine and system API."""
    return _TELEMETRY_STORE
