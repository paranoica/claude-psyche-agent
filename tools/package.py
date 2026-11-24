"""Pack skill/psyche into a zip for upload on claude.ai.

Runs the static checks and the core split check first; nothing is written if
either fails. The zip holds a single ``psyche/`` folder and is byte-identical
across runs for the same sources.

Usage:
    python -m tools.package [--out dist/psyche.zip]
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import zipfile
from pathlib import Path

from tools import split_core
from tools.check_skill import REPO_SKILL, check_skill

DEFAULT_OUT = REPO_SKILL.parent.parent / "dist" / "psyche.zip"
_FIXED_TIME = (1980, 1, 1, 0, 0, 0)
_SKIP_DIRS = frozenset({"__pycache__"})


class PackageError(Exception):
    """The skill folder is not fit to be packed."""


def _skill_files(skill: Path) -> list[Path]:
    files = []
    for path in skill.rglob("*"):
        rel = path.relative_to(skill)
        if not path.is_file() or any(
            part.startswith(".") or part in _SKIP_DIRS for part in rel.parts
        ):
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(skill).as_posix())


def build_zip(skill: Path, target: Path, *, run_checks: bool = True) -> Path:
    """Write the skill folder into a zip.

    Args:
        skill: Folder holding SKILL.md; its name becomes the top folder in the zip.
        target: Zip path to write; replaced atomically.
        run_checks: Run ``check_skill`` first and refuse on any problem.

    Returns:
        The written zip path.

    Raises:
        PackageError: If the checks report problems.
    """
    if run_checks and (problems := check_skill(skill)):
        raise PackageError("\n".join(problems))

    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=target.parent, suffix=".zip.tmp")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in _skill_files(skill):
                info = zipfile.ZipInfo(
                    f"{skill.name}/{path.relative_to(skill).as_posix()}", _FIXED_TIME
                )
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                zf.writestr(info, path.read_bytes())
        tmp.chmod(0o644)
        tmp.replace(target)
    finally:
        tmp.unlink(missing_ok=True)
    return target


def main(argv: list[str] | None = None) -> int:
    """Check and pack the repo skill."""
    parser = argparse.ArgumentParser(description="Pack the skill for claude.ai.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="zip path to write")
    args = parser.parse_args(argv)

    if split_core.main(["--rev", split_core.BASELINE, "--check"]) != 0:
        print("core split check failed, see MAINTAINING.md", file=sys.stderr)
        return 1
    try:
        out = build_zip(REPO_SKILL, args.out)
    except PackageError as err:
        print(err, file=sys.stderr)
        return 1
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
