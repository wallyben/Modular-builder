from __future__ import annotations

import json
import sys
from pathlib import Path


def cmd_tender_matrix(path_arg: str) -> None:
    p = Path(path_arg)
    if p.suffix != ".txt":
        print(f"Error: expected a .txt file, got '{p.suffix}'", file=sys.stderr)
        sys.exit(1)

    text = p.read_text(encoding="utf-8")

    from modules.tender import build_compliance_matrix, extract_requirements_from_text

    extraction = extract_requirements_from_text(text, adapter=None)
    matrix = build_compliance_matrix(extraction)
    print(json.dumps(matrix.model_dump(), indent=2))


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python main.py <command> [args...]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "tender-matrix":
        if len(sys.argv) < 3:
            print("Usage: python main.py tender-matrix <path>", file=sys.stderr)
            sys.exit(1)
        cmd_tender_matrix(sys.argv[2])
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
