"""Static checks for the skill folder before it is packed for claude.ai.

Usage:
    python -m tools.check_skill [SKILL_DIR]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_SKILL = Path(__file__).resolve().parent.parent / "skill" / "psyche"

DESCRIPTION_LIMIT = 200
EXPLICIT_CALL = "ТОЛЬКО по явному вызову"
BUDGETS = {"SKILL.md": 10500, "навигатор.md": 4000}
FORBIDDEN = ("профиль.md", "заметки.md")
MEMORY_FILES = frozenset({"areas/psyche.md"})
ALLOWED_ORPHANS = frozenset({"антипаттерны/_как_пользоваться.md"})

_LINK = re.compile(r"`([^`\s<>]+\.md)`")


def _frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return fields


def _check_frontmatter(skill: Path) -> list[str]:
    fields = _frontmatter((skill / "SKILL.md").read_text(encoding="utf-8"))
    if fields is None:
        return ["SKILL.md: missing frontmatter"]
    problems = []
    if fields.get("name") != "psyche":
        problems.append(f"SKILL.md: name is {fields.get('name')!r}, expected 'psyche'")
    description = fields.get("description", "")
    if len(description) > DESCRIPTION_LIMIT:
        problems.append(
            f"SKILL.md: description is {len(description)} chars, limit {DESCRIPTION_LIMIT}"
        )
    if EXPLICIT_CALL not in description:
        problems.append(f"SKILL.md: description lacks «{EXPLICIT_CALL}»")
    return problems


def _resolve(link: str, bases: tuple[Path, ...]) -> Path | None:
    for base in bases:
        candidate = base / link
        if candidate.is_file():
            return candidate
    return None


def _check_links(skill: Path) -> list[str]:
    core = skill / "ядро"
    core_files = sorted(core.rglob("*.md")) if core.is_dir() else []
    # Each file names paths the way the model reads them: SKILL.md from the skill
    # root, the navigator from the core, a block map from its own folder.
    sources: list[tuple[Path, tuple[Path, ...]]] = [
        (skill / "SKILL.md", (skill,)),
        (skill / "навигатор.md", (core,)),
        (skill / "журнал_шаблон.md", (skill,)),
        (skill / "подготовка.md", (skill,)),
    ]
    if core.is_dir():
        sources += [(card, (card.parent,)) for card in sorted(core.rglob("_карта.md"))]

    problems = []
    reached: set[Path] = set()
    for source, bases in sources:
        if not source.is_file():
            problems.append(f"missing file: {source.relative_to(skill)}")
            continue
        for link in _LINK.findall(source.read_text(encoding="utf-8")):
            if link in MEMORY_FILES:
                continue
            target = _resolve(link, bases)
            if target is None:
                problems.append(f"{source.relative_to(skill)}: broken link `{link}`")
            else:
                reached.add(target.resolve())

    for path in core_files:
        rel = path.relative_to(core).as_posix()
        if path.resolve() not in reached and rel not in ALLOWED_ORPHANS:
            problems.append(f"orphan node, nothing links to it: ядро/{rel}")
    return problems


def check_skill(skill: Path) -> list[str]:
    """Check a skill folder.

    Args:
        skill: Folder holding SKILL.md.

    Returns:
        Human-readable problems; empty when the folder is fine.
    """
    if not (skill / "SKILL.md").is_file():
        return [f"{skill}: no SKILL.md"]

    problems = _check_frontmatter(skill)
    problems += _check_links(skill)
    for name in FORBIDDEN:
        problems += [f"old memory file must be gone: {p}" for p in skill.rglob(name)]
    for name, limit in BUDGETS.items():
        path = skill / name
        if path.is_file() and (size := path.stat().st_size) > limit:
            problems.append(f"{name}: {size} bytes, budget {limit}")
    return problems


def main(argv: list[str] | None = None) -> int:
    """Print problems for the skill folder and return a shell exit code."""
    args = sys.argv[1:] if argv is None else argv
    skill = Path(args[0]) if args else REPO_SKILL
    problems = check_skill(skill)
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        return 1
    print(f"ok: {skill}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
