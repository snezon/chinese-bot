import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import lesson_engine


def test_load_lesson_1():
    lesson = lesson_engine.load_lesson(1)
    assert lesson["id"] == 1
    assert lesson["level"] == "hsk1"
    assert len(lesson["words"]) > 0
    assert len(lesson["exercises"]) > 0


def test_load_lesson_25():
    lesson = lesson_engine.load_lesson(25)
    assert lesson["id"] == 25
    assert lesson["level"] == "hsk1"


def test_load_lesson_26():
    lesson = lesson_engine.load_lesson(26)
    assert lesson["id"] == 26
    assert lesson["level"] == "hsk2"


def test_load_lesson_50():
    lesson = lesson_engine.load_lesson(50)
    assert lesson["id"] == 50


def test_load_lesson_not_found():
    with pytest.raises(FileNotFoundError):
        lesson_engine.load_lesson(99)


def test_load_test_hsk1():
    test = lesson_engine.load_test("hsk1")
    assert test["level"] == "hsk1"
    assert len(test["questions"]) == 30


def test_load_test_hsk2():
    test = lesson_engine.load_test("hsk2")
    assert len(test["questions"]) == 30


def test_load_test_not_found():
    with pytest.raises(FileNotFoundError):
        lesson_engine.load_test("hsk9")


def test_get_all_lesson_meta():
    meta = lesson_engine.get_all_lesson_meta()
    assert len(meta) == 50
    ids = [m["id"] for m in meta]
    assert ids == list(range(1, 51))


def test_is_lesson_1_always_unlocked():
    assert lesson_engine.is_lesson_unlocked(1, []) is True


def test_is_lesson_unlocked_requires_previous():
    assert lesson_engine.is_lesson_unlocked(2, []) is False
    progress = [{"lesson_id": 1, "completed": 1}]
    assert lesson_engine.is_lesson_unlocked(2, progress) is True


def test_is_lesson_locked_if_previous_not_completed():
    progress = [{"lesson_id": 1, "completed": 0}]
    assert lesson_engine.is_lesson_unlocked(2, progress) is False


def test_format_lesson_theory_contains_hanzi():
    lesson = lesson_engine.load_lesson(1)
    theory = lesson_engine.format_lesson_theory(lesson)
    assert "你好" in theory
    assert "nǐ hǎo" in theory


def test_all_exercises_have_valid_answer_index():
    for lesson_id in range(1, 51):
        lesson = lesson_engine.load_lesson(lesson_id)
        for ex in lesson["exercises"]:
            assert ex["type"] == "multiple_choice"
            assert 0 <= ex["answer"] < len(ex["options"]), \
                f"Lesson {lesson_id}: invalid answer index {ex['answer']}"
