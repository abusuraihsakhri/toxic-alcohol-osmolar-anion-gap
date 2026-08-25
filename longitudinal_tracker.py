#!/usr/bin/env python3
"""
Longitudinal Score Tracking for Toxic Alcohol Osmolar Anion Gap
Stores sequential assessments with date-stamped clinical parameters,
tracks score trajectory, and classifies trends (improving/stable/deteriorating).

Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict


@dataclass
class Assessment:
    """A single scored assessment with clinical parameters."""
    timestamp: str
    osmolal_gap: float
    anion_gap: float
    serum_osmolality: Optional[float] = None
    ethanol_level: Optional[float] = None
    clinical_notes: str = ""
    intervention: str = ""

    @property
    def combined_score(self) -> float:
        """Combined toxic alcohol severity score."""
        base = self.osmolal_gap + self.anion_gap * 0.5
        if self.serum_osmolality and self.serum_osmolality > 320:
            base += (self.serum_osmolality - 320) * 0.1
        return round(base, 2)


@dataclass
class TrendResult:
    """Result of trend analysis over a series of assessments."""
    trend: str  # "improving", "stable", "deteriorating"
    slope: float
    assessments_analyzed: int
    first_score: float
    last_score: float
    score_change: float
    days_span: float
    outcome_correlation: str


class LongitudinalTracker:
    """Tracks toxic alcohol osmolar anion gap scores over time."""

    TREND_IMPROVING = "improving"
    TREND_STABLE = "stable"
    TREND_DETERIORATING = "deteriorating"

    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self.assessments: List[Assessment] = []
        self.outcomes: List[Dict[str, Any]] = []

    def add_assessment(self, assessment: Assessment) -> None:
        """Add a new assessment to the longitudinal record."""
        self.assessments.append(assessment)
        self.assessments.sort(key=lambda a: a.timestamp)

    def add_outcome(self, timestamp: str, outcome_type: str, description: str) -> None:
        """Record a clinical outcome (mortality, readmission, complication)."""
        self.outcomes.append({
            "timestamp": timestamp,
            "type": outcome_type,
            "description": description,
        })

    def get_trajectory(self) -> List[Dict[str, Any]]:
        """Return the score trajectory as a list of timestamped scores."""
        return [
            {
                "timestamp": a.timestamp,
                "score": a.combined_score,
                "osmolal_gap": a.osmolal_gap,
                "anion_gap": a.anion_gap,
                "intervention": a.intervention,
            }
            for a in self.assessments
        ]

    def classify_trend(self, window_days: Optional[int] = None) -> TrendResult:
        """
        Classify the trend as improving, stable, or deteriorating.
        Uses linear regression on scores over time.
        """
        if len(self.assessments) < 2:
            return TrendResult(
                trend=self.TREND_STABLE,
                slope=0.0,
                assessments_analyzed=len(self.assessments),
                first_score=self.assessments[0].combined_score if self.assessments else 0.0,
                last_score=self.assessments[-1].combined_score if self.assessments else 0.0,
                score_change=0.0,
                days_span=0.0,
                outcome_correlation="insufficient_data",
            )

        assessments = self.assessments
        if window_days:
            cutoff = datetime.fromisoformat(assessments[-1].timestamp) - timedelta(days=window_days)
            assessments = [a for a in assessments if datetime.fromisoformat(a.timestamp) >= cutoff]

        if len(assessments) < 2:
            assessments = self.assessments[-2:]

        # Convert timestamps to numeric days from first assessment
        t0 = datetime.fromisoformat(assessments[0].timestamp)
        x = [(datetime.fromisoformat(a.timestamp) - t0).total_seconds() / 86400.0 for a in assessments]
        y = [a.combined_score for a in assessments]

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)

        denom = n * sum_x2 - sum_x ** 2
        if denom == 0:
            slope = 0.0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / denom

        score_change = y[-1] - y[0]
        days_span = x[-1] - x[0] if len(x) > 1 else 0.0

        # Classify trend: negative slope = improving (scores going down = better)
        if slope < -0.5:
            trend = self.TREND_IMPROVING
        elif slope > 0.5:
            trend = self.TREND_DETERIORATING
        else:
            trend = self.TREND_STABLE

        # Correlate with outcomes
        outcome_corr = self._correlate_with_outcomes(trend)

        return TrendResult(
            trend=trend,
            slope=round(slope, 4),
            assessments_analyzed=n,
            first_score=round(y[0], 2),
            last_score=round(y[-1], 2),
            score_change=round(score_change, 2),
            days_span=round(days_span, 1),
            outcome_correlation=outcome_corr,
        )

    def _correlate_with_outcomes(self, trend: str) -> str:
        """Correlate score trend with recorded clinical outcomes."""
        if not self.outcomes:
            return "no_outcomes_recorded"

        mortality = sum(1 for o in self.outcomes if o["type"] == "mortality")
        readmission = sum(1 for o in self.outcomes if o["type"] == "readmission")
        complication = sum(1 for o in self.outcomes if o["type"] == "complication")

        if trend == self.TREND_DETERIORATING and mortality > 0:
            return "deteriorating_with_mortality"
        elif trend == self.TREND_IMPROVING and mortality == 0:
            return "improving_no_mortality"
        elif complication > 0:
            return f"complications_present_{trend}"
        elif readmission > 0:
            return f"readmission_present_{trend}"
        else:
            return f"no_adverse_outcomes_{trend}"

    def get_summary(self) -> Dict[str, Any]:
        """Generate a comprehensive longitudinal summary."""
        trend = self.classify_trend()
        return {
            "patient_id": self.patient_id,
            "total_assessments": len(self.assessments),
            "total_outcomes": len(self.outcomes),
            "trend_analysis": asdict(trend),
            "latest_score": self.assessments[-1].combined_score if self.assessments else None,
            "peak_score": max(a.combined_score for a in self.assessments) if self.assessments else None,
            "trajectory": self.get_trajectory(),
        }


def create_tracker_from_json(data: Dict[str, Any]) -> LongitudinalTracker:
    """Factory: create a tracker from a JSON-serializable dict."""
    tracker = LongitudinalTracker(patient_id=data.get("patient_id", "unknown"))
    for a in data.get("assessments", []):
        tracker.add_assessment(Assessment(**a))
    for o in data.get("outcomes", []):
        tracker.add_outcome(o["timestamp"], o["type"], o["description"])
    return tracker
