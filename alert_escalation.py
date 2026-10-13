#!/usr/bin/env python3
"""
Alert Escalation for Toxic Alcohol Osmolar Anion Gap
Illustrative threshold alerts for laboratory gaps (not validated for diagnosis),
escalates rapid score changes, and routes to specialist workflows.

Author: Dr. Abu Suraih Sakhri
License: MIT
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class Alert:
    """A clinical alert triggered by score thresholds."""
    alert_id: str
    timestamp: str
    severity: str  # "info", "warning", "critical", "emergent"
    category: str  # "threshold", "rapid_change", "overdue", "specialist"
    message: str
    score_value: float
    threshold: float
    recommended_action: str
    escalation_target: str
    acknowledged: bool = False


class AlertEscalationEngine:
    """Illustrative gap-based alerts; not a treatment decision engine."""

    # Critical thresholds for toxic alcohol osmolar gap
    THRESHOLDS = {
        "osmolal_gap_warning": 10.0,
        "osmolal_gap_critical": 25.0,
        "osmolal_gap_emergent": 50.0,
        "anion_gap_warning": 12.0,
        "anion_gap_critical": 20.0,
        "combined_score_warning": 15.0,
        "combined_score_critical": 30.0,
        "combined_score_emergent": 50.0,
        "rapid_change_pct": 30.0,  # % change within 6 hours
    }

    ESCALATION_PATHS = {
        "info": "primary_team",
        "warning": "primary_team",
        "critical": "toxicology_consult",
        "emergent": "emergency_department",
    }

    def __init__(self):
        self.alerts: List[Alert] = []
        self._alert_counter = 0

    def _next_alert_id(self) -> str:
        self._alert_counter += 1
        return f"ALERT-{self._alert_counter:06d}"

    def evaluate_score(
        self,
        osmolal_gap: float,
        anion_gap: float,
        combined_score: float,
        timestamp: Optional[str] = None,
    ) -> List[Alert]:
        """Evaluate a new score against thresholds and generate alerts."""
        ts = timestamp or datetime.now().isoformat()
        new_alerts = []

        # Check osmolal gap thresholds
        if osmolal_gap >= self.THRESHOLDS["osmolal_gap_emergent"]:
            new_alerts.append(self._create_alert(
                ts, "emergent", "threshold",
                f"Emergent osmolal gap ({osmolal_gap:.1f} mOsm/kg) — immediate toxicology evaluation required",
                osmolal_gap, self.THRESHOLDS["osmolal_gap_emergent"],
                "Urgent toxicology assessment; obtain confirmatory levels as clinically indicated.",
                self.ESCALATION_PATHS["emergent"],
            ))
        elif osmolal_gap >= self.THRESHOLDS["osmolal_gap_critical"]:
            new_alerts.append(self._create_alert(
                ts, "critical", "threshold",
                f"Markedly elevated osmolal gap ({osmolal_gap:.1f} mOsm/kg) — nonspecific finding",
                osmolal_gap, self.THRESHOLDS["osmolal_gap_critical"],
                "Urgent clinical assessment, evaluate alternative causes, and consider specific toxic alcohol tests.",
                self.ESCALATION_PATHS["critical"],
            ))
        elif osmolal_gap >= self.THRESHOLDS["osmolal_gap_warning"]:
            new_alerts.append(self._create_alert(
                ts, "warning", "threshold",
                f"Elevated osmolal gap ({osmolal_gap:.1f} mOsm/kg) — monitor closely",
                osmolal_gap, self.THRESHOLDS["osmolal_gap_warning"],
                "Review history, ethanol level, acid-base status, and need for repeat testing.",
                self.ESCALATION_PATHS["warning"],
            ))

        # Check anion gap thresholds
        if anion_gap >= self.THRESHOLDS["anion_gap_critical"]:
            new_alerts.append(self._create_alert(
                ts, "critical", "threshold",
                f"Markedly elevated anion gap ({anion_gap:.1f} mEq/L) — evaluate acid-base status",
                anion_gap, self.THRESHOLDS["anion_gap_critical"],
                "Urgent clinical evaluation for metabolic acidosis and its differential diagnosis.",
                self.ESCALATION_PATHS["critical"],
            ))
        elif anion_gap >= self.THRESHOLDS["anion_gap_warning"]:
            new_alerts.append(self._create_alert(
                ts, "warning", "threshold",
                f"Elevated anion gap ({anion_gap:.1f} mEq/L)",
                anion_gap, self.THRESHOLDS["anion_gap_warning"],
                "Review lactate, ketones, renal function, and laboratory context.",
                self.ESCALATION_PATHS["warning"],
            ))

        # Check combined score
        if combined_score >= self.THRESHOLDS["combined_score_emergent"]:
            new_alerts.append(self._create_alert(
                ts, "emergent", "threshold",
                f"Emergent combined toxic alcohol score ({combined_score:.1f})",
                combined_score, self.THRESHOLDS["combined_score_emergent"],
                "Do not use this unvalidated composite to initiate treatment; seek specialist assessment.",
                self.ESCALATION_PATHS["emergent"],
            ))
        elif combined_score >= self.THRESHOLDS["combined_score_critical"]:
            new_alerts.append(self._create_alert(
                ts, "critical", "threshold",
                f"Critical combined toxic alcohol score ({combined_score:.1f})",
                combined_score, self.THRESHOLDS["combined_score_critical"],
                "Do not use this unvalidated composite to guide care; assess clinically.",
                self.ESCALATION_PATHS["critical"],
            ))

        self.alerts.extend(new_alerts)
        return new_alerts

    def evaluate_rapid_change(
        self,
        previous_score: float,
        current_score: float,
        hours_elapsed: float,
        timestamp: Optional[str] = None,
    ) -> Optional[Alert]:
        """Detect rapid score changes indicating acute deterioration."""
        ts = timestamp or datetime.now().isoformat()
        if previous_score == 0:
            return None

        pct_change = abs(current_score - previous_score) / previous_score * 100
        rate = pct_change / max(hours_elapsed, 0.1)

        if pct_change >= self.THRESHOLDS["rapid_change_pct"] and hours_elapsed <= 12:
            direction = "deterioration" if current_score > previous_score else "improvement"
            severity = "critical" if current_score > previous_score and pct_change >= 50 else "warning"
            alert = self._create_alert(
                ts, severity, "rapid_change",
                f"Rapid {direction}: {pct_change:.1f}% score change in {hours_elapsed:.1f} hours",
                current_score, self.THRESHOLDS["rapid_change_pct"],
                f"Score changed from {previous_score:.1f} to {current_score:.1f}. "
                f"{'Urgent reassessment needed.' if severity == 'critical' else 'Monitor closely.'}",
                self.ESCALATION_PATHS[severity],
            )
            self.alerts.append(alert)
            return alert
        return None

    def check_overdue_assessment(
        self,
        last_assessment_hours_ago: float,
        has_active_condition: bool,
        timestamp: Optional[str] = None,
    ) -> Optional[Alert]:
        """Alert when scoring assessment is overdue for patients with active conditions."""
        ts = timestamp or datetime.now().isoformat()
        overdue_threshold = 6.0  # hours

        if has_active_condition and last_assessment_hours_ago > overdue_threshold:
            alert = self._create_alert(
                ts, "warning", "overdue",
                f"Assessment overdue: {last_assessment_hours_ago:.1f}h since last scoring (threshold: {overdue_threshold}h)",
                0.0, overdue_threshold,
                "Obtain repeat toxic alcohol panel and osmolal gap calculation.",
                self.ESCALATION_PATHS["warning"],
            )
            self.alerts.append(alert)
            return alert
        return None

    def _create_alert(
        self, timestamp: str, severity: str, category: str,
        message: str, score_value: float, threshold: float,
        recommended_action: str, escalation_target: str,
    ) -> Alert:
        return Alert(
            alert_id=self._next_alert_id(),
            timestamp=timestamp,
            severity=severity,
            category=category,
            message=message,
            score_value=score_value,
            threshold=threshold,
            recommended_action=recommended_action,
            escalation_target=escalation_target,
        )

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert by ID."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def get_active_alerts(self, min_severity: str = "warning") -> List[Alert]:
        """Get unacknowledged alerts at or above the specified severity."""
        severity_order = {"info": 0, "warning": 1, "critical": 2, "emergent": 3}
        min_level = severity_order.get(min_severity, 1)
        return [
            a for a in self.alerts
            if not a.acknowledged and severity_order.get(a.severity, 0) >= min_level
        ]

    def get_alert_summary(self) -> Dict[str, Any]:
        """Summarize all alerts."""
        active = [a for a in self.alerts if not a.acknowledged]
        return {
            "total_alerts": len(self.alerts),
            "active_alerts": len(active),
            "by_severity": {
                sev: sum(1 for a in active if a.severity == sev)
                for sev in ["info", "warning", "critical", "emergent"]
            },
            "alerts": [asdict(a) for a in self.alerts],
        }
