"""
Comprehensive tests for core algorithms, validation, and security features.
"""
import sys
import math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from toxic_alcohols import (
    calculate_metrics,
    calculate_osmolal_gap,
    calculate_anion_gap,
    process_batch,
    ValidationError,
)
from alert_escalation import AlertEscalationEngine
from longitudinal_tracker import LongitudinalTracker, Assessment
from patient_stratification import PatientStratifier


# =============================================================================
# Input Validation Tests
# =============================================================================

class TestInputValidation:
    """Test input validation for core algorithms."""

    def test_calculate_metrics_rejects_nan(self):
        with pytest.raises(ValidationError, match="finite number"):
            calculate_metrics(v1=float("nan"), v2=4.0)

    def test_calculate_metrics_rejects_inf(self):
        with pytest.raises(ValidationError, match="finite number"):
            calculate_metrics(v1=float("inf"), v2=4.0)

    def test_calculate_metrics_rejects_negative(self):
        with pytest.raises(ValidationError, match="non-negative"):
            calculate_metrics(v1=-5.0, v2=4.0)

    def test_calculate_osmolal_gap_rejects_nan(self):
        with pytest.raises(ValidationError):
            calculate_osmolal_gap(float("nan"), 140, 100, 15)

    def test_calculate_osmolal_gap_rejects_negative(self):
        with pytest.raises(ValidationError):
            calculate_osmolal_gap(300, -140, 100, 15)

    def test_calculate_anion_gap_rejects_nan(self):
        with pytest.raises(ValidationError):
            calculate_anion_gap(140, float("nan"), 24)

    def test_calculate_anion_gap_rejects_negative(self):
        with pytest.raises(ValidationError):
            calculate_anion_gap(140, -100, 24)


# =============================================================================
# Osmolal Gap Calculation Tests
# =============================================================================

class TestOsmolalGap:
    """Test osmolal gap calculation."""

    def test_normal_osmolal_gap(self):
        # Normal: measured 290, Na 140, glucose 100, BUN 15
        # Calculated = 2*140 + 100/18 + 15/2.8 = 280 + 5.56 + 5.36 = 290.92
        # Gap = 290 - 290.92 = -0.92
        result = calculate_osmolal_gap(290, 140, 100, 15)
        assert isinstance(result, float)
        assert abs(result - (-0.92)) < 0.1

    def test_elevated_osmolal_gap(self):
        # Elevated: measured 320, Na 140, glucose 100, BUN 15
        # Gap = 320 - 290.92 = 29.08
        result = calculate_osmolal_gap(320, 140, 100, 15)
        assert result > 25.0

    def test_zero_inputs(self):
        result = calculate_osmolal_gap(0, 0, 0, 0)
        assert result == 0.0


# =============================================================================
# Anion Gap Calculation Tests
# =============================================================================

class TestAnionGap:
    """Test anion gap calculation."""

    def test_normal_anion_gap(self):
        # Normal: Na 140, Cl 104, HCO3 24
        # Gap = 140 - (104 + 24) = 12
        result = calculate_anion_gap(140, 104, 24)
        assert result == 12.0

    def test_elevated_anion_gap(self):
        # Elevated: Na 140, Cl 90, HCO3 18
        # Gap = 140 - (90 + 18) = 32
        result = calculate_anion_gap(140, 90, 18)
        assert result == 32.0

    def test_zero_inputs(self):
        result = calculate_anion_gap(0, 0, 0)
        assert result == 0.0


# =============================================================================
# Risk Classification Tests
# =============================================================================

class TestRiskClassification:
    """Test risk tier classification."""

    def test_low_risk(self):
        res = calculate_metrics(v1=5.0, v2=2.0)
        assert res["classification"] == "Low / Standard"

    def test_moderate_risk(self):
        res = calculate_metrics(v1=15.0, v2=5.0)
        assert res["classification"] == "Moderate / Intermediate"

    def test_high_risk(self):
        res = calculate_metrics(v1=30.0, v2=10.0)
        assert res["classification"] == "High / Severe"

    def test_score_is_positive(self):
        res = calculate_metrics(v1=10.0, v2=5.0)
        assert res["score"] > 0

    def test_score_is_rounded(self):
        res = calculate_metrics(v1=10.123456, v2=5.789012)
        # Score should be rounded to 2 decimal places
        assert res["score"] == round(res["score"], 2)


