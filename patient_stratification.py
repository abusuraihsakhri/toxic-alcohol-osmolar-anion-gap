#!/usr/bin/env python3
"""
Patient Stratification for Toxic Alcohol Osmolar Anion Gap
Exploratory scoring module. Tiers are not validated diagnostic or treatment criteria.

Author: Dr. Abu Suraih Sakhri
License: MIT
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class RiskTier:
    """Defines a risk tier with clinical pathway."""
    tier_id: str
    name: str
    score_range: tuple  # (min, max)
    description: str
    monitoring_frequency: str
    interventions: List[str]
    specialist_referral: bool
    clinical_pathway: str
    trial_eligibility: Optional[str] = None


# Stratification tiers for toxic alcohol osmolar anion gap
RISK_TIERS = [
    RiskTier(
        tier_id="tier_0",
        name="Minimal Risk",
        score_range=(0, 10),
        description="Normal or near-normal osmolal and anion gap. Gaps alone cannot exclude toxic alcohol ingestion.",
        monitoring_frequency="Determine clinically",
        interventions=["Review clinical history and relevant testing"],
        specialist_referral=False,
        clinical_pathway="standard_observation",
        trial_eligibility="not_eligible",
    ),
    RiskTier(
        tier_id="tier_1",
        name="Low-Moderate Risk",
        score_range=(10, 20),
        description="Mildly elevated gaps. Possible early ingestion or alternative etiology.",
        monitoring_frequency="Determine clinically",
        interventions=[
            "Consider serial laboratory assessment if clinically indicated",
            "Arterial blood gas",
            "Serum ethanol level",
            "Specific toxic alcohol assays when indicated",
        ],
        specialist_referral=False,
        clinical_pathway="enhanced_observation",
        trial_eligibility="screening_eligible",
    ),
    RiskTier(
        tier_id="tier_2",
        name="Moderate-High Risk",
        score_range=(20, 35),
        description="Elevated composite score; not a validated probability of poisoning.",
        monitoring_frequency="Determine clinically",
        interventions=[
            "Stat toxic alcohol levels (methanol, ethylene glycol, isopropanol)",
            "Discuss antidotal therapy with a toxicologist based on full clinical context",
            "Nephrology consultation for hemodialysis evaluation",
            "Assess acid-base status with appropriate specialist oversight",
            "Refer to current toxicology guidance for adjuncts",
        ],
        specialist_referral=True,
        clinical_pathway="toxicology_consult",
        trial_eligibility="treatment_eligible",
    ),
    RiskTier(
        tier_id="tier_3",
        name="High Risk / Emergent",
        score_range=(35, 100),
        description="High illustrative composite score; poisoning is neither confirmed nor excluded.",
        monitoring_frequency="Determine clinically",
        interventions=[
            "Urgent expert toxicology assessment",
            "Refer to current poison-specific extracorporeal treatment guidance",
            "Assess level of care based on clinical findings",
            "Supportive management based on clinical indications",
            "Ophthalmology consult (methanol) / Nephrology (ethylene glycol)",
            "Seek specialist guidance on antidotal options",
        ],
        specialist_referral=True,
        clinical_pathway="emergent_toxicology",
        trial_eligibility="urgent_treatment",
    ),
]


class PatientStratifier:
    """Reports legacy illustrative tiers; never substitute for clinical assessment."""

    def __init__(self, tiers: Optional[List[RiskTier]] = None):
        self.tiers = tiers or RISK_TIERS

    def stratify(
        self,
        osmolal_gap: float,
        anion_gap: float,
        additional_factors: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Stratify a patient into a risk tier based on scores and clinical factors.
        """
        # Compute combined score (same as toxic_alcohols.py)
        combined_score = osmolal_gap + anion_gap * 0.5
        if additional_factors and additional_factors.get("serum_osmolality"):
            so = additional_factors["serum_osmolality"]
            if so > 320:
                combined_score += (so - 320) * 0.1

        combined_score = round(combined_score, 2)

        # Find matching tier
        matched_tier = self.tiers[0]
        for tier in self.tiers:
            if tier.score_range[0] <= combined_score < tier.score_range[1]:
                matched_tier = tier
                break
        else:
            # Score exceeds all tier ranges
            if combined_score >= self.tiers[-1].score_range[0]:
                matched_tier = self.tiers[-1]

        # Apply modifier for additional clinical factors
        modifiers = self._apply_clinical_modifiers(additional_factors or {})

        return {
            "combined_score": combined_score,
            "osmolal_gap": osmolal_gap,
            "anion_gap": anion_gap,
            "risk_tier": asdict(matched_tier),
            "clinical_modifiers": modifiers,
            "adjusted_risk": self._adjust_risk(matched_tier, modifiers),
            "protocol_recommendation": self._generate_protocol(matched_tier, modifiers),
            "disclaimer": "Unvalidated illustrative categories, not treatment or trial eligibility criteria.",
        }

    def _apply_clinical_modifiers(self, factors: Dict[str, Any]) -> List[Dict[str, str]]:
        """Apply clinical modifiers that may shift risk up or down."""
        modifiers = []

        if factors.get("age", 0) > 65:
            modifiers.append({"factor": "advanced_age", "effect": "increase", "reason": "Reduced renal clearance in elderly"})
        if factors.get("ckd", False):
            modifiers.append({"factor": "chronic_kidney_disease", "effect": "increase", "reason": "Impaired toxin clearance"})
        if factors.get("ethanol_co_ingestion", False):
            modifiers.append({"factor": "ethanol_co_ingestion", "effect": "decrease", "reason": "Competitive metabolism delays toxic alcohol metabolism"})
        if factors.get("pregnancy", False):
            modifiers.append({"factor": "pregnancy", "effect": "increase", "reason": "Fetal toxicity risk, altered Vd"})
        if factors.get("liver_disease", False):
            modifiers.append({"factor": "liver_disease", "effect": "increase", "reason": "Impaired folate metabolism and acid-base regulation"})

        return modifiers

    def _adjust_risk(self, tier: RiskTier, modifiers: List[Dict[str, str]]) -> str:
        """Determine adjusted risk level after modifiers."""
        increase_count = sum(1 for m in modifiers if m["effect"] == "increase")
        decrease_count = sum(1 for m in modifiers if m["effect"] == "decrease")

        tier_idx = next(i for i, t in enumerate(self.tiers) if t.tier_id == tier.tier_id)
        adjusted_idx = min(max(tier_idx + increase_count - decrease_count, 0), len(self.tiers) - 1)

        return self.tiers[adjusted_idx].name

    def _generate_protocol(self, tier: RiskTier, modifiers: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate a clinical protocol recommendation."""
        return {
            "pathway": tier.clinical_pathway,
            "monitoring": tier.monitoring_frequency,
            "interventions": tier.interventions,
            "specialist_referral": tier.specialist_referral,
            "modifier_notes": [m["reason"] for m in modifiers],
        }

    def get_all_tiers(self) -> List[Dict[str, Any]]:
        """Return all defined risk tiers."""
        return [asdict(t) for t in self.tiers]

    def identify_trial_candidates(self, patients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify patients eligible for clinical trials based on score criteria."""
        candidates = []
        for p in patients:
            result = self.stratify(
                osmolal_gap=p.get("osmolal_gap", 0),
                anion_gap=p.get("anion_gap", 0),
                additional_factors=p.get("factors", {}),
            )
            tier = result["risk_tier"]
            if tier.get("trial_eligibility") in ("treatment_eligible", "urgent_treatment"):
                candidates.append({
                    "patient_id": p.get("patient_id", "unknown"),
                    "score": result["combined_score"],
                    "tier": tier["name"],
                    "trial_eligibility": tier["trial_eligibility"],
                })
        return candidates
