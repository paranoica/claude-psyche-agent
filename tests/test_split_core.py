import subprocess
from pathlib import Path

import pytest

from tools.split_core import SplitError, _git_show, find_drift, split_text

SAMPLE = (
    "# Ядро · Пример\n"
    "\n"
    "**Статус блока: готов.**\n"
    "\n"
    "---\n"
    "\n"
    "## Первый узел (first)\n"
    "\n"
    "### 1. Признаки\n"
    "текст первого\n"
    "\n"
    "---\n"
    "\n"
    "## Второй узел\n"
    "текст второго\n"
    "\n"
    "> Примечание: сноска.\n"
)


def test_header_is_dropped_and_nodes_keep_their_text() -> None:
    result = split_text(SAMPLE, [("Первый узел", "a/first.md"), ("Второй узел", "a/second.md")])

    assert result.header == "# Ядро · Пример\n\n**Статус блока: готов.**\n\n---\n\n"
    assert result.files == {
        "a/first.md": "## Первый узел (first)\n\n### 1. Признаки\nтекст первого\n",
        "a/second.md": "## Второй узел\nтекст второго\n\n> Примечание: сноска.\n",
    }


def test_sections_mapped_to_one_file_are_joined_in_order() -> None:
    result = split_text(SAMPLE, [("Первый", "a/_frame.md"), ("Второй", "a/_frame.md")])

    assert list(result.files) == ["a/_frame.md"]
    body = result.files["a/_frame.md"]
    assert body.index("## Первый") < body.index("## Второй")
    assert "---" not in body


def test_only_separator_whitespace_is_removed() -> None:
    result = split_text(SAMPLE, [("Первый", "x.md"), ("Второй", "y.md")])
    rebuilt = result.header + "".join(
        body + tail for body, tail in zip(result.files.values(), result.tails, strict=True)
    )

    assert rebuilt == SAMPLE


def test_horizontal_rule_inside_a_node_is_kept() -> None:
    text = "## Узел\nдо\n\n---\n\nпосле\n\n---\n\n## Следующий\nконец\n"
    result = split_text(text, [("Узел", "a.md"), ("Следующий", "b.md")])

    assert result.files["a.md"] == "## Узел\nдо\n\n---\n\nпосле\n"


def test_unmapped_section_fails() -> None:
    with pytest.raises(SplitError, match="Второй узел"):
        split_text(SAMPLE, [("Первый", "a.md")])


def test_mapping_that_matches_nothing_fails() -> None:
    with pytest.raises(SplitError, match="Третий"):
        split_text(SAMPLE, [("Первый", "a.md"), ("Второй", "b.md"), ("Третий", "c.md")])


def test_prefix_matching_two_sections_fails() -> None:
    text = "## Узел один\nа\n## Узел два\nб\n"
    with pytest.raises(SplitError, match="Узел"):
        split_text(text, [("Узел", "a.md")])


def test_text_without_sections_fails() -> None:
    with pytest.raises(SplitError):
        split_text("# только заголовок\n", [("Что-то", "a.md")])


def test_drift_detects_crlf_in_node_file(tmp_path: Path) -> None:
    node = tmp_path / "сон" / "сон.md"
    node.parent.mkdir()
    node.write_bytes("## Сон\r\nтекст\r\n".encode())

    problems, extra = find_drift({node: "## Сон\nтекст\n"}, tmp_path, frozenset())

    assert problems == [node]
    assert extra == []


def test_drift_reports_missing_and_extra_files(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    stray = tmp_path / "a" / "stray.md"
    stray.write_text("x", encoding="utf-8")
    kept = tmp_path / "a" / "kept.md"
    kept.write_text("x", encoding="utf-8")
    top = tmp_path / "top.md"
    top.write_text("x", encoding="utf-8")
    missing = tmp_path / "a" / "missing.md"

    problems, extra = find_drift({missing: "x"}, tmp_path, frozenset({kept}))

    assert problems == [missing]
    assert extra == [stray]


def test_git_show_keeps_crlf(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    run = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.autocrlf=false"]
    subprocess.run(["git", "init", "-q"], check=True)
    (tmp_path / "f.md").write_bytes(b"a\r\n")
    subprocess.run([*run, "add", "f.md"], check=True)
    subprocess.run([*run, "commit", "-qm", "x"], check=True)

    assert _git_show("HEAD", "f.md") == "a\r\n"