# =============================================================================
# Batch Processing Tests
# =============================================================================

class TestBatchProcessing:
    """Test batch CSV processing."""

    def test_batch_creates_output(self, tmp_path):
        csv_in = tmp_path / "in.csv"
        csv_out = tmp_path / "out.csv"
        csv_in.write_text("Patient_ID,v1,v2\nPT-001,10.0,5.0\n", encoding="utf-8")
        process_batch(str(csv_in), str(csv_out))
        assert csv_out.exists()

    def test_batch_missing_input_raises(self, tmp_path):
        csv_out = tmp_path / "out.csv"
        with pytest.raises(FileNotFoundError):
            process_batch("nonexistent.csv", str(csv_out))

    def test_batch_invalid_output_dir_raises(self, tmp_path):
        csv_in = tmp_path / "in.csv"
        csv_in.write_text("Patient_ID,v1\nPT-001,10.0\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Output directory"):
            process_batch(str(csv_in), "/nonexistent/dir/out.csv")


# =============================================================================
# Alert Escalation Tests
# =============================================================================

class TestAlertEscalation:
    """Test alert escalation engine."""

    def test_emergent_osmolal_gap(self):
        engine = AlertEscalationEngine()
        alerts = engine.evaluate_score(osmolal_gap=55.0, anion_gap=10.0, combined_score=20.0)
        assert any(a.severity == "emergent" for a in alerts)

    def test_critical_osmolal_gap(self):
        engine = AlertEscalationEngine()
        alerts = engine.evaluate_score(osmolal_gap=30.0, anion_gap=10.0, combined_score=20.0)
        assert any(a.severity == "critical" for a in alerts)

    def test_warning_osmolal_gap(self):
        engine = AlertEscalationEngine()
        alerts = engine.evaluate_score(osmolal_gap=15.0, anion_gap=10.0, combined_score=12.0)
        assert any(a.severity == "warning" for a in alerts)

    def test_critical_anion_gap(self):
        engine = AlertEscalationEngine()
        alerts = engine.evaluate_score(osmolal_gap=5.0, anion_gap=25.0, combined_score=10.0)
        assert any(a.severity == "critical" and "anion" in a.message.lower() for a in alerts)

    def test_rapid_change_detection(self):
        engine = AlertEscalationEngine()
        alert = engine.evaluate_rapid_change(10.0, 25.0, 2.0)
        assert alert is not None
        assert alert.category == "rapid_change"

    def test_no_rapid_change_for_small_change(self):
        engine = AlertEscalationEngine()
        alert = engine.evaluate_rapid_change(10.0, 11.0, 2.0)
        assert alert is None

    def test_overdue_assessment(self):
        engine = AlertEscalationEngine()
        alert = engine.check_overdue_assessment(10.0, True)
        assert alert is not None
        assert alert.category == "overdue"

    def test_acknowledge_alert(self):
        engine = AlertEscalationEngine()
        engine.evaluate_score(osmolal_gap=55.0, anion_gap=10.0, combined_score=20.0)
        alert_id = engine.alerts[0].alert_id
        assert engine.acknowledge_alert(alert_id) is True
        assert engine.alerts[0].acknowledged is True

    def test_get_active_alerts(self):
        engine = AlertEscalationEngine()
        engine.evaluate_score(osmolal_gap=55.0, anion_gap=10.0, combined_score=20.0)
        active = engine.get_active_alerts()
        assert len(active) > 0


# =============================================================================
# Longitudinal Tracker Tests
# =============================================================================

