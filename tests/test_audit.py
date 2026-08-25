from pathlib import Path

from biomed_repro.audit import file_sha256, seed_everything, stable_json_sha256


def test_json_hash_is_order_independent():
    a = stable_json_sha256({"alpha": 1, "beta": [2, 3]})
    b = stable_json_sha256({"beta": [2, 3], "alpha": 1})
    assert a == b


def test_json_hash_changes_with_configuration():
    assert stable_json_sha256({"seed": 1}) != stable_json_sha256({"seed": 2})


def test_file_hash(tmp_path: Path):
    p = tmp_path / "data.csv"
    p.write_text("x,y\n1,2\n", encoding="utf-8")
    first = file_sha256(p)
    second = file_sha256(p)
    assert first == second
    p.write_text("x,y\n1,3\n", encoding="utf-8")
    assert file_sha256(p) != first


def test_seed_function_returns_normalized_seed():
    assert seed_everything("42") == 42
