from pathlib import Path

import pytest

from tools.check_skill import REPO_SKILL, check_skill

GOOD_SKILL = """---
name: psyche
description: Собеседник. Запускать ТОЛЬКО по явному вызову («psyche»).
---

# psyche

См. `навигатор.md` и `ядро/антипаттерны/заходы.md`.
"""

GOOD_NAV = """# Навигатор

Путь: `ядро/<папка>/<файл>.md`.

| тема | узел |
|---|---|
| сон | `сон/сон.md` |
| препараты | `фарма/_карта.md` |

Давление: `антипаттерны/заходы.md`.
"""

GOOD_CARD = """# Карта

Начинать с `_рамка.md`.

| класс | узел |
|---|---|
| СИОЗС | `сиозс.md` |
"""


def make_skill(root: Path, **overrides: str | None) -> Path:
    files: dict[str, str | None] = {
        "SKILL.md": GOOD_SKILL,
        "навигатор.md": GOOD_NAV,
        "журнал_шаблон.md": "Файл памяти `areas/psyche.md`.\n",
        "подготовка.md": "Источник: журнал `areas/psyche.md`.\n",
        "ядро/сон/сон.md": "## Сон\n",
        "ядро/фарма/_карта.md": GOOD_CARD,
        "ядро/фарма/_рамка.md": "## РАМКА\n",
        "ядро/фарма/сиозс.md": "## СИОЗС\n",
        "ядро/антипаттерны/заходы.md": "## Часть C\n",
    }
    files.update(overrides)
    skill = root / "psyche"
    for rel, text in files.items():
        if text is None:
            continue
        path = skill / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return skill


def test_minimal_good_skill_passes(tmp_path: Path) -> None:
    assert check_skill(make_skill(tmp_path)) == []


def test_repo_skill_passes() -> None:
    assert check_skill(REPO_SKILL) == []


def test_description_over_200_chars_fails(tmp_path: Path) -> None:
    long = "Запускать ТОЛЬКО по явному вызову. " + "а" * 170
    skill = make_skill(
        tmp_path,
        **{
            "SKILL.md": GOOD_SKILL.replace(
                "Собеседник. Запускать ТОЛЬКО по явному вызову («psyche»).", long
            )
        },
    )
    assert any("200" in p for p in check_skill(skill))


def test_description_of_exactly_200_chars_passes(tmp_path: Path) -> None:
    base = "Запускать ТОЛЬКО по явному вызову."
    desc = base + "а" * (200 - len(base))
    skill = make_skill(
        tmp_path,
        **{
            "SKILL.md": GOOD_SKILL.replace(
                "Собеседник. Запускать ТОЛЬКО по явному вызову («psyche»).", desc
            )
        },
    )
    assert check_skill(skill) == []


def test_description_without_explicit_call_condition_fails(tmp_path: Path) -> None:
    skill = make_skill(
        tmp_path,
        **{
            "SKILL.md": GOOD_SKILL.replace(
                "Запускать ТОЛЬКО по явному вызову", "Запускать при разговоре о настроении"
            )
        },
    )
    assert any("явному вызову" in p for p in check_skill(skill))


def test_wrong_name_fails(tmp_path: Path) -> None:
    skill = make_skill(tmp_path, **{"SKILL.md": GOOD_SKILL.replace("name: psyche", "name: other")})
    assert any("name" in p for p in check_skill(skill))


def test_missing_frontmatter_fails(tmp_path: Path) -> None:
    skill = make_skill(tmp_path, **{"SKILL.md": "# psyche\n"})
    assert any("frontmatter" in p for p in check_skill(skill))


@pytest.mark.parametrize(
    ("file", "bad"),
    [
        ("SKILL.md", GOOD_SKILL + "\nИ `ядро/нет/такого.md`.\n"),
        ("навигатор.md", GOOD_NAV + "\n| x | `сон/бессонница.md` |\n"),
        ("ядро/фарма/_карта.md", GOOD_CARD + "| ИМАО | `имао.md` |\n"),
        ("подготовка.md", "См. `ядро/нет.md`.\n"),
    ],
)
def test_broken_link_fails(tmp_path: Path, file: str, bad: str) -> None:
    problems = check_skill(make_skill(tmp_path, **{file: bad}))
    assert any("broken link" in p for p in problems)


def test_orphan_node_fails(tmp_path: Path) -> None:
    skill = make_skill(tmp_path, **{"ядро/сон/апноэ.md": "## Апноэ\n"})
    assert any("апноэ.md" in p and "orphan" in p for p in check_skill(skill))


@pytest.mark.parametrize("name", ["профиль.md", "заметки.md"])
def test_old_memory_files_are_rejected(tmp_path: Path, name: str) -> None:
    skill = make_skill(tmp_path, **{name: "# старое\n"})
    assert any(name in p for p in check_skill(skill))


def test_size_budget_fails_above_limit(tmp_path: Path) -> None:
    skill = make_skill(tmp_path, **{"навигатор.md": GOOD_NAV + "я" * 4000})
    assert any("навигатор.md" in p and "budget" in p for p in check_skill(skill))


def test_card_link_does_not_fall_back_to_another_folder(tmp_path: Path) -> None:
    skill = make_skill(
        tmp_path,
        **{
            "ядро/фарма/_рамка.md": None,
            "ядро/методы/_рамка.md": "## РАМКА\n",
            "ядро/методы/_карта.md": GOOD_CARD.replace("`сиозс.md`", "`кпт.md`"),
            "ядро/методы/кпт.md": "## КПТ\n",
        },
    )
    problems = check_skill(skill)
    assert any("фарма/_карта.md" in p and "_рамка.md" in p for p in problems)


def test_navigator_bare_name_is_broken(tmp_path: Path) -> None:
    skill = make_skill(tmp_path, **{"навигатор.md": GOOD_NAV + "\nСИОЗС: `сиозс.md`.\n"})
    assert any("навигатор.md" in p and "сиозс.md" in p for p in check_skill(skill))


def test_missing_prep_file_fails(tmp_path: Path) -> None:
    skill = make_skill(tmp_path, **{"подготовка.md": None})
    assert any("подготовка.md" in p for p in check_skill(skill))