class TestLongitudinalTracker:
    """Test longitudinal tracking."""

    def test_add_assessment(self):
        tracker = LongitudinalTracker("PT-001")
        tracker.add_assessment(Assessment(
            timestamp="2026-01-01T00:00:00",
            osmolal_gap=15.0,
            anion_gap=12.0,
        ))
        assert len(tracker.assessments) == 1

    def test_combined_score(self):
        a = Assessment(
            timestamp="2026-01-01T00:00:00",
            osmolal_gap=20.0,
            anion_gap=10.0,
        )
        # combined = 20 + 10*0.5 = 25
        assert a.combined_score == 25.0

    def test_combined_score_with_high_osmolality(self):
        a = Assessment(
            timestamp="2026-01-01T00:00:00",
            osmolal_gap=20.0,
            anion_gap=10.0,
            serum_osmolality=340.0,
        )
        # combined = 20 + 10*0.5 + (340-320)*0.1 = 25 + 2 = 27
        assert a.combined_score == 27.0

    def test_trend_deteriorating(self):
        tracker = LongitudinalTracker("PT-001")
        tracker.add_assessment(Assessment(timestamp="2026-01-01T00:00:00", osmolal_gap=10.0, anion_gap=8.0))
        tracker.add_assessment(Assessment(timestamp="2026-01-02T00:00:00", osmolal_gap=20.0, anion_gap=15.0))
        tracker.add_assessment(Assessment(timestamp="2026-01-03T00:00:00", osmolal_gap=35.0, anion_gap=25.0))
        result = tracker.classify_trend()
        assert result.trend == "deteriorating"

    def test_trend_improving(self):
        tracker = LongitudinalTracker("PT-001")
        tracker.add_assessment(Assessment(timestamp="2026-01-01T00:00:00", osmolal_gap=35.0, anion_gap=25.0))
        tracker.add_assessment(Assessment(timestamp="2026-01-02T00:00:00", osmolal_gap=20.0, anion_gap=15.0))
        tracker.add_assessment(Assessment(timestamp="2026-01-03T00:00:00", osmolal_gap=10.0, anion_gap=8.0))
        result = tracker.classify_trend()
        assert result.trend == "improving"

    def test_trend_stable(self):
        tracker = LongitudinalTracker("PT-001")
        # Use values that produce a slope within the stable range (|slope| <= 0.5)
        tracker.add_assessment(Assessment(timestamp="2026-01-01T00:00:00", osmolal_gap=15.0, anion_gap=10.0))
        tracker.add_assessment(Assessment(timestamp="2026-01-02T00:00:00", osmolal_gap=15.1, anion_gap=10.0))
        result = tracker.classify_trend()
        assert result.trend == "stable"

    def test_insufficient_data(self):
        tracker = LongitudinalTracker("PT-001")
        result = tracker.classify_trend()
        assert result.trend == "stable"
        assert result.assessments_analyzed == 0


# =============================================================================
# Patient Stratification Tests
# =============================================================================

class TestPatientStratification:
    """Test patient stratification."""

    def test_minimal_risk(self):
        stratifier = PatientStratifier()
        result = stratifier.stratify(osmolal_gap=5.0, anion_gap=8.0)
        assert result["risk_tier"]["tier_id"] == "tier_0"

    def test_moderate_risk(self):
        stratifier = PatientStratifier()
        result = stratifier.stratify(osmolal_gap=25.0, anion_gap=15.0)
        assert result["risk_tier"]["tier_id"] == "tier_2"

    def test_emergent_risk(self):
        stratifier = PatientStratifier()
        result = stratifier.stratify(osmolal_gap=50.0, anion_gap=30.0)
        assert result["risk_tier"]["tier_id"] == "tier_3"

    def test_clinical_modifiers_increase_risk(self):
        stratifier = PatientStratifier()
        result = stratifier.stratify(
            osmolal_gap=15.0, anion_gap=10.0,
            additional_factors={"age": 70, "ckd": True}
        )
        # Modifiers should increase risk
        assert len(result["clinical_modifiers"]) >= 2

    def test_trial_candidate_identification(self):
        stratifier = PatientStratifier()
        patients = [
            {"patient_id": "PT-001", "osmolal_gap": 5.0, "anion_gap": 5.0},
            {"patient_id": "PT-002", "osmolal_gap": 25.0, "anion_gap": 15.0},
            {"patient_id": "PT-003", "osmolal_gap": 50.0, "anion_gap": 30.0},
        ]
        candidates = stratifier.identify_trial_candidates(patients)
        assert len(candidates) >= 2  # PT-002 and PT-003 should be eligible
