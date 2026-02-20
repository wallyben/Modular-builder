from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List

from core.buildspec import ModuleSpec

_LOG = logging.getLogger(__name__)


class ArtifactValidator:
    def __init__(self, output_dir: str, generated_files: List[str], last_pytest_exit_code: int) -> None:
        self._output_dir = Path(output_dir)
        self._generated_files = generated_files
        self._last_pytest_exit_code = last_pytest_exit_code
        self._failures: List[str] = []

    def validate_file_count(self, max_files: int) -> bool:
        count = len(self._generated_files)
        if count > max_files:
            msg = f"file count {count} exceeds max_files {max_files}"
            _LOG.error("VALIDATE FAIL %s", msg)
            self._failures.append(msg)
            return False
        _LOG.debug("VALIDATE OK file_count=%d max_files=%d", count, max_files)
        return True

    def validate_required_modules(self, modules: List[ModuleSpec]) -> bool:
        ok = True
        for module in modules:
            if not module.required:
                continue
            expected = self._output_dir / f"{module.name}.py"
            if not expected.exists():
                msg = f"required module file missing: {expected}"
                _LOG.error("VALIDATE FAIL %s", msg)
                self._failures.append(msg)
                ok = False
            else:
                _LOG.debug("VALIDATE OK required_module=%s", module.name)
        return ok

    def validate_tests_pass(self, test_required: bool) -> bool:
        if not test_required:
            _LOG.debug("VALIDATE SKIP tests_required=False")
            return True
        if self._last_pytest_exit_code != 0:
            msg = f"pytest exited with code {self._last_pytest_exit_code}"
            _LOG.error("VALIDATE FAIL %s", msg)
            self._failures.append(msg)
            return False
        _LOG.debug("VALIDATE OK pytest_exit_code=0")
        return True

    def validate_build_integrity(self) -> bool:
        passed = not self._failures
        if passed:
            _LOG.info("VALIDATE INTEGRITY OK")
        else:
            _LOG.error("VALIDATE INTEGRITY FAIL reasons=%s", self._failures)
        return passed
