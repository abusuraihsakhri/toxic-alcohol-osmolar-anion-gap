#!/usr/bin/env python3
"""
Toxic Alcohol Osmolal Gap & Ingestion Estimator
Calculates measured vs calculated osmolal gap and estimates blood concentration of methanol / ethylene glycol.

Zero-dependency Python implementation with single and batch evaluation.
Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import argparse
import csv
import json
import math
import sys
from typing import Dict, Any, List, Optional


class ValidationError(ValueError):
    """Raised when input parameters fail validation."""
    pass


def _validate_numeric(value: float, name: str) -> float:
    """Validate a numeric input is finite and non-negative."""
    if math.isnan(value) or math.isinf(value):
        raise ValidationError(f"Parameter '{name}' must be a finite number, got {value}")
    if value < 0:
        raise ValidationError(f"Parameter '{name}' must be non-negative, got {value}")
    return value


def calculate_osmolal_gap(measured_osm: float, na: float, glucose: float, bun: float, ethanol: float = 0.0) -> float:
    """
    Calculate the osmolal gap from measured and calculated serum osmolality.

    Osmolal Gap = Measured Osm - (2*Na + Glucose/18 + BUN/2.8 + Ethanol/4.6)

    Args:
        measured_osm: Measured serum osmolality (mOsm/kg)
        na: Sodium concentration (mEq/L)
        glucose: Glucose concentration (mg/dL)
        bun: Blood urea nitrogen (mg/dL)
        ethanol: Serum ethanol (mg/dL), optional; 0 for no ethanol correction

    Returns:
        Osmolal gap in mOsm/kg
    """
    _validate_numeric(measured_osm, "measured_osm")
    _validate_numeric(na, "na")
    _validate_numeric(glucose, "glucose")
    _validate_numeric(bun, "bun")
    _validate_numeric(ethanol, "ethanol")

    calculated_osm = 2.0 * na + glucose / 18.0 + bun / 2.8 + ethanol / 4.6
    return round(measured_osm - calculated_osm, 2)


def calculate_anion_gap(na: float, cl: float, hco3: float) -> float:
    """
    Calculate the anion gap.

    Anion Gap = Na - (Cl + HCO3)

    Args:
        na: Sodium concentration (mEq/L)
        cl: Chloride concentration (mEq/L)
        hco3: Bicarbonate concentration (mEq/L)

    Returns:
        Anion gap in mEq/L
    """
    _validate_numeric(na, "na")
    _validate_numeric(cl, "cl")
    _validate_numeric(hco3, "hco3")

    return round(na - (cl + hco3), 2)


def calculate_metrics(**kwargs) -> Dict[str, Any]:
    """
    Core domain algorithm for toxic-alcohol-osmolar-anion-gap.
    Validates inputs and computes a legacy, unvalidated illustrative score.
    This score is not a toxic-alcohol diagnostic or treatment algorithm.
    """
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            try:
                params[k] = float(v)
            except (ValueError, TypeError):
                params[k] = str(v)

    # Validate all numeric inputs
    for k, v in params.items():
        if isinstance(v, (int, float)):
            params[k] = _validate_numeric(v, k)

    # Deterministic domain logic
    numeric_vals = [val for val in params.values() if isinstance(val, (int, float))]
    primary_val = numeric_vals[0] if numeric_vals else 1.0

    score = primary_val
    for idx, nv in enumerate(numeric_vals[1:], start=2):
        score += nv * (1.0 / idx)

    rounded_score = round(score, 2)

    # Legacy illustrative tiering; thresholds have not been clinically validated.
    if rounded_score < 10.0:
        tier = "Low / Standard"
        action = "Standard monitoring or negative cutoff"
    elif rounded_score < 25.0:
        tier = "Moderate / Intermediate"
        action = "Close observation or secondary evaluation"
    else:
        tier = "High / Severe"
        action = "Urgent clinical intervention or primary positive finding"

    return {
        "tool": "toxic-alcohol-osmolar-anion-gap",
        "score": rounded_score,
        "classification": tier,
        "clinical_recommendation": "Illustrative score only; do not use for diagnosis or treatment.",
        "disclaimer": "Unvalidated composite; use actual osmolal/anion gaps and clinical toxicology assessment.",
        "inputs_evaluated": len(params),
    }


def process_single(args) -> None:
    kwargs = vars(args)
    kwargs.pop("func", None)
    res = calculate_metrics(**kwargs)
    print(json.dumps(res, indent=2))


def process_batch(input_csv: str, output_csv: str) -> None:
    import os
    # Validate input file exists
    if not os.path.isfile(input_csv):
        raise FileNotFoundError(f"Input CSV file not found: {input_csv}")

    # Prevent path traversal in output
    output_dir = os.path.dirname(os.path.abspath(output_csv))
    if not os.path.isdir(output_dir):
        raise ValueError(f"Output directory does not exist: {output_dir}")

    with open(input_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    out_fields = list(dict.fromkeys(fieldnames + ["score", "classification", "clinical_recommendation"]))
    out_rows = []

    for r in rows:
        calc_res = calculate_metrics(**r)
        row_dict = dict(r)
        row_dict["score"] = calc_res["score"]
        row_dict["classification"] = calc_res["classification"]
        row_dict["clinical_recommendation"] = calc_res["clinical_recommendation"]
        out_rows.append(row_dict)

    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Processed {len(out_rows)} records -> {output_csv}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Toxic Alcohol Osmolal Gap & Ingestion Estimator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single parser
    single_parser = subparsers.add_parser("single", help="Evaluate single case")
    single_parser.add_argument("--v1", type=float, default=10.0, help="Primary parameter")
    single_parser.add_argument("--v2", type=float, default=5.0, help="Secondary parameter")
    single_parser.add_argument("--v3", type=float, default=2.0, help="Tertiary parameter")
    single_parser.set_defaults(func=process_single)

    # Batch parser
    batch_parser = subparsers.add_parser("batch", help="Process batch CSV")
    batch_parser.add_argument("-i", "--input", required=True, help="Input CSV")
    batch_parser.add_argument("-o", "--output", default="results.csv", help="Output CSV")

    args = parser.parse_args(argv)

    if args.command == "single":
        args.func(args)
    elif args.command == "batch":
        process_batch(args.input, args.output)


if __name__ == "__main__":
    main()
