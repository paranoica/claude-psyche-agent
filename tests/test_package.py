import zipfile
from pathlib import Path

import pytest

from tools.check_skill import REPO_SKILL
from tools.package import PackageError, build_zip


def test_zip_has_single_psyche_folder_with_all_skill_files(tmp_path: Path) -> None:
    out = build_zip(REPO_SKILL, tmp_path / "psyche.zip")

    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
    expected = sorted(
        "psyche/" + p.relative_to(REPO_SKILL).as_posix()
        for p in REPO_SKILL.rglob("*")
        if p.is_file()
    )
    assert sorted(names) == expected
    assert "psyche/SKILL.md" in names
    assert "psyche/ядро/сон/сон.md" in names


def test_cyrillic_names_flagged_utf8(tmp_path: Path) -> None:
    out = build_zip(REPO_SKILL, tmp_path / "psyche.zip")

    with zipfile.ZipFile(out) as zf:
        info = zf.getinfo("psyche/навигатор.md")
    assert info.flag_bits & 0x800


def test_zip_content_equals_source(tmp_path: Path) -> None:
    out = build_zip(REPO_SKILL, tmp_path / "psyche.zip")

    with zipfile.ZipFile(out) as zf:
        assert zf.read("psyche/SKILL.md") == (REPO_SKILL / "SKILL.md").read_bytes()


def test_build_is_reproducible(tmp_path: Path) -> None:
    a = build_zip(REPO_SKILL, tmp_path / "a.zip").read_bytes()
    b = build_zip(REPO_SKILL, tmp_path / "b.zip").read_bytes()
    assert a == b


def test_hidden_and_cache_files_are_skipped(tmp_path: Path) -> None:
    skill = tmp_path / "psyche"
    skill.mkdir()
    (skill / "SKILL.md").write_text("x", encoding="utf-8")
    (skill / ".DS_Store").write_text("x", encoding="utf-8")
    (skill / "__pycache__").mkdir()
    (skill / "__pycache__" / "a.pyc").write_text("x", encoding="utf-8")

    out = build_zip(skill, tmp_path / "out.zip", run_checks=False)

    with zipfile.ZipFile(out) as zf:
        assert zf.namelist() == ["psyche/SKILL.md"]


def test_failing_checks_stop_the_build(tmp_path: Path) -> None:
    skill = tmp_path / "psyche"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# no frontmatter\n", encoding="utf-8")
    target = tmp_path / "out.zip"

    with pytest.raises(PackageError, match="frontmatter"):
        build_zip(skill, target)
    assert not target.exists()


def test_zip_is_world_readable(tmp_path: Path) -> None:
    out = build_zip(REPO_SKILL, tmp_path / "psyche.zip")
    assert out.stat().st_mode & 0o777 == 0o644
