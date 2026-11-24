"""Compare how many bytes the old and the new skill load per acceptance scenario.

Old sizes are fixed byte counts of the previous version of the skill, which is
not in this repository; new files are measured on disk. Memory files (the journal
on claude.ai, the empty profile/notes templates of the old skill) are left out on
both sides.

Usage:
    python -m tools.measure
"""

from __future__ import annotations

import argparse
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

from tools.check_skill import REPO_SKILL

OLD_SIZES = {
    "SKILL.md": 24795,
    "навигатор.md": 13709,
    "ядро/сон.md": 12241,
    "ядро/антипаттерны.md": 14141,
    "ядро/фарма.md": 47370,
    "ядро/настроение.md": 22862,
}


@dataclass(frozen=True)
class Scenario:
    """Files one acceptance scenario is expected to load.

    Attributes:
        name: Short label, numbered as in tests/scenarios.md.
        old: Paths in the old skill, relative to its root.
        new: Paths in the new skill, relative to its root.
    """

    name: str
    old: tuple[str, ...]
    new: tuple[str, ...]


SCENARIOS = (
    Scenario("1 первая сессия", ("SKILL.md",), ("SKILL.md",)),
    Scenario("2 хочу поговорить, затык", ("SKILL.md",), ("SKILL.md",)),
    Scenario(
        "3 сон, потом разбор",
        ("SKILL.md", "навигатор.md", "ядро/сон.md"),
        ("SKILL.md", "навигатор.md", "ядро/сон/сон.md"),
    ),
    Scenario(
        "4 скажи дозу, по кусочкам",
        ("SKILL.md", "навигатор.md", "ядро/антипаттерны.md", "ядро/фарма.md"),
        (
            "SKILL.md",
            "навигатор.md",
            "ядро/антипаттерны/заходы.md",
            "ядро/фарма/_карта.md",
            "ядро/фарма/_рамка.md",
            "ядро/фарма/бензодиазепины.md",
        ),
    ),
    Scenario(
        "5 лучше бы не просыпаться",
        ("SKILL.md", "навигатор.md", "ядро/настроение.md"),
        ("SKILL.md", "навигатор.md", "ядро/настроение/депрессия.md"),
    ),
    Scenario("6 подготовка к терапевту", ("SKILL.md",), ("SKILL.md", "подготовка.md")),
    Scenario("7 повторная сессия", ("SKILL.md",), ("SKILL.md",)),
    Scenario("8 запись в журнал", ("SKILL.md",), ("SKILL.md", "журнал_шаблон.md")),
)


@dataclass(frozen=True)
class Row:
    """Measured sizes of one scenario."""

    name: str
    old: int
    new: int

    @property
    def ratio(self) -> float:
        """How many times the new load is smaller than the old one."""
        return self.old / self.new


def summarize(rows: list[Row]) -> dict[str, float]:
    """Aggregate per-scenario rows.

    Args:
        rows: At least one measured scenario.

    Returns:
        ``total`` (sum old / sum new), ``mean`` and ``worst`` per-scenario ratios.
    """
    if not rows:
        raise ValueError("no scenarios to summarize")
    return {
        "total": sum(r.old for r in rows) / sum(r.new for r in rows),
        "mean": statistics.fmean(r.ratio for r in rows),
        "worst": min(r.ratio for r in rows),
    }


def measure(skill: Path = REPO_SKILL) -> list[Row]:
    """Measure every scenario.

    Args:
        skill: Folder of the new skill.

    Returns:
        One row per scenario, in order.
    """
    return [
        Row(
            s.name,
            sum(OLD_SIZES[p] for p in s.old),
            sum((skill / p).stat().st_size for p in s.new),
        )
        for s in SCENARIOS
    ]


def main(argv: list[str] | None = None) -> int:
    """Print the comparison table."""
    argparse.ArgumentParser(description="Compare loaded bytes per scenario.").parse_args(argv)

    rows = measure()
    width = max(len(r.name) for r in rows)
    print(f"{'сценарий':<{width}}  {'было':>7}  {'стало':>7}  кратность")
    for r in rows:
        print(f"{r.name:<{width}}  {r.old:>7}  {r.new:>7}  {r.ratio:>6.2f}x")
    s = summarize(rows)
    print(f"\nсумма: {s['total']:.2f}x  среднее: {s['mean']:.2f}x  худший: {s['worst']:.2f}x")
    return 0


if __name__ == "__main__":
    sys.exit(main())
