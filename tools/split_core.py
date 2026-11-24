"""Split the old cluster files of the knowledge core into one file per node.

The text of every node is copied byte for byte. Only the file header (title and
review status, which now live in MAINTAINING.md) and the ``---`` separators
between nodes are dropped, and the split refuses to write anything unless the
original file can be rebuilt from header + nodes + separators.

Usage:
    python -m tools.split_core --rev 9f920c0            # write the node files
    python -m tools.split_core --rev 9f920c0 --check    # verify them, exit 1 on drift
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

SOURCE_DIR = "skill/psyche/ядро"
BASELINE = "9f920c0"
OUT_DIR = Path(__file__).resolve().parent.parent / "skill" / "psyche" / "ядро"
HANDWRITTEN = frozenset({OUT_DIR / "фарма/_карта.md", OUT_DIR / "методы/_карта.md"})

MAP: dict[str, list[tuple[str, str]]] = {
    "настроение.md": [
        ("Депрессивный эпизод", "настроение/депрессия.md"),
        ("Скрининг биполярного", "настроение/биполяр.md"),
    ],
    "тревога.md": [
        ("Генерализованное тревожное", "тревога/гтр.md"),
        ("Паническое расстройство", "тревога/паника.md"),
        ("Социальное тревожное", "тревога/соц_тревога.md"),
        ("Обсессивно-компульсивное", "тревога/окр.md"),
    ],
    "травма_стресс.md": [
        ("ПТСР и комплексное", "травма_стресс/птср.md"),
        ("Стресс, расстройство адаптации", "травма_стресс/адаптация_выгорание.md"),
        ("Горе", "травма_стресс/горе.md"),
    ],
    "психоз.md": [("Психотический спектр", "психоз/психоз.md")],
    "личность.md": [("Расстройства личности", "личность/прл.md")],
    "пищевое.md": [("Расстройства пищевого", "пищевое/рпп.md")],
    "зависимости.md": [("Зависимости", "зависимости/зависимости.md")],
    "сон.md": [("Нарушения сна", "сон/сон.md")],
    "сдвг.md": [("СДВГ у взрослых", "сдвг/сдвг.md")],
    "методы.md": [
        ("РАМКА", "методы/_рамка.md"),
        ("Доказательность", "методы/_рамка.md"),
        ("Когнитивно-поведенческая", "методы/кпт.md"),
        ("Поведенческая активация", "методы/поведенческая_активация.md"),
        ("Экспозиционная терапия", "методы/экспозиция_эпр.md"),
        ("Диалектическая", "методы/дпт.md"),
        ("Терапия принятия", "методы/акт.md"),
        ("Схема-терапия", "методы/схема_терапия.md"),
        ("Психодинамическая", "методы/психодинамическая.md"),
        ("Межличностная", "методы/ипт.md"),
        ("Травмофокусированные", "методы/травмофокусированные_emdr.md"),
        ("Осознанность", "методы/осознанность_mbct.md"),
        ("Общие факторы", "методы/общие_факторы.md"),
    ],
    "фарма.md": [
        ("РАМКА", "фарма/_рамка.md"),
        ("Про статус в РБ", "фарма/_рамка.md"),
        ("Антидепрессанты: СИОЗС ", "фарма/сиозс.md"),
        ("Антидепрессанты: СИОЗСиН", "фарма/сиозсин.md"),
        ("Антидепрессанты: атипичные", "фарма/атипичные_ад.md"),
        ("Антидепрессанты: трициклические", "фарма/тца.md"),
        ("Антидепрессанты: ИМАО", "фарма/имао.md"),
        ("Нормотимики", "фарма/нормотимики.md"),
        ("Антипсихотики", "фарма/антипсихотики.md"),
        ("Бензодиазепины", "фарма/бензодиазепины.md"),
        ("Небензодиазепиновые", "фарма/снотворные_анксиолитики.md"),
        ("Препараты при СДВГ", "фарма/сдвг_препараты.md"),
        ("Сводная заметка", "фарма/_источники.md"),
    ],
    "антипаттерны.md": [
        ("Часть A", "антипаттерны/рассуждение.md"),
        ("Часть B", "антипаттерны/поведение.md"),
        ("Часть C", "антипаттерны/заходы.md"),
        ("Как пользоваться", "антипаттерны/_как_пользоваться.md"),
    ],
}

_SECTION = re.compile(r"^## (.+)$", re.M)
_SEPARATOR = re.compile(r"\n---\s*\Z")


class SplitError(Exception):
    """The source text and the mapping do not fit together."""


@dataclass
class Split:
    """Result of splitting one cluster file.

    Attributes:
        header: Text before the first ``## `` section, dropped from the output.
        files: Output path to node text, in source order.
        tails: Separator text removed after each section, in section order.
    """

    header: str
    files: dict[str, str] = field(default_factory=dict)
    tails: list[str] = field(default_factory=list)


def _match(title: str, mapping: list[tuple[str, str]]) -> tuple[str, str]:
    hits = [entry for entry in mapping if title.startswith(entry[0])]
    if len(hits) != 1:
        raise SplitError(f"section {title!r} matches {len(hits)} mapping entries, need 1")
    return hits[0]


def split_text(text: str, mapping: list[tuple[str, str]]) -> Split:
    """Split a cluster file into node texts.

    Args:
        text: Full text of the old cluster file.
        mapping: ``(title prefix, output path)`` pairs. Every section must match
            exactly one prefix and every prefix exactly one section. Sections
            sharing an output path are joined with a blank line.

    Returns:
        The dropped header, node texts per output path and removed separators.

    Raises:
        SplitError: On a mapping mismatch or if the original cannot be rebuilt.
    """
    starts = [m.start() for m in _SECTION.finditer(text)]
    if not starts:
        raise SplitError("no '## ' sections found")

    result = Split(header=text[: starts[0]])
    used: dict[str, int] = {prefix: 0 for prefix, _ in mapping}
    bodies: list[str] = []
    for start, end in zip(starts, [*starts[1:], len(text)], strict=True):
        chunk = text[start:end]
        title = _SECTION.match(chunk).group(1)  # type: ignore[union-attr]
        prefix, dest = _match(title, mapping)
        used[prefix] += 1

        stripped = chunk.rstrip()
        while _SEPARATOR.search(stripped):
            stripped = _SEPARATOR.sub("", stripped).rstrip()
        if not chunk[len(stripped) :].startswith("\n"):
            raise SplitError(f"section {title!r} does not end with a newline")
        body = stripped + "\n"
        bodies.append(body)
        result.tails.append(chunk[len(body) :])
        result.files[dest] = result.files[dest] + "\n" + body if dest in result.files else body

    unused = [prefix for prefix, count in used.items() if count != 1]
    if unused:
        raise SplitError(f"mapping entries without exactly one section: {unused}")

    rebuilt = result.header + "".join(b + t for b, t in zip(bodies, result.tails, strict=True))
    if rebuilt != text:
        raise SplitError("original text cannot be rebuilt from the split")
    return result


def _git_show(rev: str, path: str) -> str:
    blob = subprocess.run(["git", "show", f"{rev}:{path}"], check=True, capture_output=True)
    return blob.stdout.decode("utf-8")


def find_drift(
    expected: dict[Path, str], out_dir: Path, handwritten: frozenset[Path]
) -> tuple[list[Path], list[Path]]:
    """Compare node files on disk with the split, byte for byte.

    Args:
        expected: Output path to expected node text.
        out_dir: Core folder; files directly in it are not nodes and are skipped.
        handwritten: Node-level files that are not produced by the split.

    Returns:
        Files that are missing or differ, and node files the split does not produce.
    """
    problems = [
        path
        for path, body in expected.items()
        if not path.is_file() or path.read_bytes() != body.encode("utf-8")
    ]
    extra = sorted(
        p
        for p in out_dir.rglob("*.md")
        if p.parent != out_dir and p not in expected and p not in handwritten
    )
    return problems, extra


def split_all(rev: str) -> dict[Path, str]:
    """Split every mapped cluster file as it was at a git revision.

    Args:
        rev: Revision holding the old cluster files under ``SOURCE_DIR``.

    Returns:
        Output path to expected file text.
    """
    out: dict[Path, str] = {}
    for name, mapping in MAP.items():
        split = split_text(_git_show(rev, f"{SOURCE_DIR}/{name}"), mapping)
        for dest, body in split.files.items():
            out[OUT_DIR / dest] = body
    return out


def main(argv: list[str] | None = None) -> int:
    """Run the split or the check from the command line."""
    parser = argparse.ArgumentParser(description="Split the knowledge core into node files.")
    parser.add_argument("--rev", required=True, help="git revision with the old cluster files")
    parser.add_argument("--check", action="store_true", help="verify instead of writing")
    args = parser.parse_args(argv)

    expected = split_all(args.rev)
    if args.check:
        problems, extra = find_drift(expected, OUT_DIR, HANDWRITTEN)
        for path in problems:
            print(f"differs from source: {path}", file=sys.stderr)
        for path in extra:
            print(f"not produced by the split: {path}", file=sys.stderr)
        if problems or extra:
            return 1
        print(f"ok: {len(expected)} node files match {args.rev}")
        return 0

    for path, body in expected.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body.encode("utf-8"))
    print(f"wrote {len(expected)} node files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
