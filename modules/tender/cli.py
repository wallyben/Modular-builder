"""Minimal CLI for tender matrix analysis.

Usage:
    python -m modules.tender.cli <file.txt> [--score]

With --score: prints mandatory_score, rated_score,
              evidence_map JSON, and disqualify_flags JSON.
"""
from __future__ import annotations

import argparse
import json
import sys

from modules.tender.hardening import (
    TenderExtraction,
    TenderMatrix,
    build_evidence_map,
    calculate_split_scores,
    classify_requirement_levels,
    detect_disqualify_flags,
    detect_mandatory_gaps,
)


def _build_extraction(lines: list[str]) -> TenderExtraction:
    return [{"id": str(i + 1), "text": line, "level": ""} for i, line in enumerate(lines)]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="tender-matrix")
    parser.add_argument("file", help="Path to tender .txt file")
    parser.add_argument(
        "--score",
        action="store_true",
        help="Include split scores, evidence map, and disqualify flags",
    )
    args = parser.parse_args(argv)

    try:
        text = open(args.file).read()
    except OSError as exc:
        print(f"Error reading file: {exc}", file=sys.stderr)
        sys.exit(1)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    extraction = _build_extraction(lines)
    classification = classify_requirement_levels(extraction)

    output: dict = {"classification": classification}

    if args.score:
        tender_matrix: TenderMatrix = [
            {"requirement_id": req["id"], "status": ""} for req in extraction
        ]
        split_scores = calculate_split_scores(tender_matrix, classification)
        mandatory_gaps = detect_mandatory_gaps(tender_matrix, classification["mandatory_ids"])
        evidence_map = build_evidence_map(extraction)
        disqualify_flags = detect_disqualify_flags(extraction)

        output["mandatory_score"] = split_scores["mandatory_score"]
        output["rated_score"] = split_scores["rated_score"]
        output["mandatory_gaps"] = mandatory_gaps
        output["evidence_map"] = [item.model_dump() for item in evidence_map]
        output["disqualify_flags"] = [flag.model_dump() for flag in disqualify_flags]

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
