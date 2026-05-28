import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tempfile
import pytest
from pathlib import Path
import db as db_module


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    db_module.init_db()


def test_lesson_progress_default():
    p = db_module.get_lesson_progress(1)
    assert p["completed"] == 0
    assert p["attempts"] == 0


def test_save_lesson_result_pass():
    db_module.save_lesson_result(1, 0.8)
    p = db_module.get_lesson_progress(1)
    assert p["completed"] == 1
    assert p["score"] == pytest.approx(0.8)
    assert p["attempts"] == 1


def test_save_lesson_result_fail():
    db_module.save_lesson_result(2, 0.4)
    p = db_module.get_lesson_progress(2)
    assert p["completed"] == 0


def test_save_lesson_keeps_best_score():
    db_module.save_lesson_result(3, 0.6)
    db_module.save_lesson_result(3, 0.4)
    p = db_module.get_lesson_progress(3)
    assert p["score"] == pytest.approx(0.6)
    assert p["attempts"] == 2


def test_test_result_default():
    r = db_module.get_test_result("hsk1")
    assert r["passed"] == 0
    assert r["best_score"] == pytest.approx(0.0)


def test_save_test_result_pass():
    db_module.save_test_result("hsk1", 0.7)
    r = db_module.get_test_result("hsk1")
    assert r["passed"] == 1
    assert r["best_score"] == pytest.approx(0.7)


def test_save_test_result_fail():
    db_module.save_test_result("hsk2", 0.5)
    r = db_module.get_test_result("hsk2")
    assert r["passed"] == 0


def test_get_all_progress_empty():
    assert db_module.get_all_progress() == []


def test_get_all_progress_sorted():
    db_module.save_lesson_result(5, 1.0)
    db_module.save_lesson_result(2, 1.0)
    rows = db_module.get_all_progress()
    ids = [r["lesson_id"] for r in rows]
    assert ids == sorted(ids)
