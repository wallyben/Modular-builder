from __future__ import annotations

import json
import sys
from pathlib import Path


def cmd_tender_matrix(
    path_arg: str,
    score: bool = False,
    export_path: str | None = None,
) -> None:
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

    summary = None
    gaps = None

    if score:
        summary = score_matrix(matrix)
        print(json.dumps(summary.model_dump(), indent=2))
        gaps = identify_evidence_gaps(extraction, matrix)
        print(json.dumps([g.model_dump() for g in gaps], indent=2))

    if export_path:
        from modules.tender.export import export_win_pack_docx
        out = export_win_pack_docx(export_path, text, extraction, matrix, summary, gaps)
        print(out)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python main.py <command> [args...]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "prospect-from-award":
        if len(sys.argv) < 3:
            print("Usage: python main.py prospect-from-award <path_to_txt>", file=sys.stderr)
            sys.exit(1)
        from modules.prospecting import (
            draft_outreach,
            extract_award_notice,
            record_outreach,
            score_prospect,
        )
        from modules.prospecting.tracker import ensure_data_dir
        ensure_data_dir()
        text = Path(sys.argv[2]).read_text(encoding="utf-8")
        award = extract_award_notice(text)
        prospect = score_prospect(award)
        draft = draft_outreach(prospect)
        print(json.dumps(prospect.model_dump(), indent=2))
        print(json.dumps(draft.model_dump(), indent=2))
        record_outreach(prospect.company_name, email=None, status="drafted")

    elif command == "tender-demo":
        from modules.tender.demo import run_demo_flow
        result = run_demo_flow(adapter=None)
        summary = result["summary"]
        extraction = result["extraction"]
        print(json.dumps(summary.model_dump(), indent=2))
        print(f"Requirements: {len(extraction.requirements)}")
        print(f"Score: {summary.score:.2%}")

    elif command == "tender-matrix":
        if len(sys.argv) < 3:
            print("Usage: python main.py tender-matrix <path> [--score]", file=sys.stderr)
            sys.exit(1)
        args = sys.argv[3:]
        score_flag = "--score" in args
        export_path = None
        if "--export" in args:
            idx = args.index("--export")
            if idx + 1 >= len(args):
                print("Error: --export requires a path argument", file=sys.stderr)
                sys.exit(1)
            export_path = args[idx + 1]
        cmd_tender_matrix(sys.argv[2], score=score_flag, export_path=export_path)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
