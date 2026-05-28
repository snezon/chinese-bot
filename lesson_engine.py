import json
from pathlib import Path
from pinyin_ru import pinyin_to_ru

LESSONS_DIR = Path(__file__).parent / "lessons"
TOTAL_LESSONS = 50


def load_lesson(lesson_id: int) -> dict:
    level = "hsk1" if lesson_id <= 25 else "hsk2"
    pattern = f"{lesson_id:02d}_*.json"
    files = list((LESSONS_DIR / level).glob(pattern))
    if not files:
        raise FileNotFoundError(f"Lesson {lesson_id} not found")
    with open(files[0], encoding="utf-8") as f:
        return json.load(f)


def load_test(level: str) -> dict:
    path = LESSONS_DIR / f"test_{level}.json"
    if not path.exists():
        raise FileNotFoundError(f"Test {level} not found")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_all_lesson_meta() -> list:
    meta = []
    for level in ("hsk1", "hsk2"):
        for path in sorted((LESSONS_DIR / level).glob("*.json")):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            meta.append({"id": data["id"], "title": data["title"], "level": level})
    return sorted(meta, key=lambda x: x["id"])


def is_lesson_unlocked(lesson_id: int, progress: list) -> bool:
    if lesson_id == 1:
        return True
    completed_ids = {p["lesson_id"] for p in progress if p["completed"]}
    return (lesson_id - 1) in completed_ids


def format_lesson_theory(lesson: dict) -> str:
    lines = [f"📚 *Урок {lesson['id']}: {lesson['title']}*\n"]
    lines.append("*Слова урока:*\n")
    for w in lesson["words"]:
        ru_sound = pinyin_to_ru(w['pinyin'])
        lines.append(f"*{w['hanzi']}* `{w['pinyin']}` _{ru_sound}_ — {w['ru']}")
        if w.get("mnemonic"):
            lines.append(f"   💡 _{w['mnemonic']}_")
        if w.get("etymology"):
            lines.append(f"   📖 _{w['etymology']}_")
        lines.append("")
    if lesson.get("grammar"):
        lines.append(f"*Грамматика:*\n_{lesson['grammar']}_\n")
    if lesson.get("examples"):
        lines.append("*Примеры:*")
        for ex in lesson["examples"]:
            lines.append(f"• {ex}")
        lines.append("")
    lines.append("_Ответь на вопросы ниже:_")
    return "\n".join(lines)
