from __future__ import annotations

import json
import sys
from pathlib import Path


def cmd_tender_matrix(path_arg: str, score: bool = False) -> None:
    p = Path(path_arg)
    if p.suffix != ".txt":
        print(f"Error: expected a .txt file, got '{p.suffix}'", file=sys.stderr)
        sys.exit(1)

    text = p.read_text(encoding="utf-8")

    from modules.tender import build_compliance_matrix, extract_requirements_from_text
    from modules.tender.scoring import identify_evidence_gaps, score_matrix

    extraction = extract_requirements_from_text(text, adapter=None)
    matrix = build_compliance_matrix(extraction)
    print(json.dumps(matrix.model_dump(), indent=2))

    if score:
        summary = score_matrix(matrix)
        print(json.dumps(summary.model_dump(), indent=2))
        gaps = identify_evidence_gaps(extraction, matrix)
        print(json.dumps([g.model_dump() for g in gaps], indent=2))


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python main.py <command> [args...]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "tender-matrix":
        if len(sys.argv) < 3:
            print("Usage: python main.py tender-matrix <path> [--score]", file=sys.stderr)
            sys.exit(1)
        score_flag = "--score" in sys.argv[3:]
        cmd_tender_matrix(sys.argv[2], score=score_flag)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
