import io
import os
import re
import random
import tempfile
import logging
from openai import AsyncOpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters,
)
import db
import lesson_engine

_openai = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

# flat dict: hanzi → (pinyin, ru) for all HSK1+2 words — built once at startup
_all_words: dict = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── mascot phrases ────────────────────────────────────────────────────────────

_CORRECT = [
    "✅ Точно! Ты в ударе сегодня 🔥",
    "✅ Да, правильно! 对了～",
    "✅ Ес! Так держать 💪",
    "✅ Мико доволен 😏 Всё верно!",
    "✅ Огонь! Запомни это слово навсегда 🧠",
]

_WRONG = [
    "❌ Мимо. Правильно: *{correct}* — запомни!",
    "❌ Не то, но не беда. Правильно: *{correct}*",
    "❌ Чуть-чуть не дошло. *{correct}* — вот что нужно было!",
    "❌ Ошибочка. Держи правильный: *{correct}*",
]

_LISTEN_CORRECT = [
    "✅ Слух — огонь! Это *{hanzi}* `{pinyin}` — {ru}",
    "✅ Поймала! *{hanzi}* `{pinyin}` — {ru} 🎧",
    "✅ Супер-уши! *{hanzi}* `{pinyin}` — {ru}",
]

_LISTEN_WRONG = [
    "❌ Это было *{hanzi}* `{pinyin}` — {ru}. Слушай внимательнее в следующий раз 👂",
    "❌ Нет, это *{hanzi}* `{pinyin}` — {ru}. Ничего, потренируемся!",
]


# ── word index ───────────────────────────────────────────────────────────────

def _build_word_index():
    global _all_words
    for meta in lesson_engine.get_all_lesson_meta():
        try:
            lesson = lesson_engine.load_lesson(meta["id"])
        except Exception:
            continue
        for w in lesson.get("words", []):
            hanzi = w.get("hanzi", "").strip()
            if hanzi:
                _all_words[hanzi] = (w.get("pinyin", ""), w.get("ru", ""))


# ── TTS & listening helpers ───────────────────────────────────────────────────

async def _tts(text: str) -> bytes:
    import edge_tts
    communicate = edge_tts.Communicate(text, voice="zh-CN-XiaoxiaoNeural")
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    buf.seek(0)
    return buf.read()


def _generate_listening_questions(lesson: dict, count: int = 2) -> list:
    words = lesson.get("words", [])
    if len(words) < 2:
        return []
    all_ru = list({ru for _, (_, ru) in _all_words.items()})
    test_words = random.sample(words, min(count, len(words)))
    questions = []
    for word in test_words:
        correct = word["ru"]
        pool = [r for r in all_ru if r != correct]
        distractors = random.sample(pool, min(3, len(pool)))
        options = distractors + [correct]
        random.shuffle(options)
        questions.append({
            "hanzi": word["hanzi"],
            "pinyin": word["pinyin"],
            "ru": correct,
            "options": options,
            "correct_idx": options.index(correct),
        })
    return questions


async def _send_listening_question(msg, context: ContextTypes.DEFAULT_TYPE):
    questions = context.user_data.get("listen_questions", [])
    idx = context.user_data.get("listen_idx", 0)
    total = len(questions)
    if idx >= total:
        return
    q = questions[idx]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(opt, callback_data=f"lans_{i}")]
        for i, opt in enumerate(q["options"])
    ])
    caption = f"🎧 *Слушание {idx + 1}/{total}:* что ты услышала?"
    try:
        audio = await _tts(q["hanzi"])
        await msg.reply_voice(
            voice=io.BytesIO(audio),
            caption=caption,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error("TTS error: %s", e)
        await msg.reply_text(
            f"{caption}\n\n_{q['hanzi']}_",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


async def _send_pronunciation_prompt(msg, context: ContextTypes.DEFAULT_TYPE):
    lesson = context.user_data.get("lesson")
    if not lesson or not lesson.get("words"):
        context.user_data["phase"] = "exercises"
        await _send_exercise(msg, context)
        return
    word = lesson["words"][0]
    context.user_data["pron_word"] = word
    context.user_data["phase"] = "pronunciation"
    skip_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("Пропустить →", callback_data="skip_pron")
    ]])
    caption = (
        f"🗣 *Мiko слушает!*\n\n"
        f"Повтори за мной: *{word['hanzi']}* `{word['pinyin']}` — {word['ru']}\n\n"
        f"Отправь голосовое 🎤 или нажми «Пропустить»"
    )
    try:
        audio = await _tts(word["hanzi"])
        await msg.reply_voice(
            voice=io.BytesIO(audio),
            caption=caption,
            parse_mode="Markdown",
            reply_markup=skip_kb,
        )
    except Exception as e:
        logger.error("TTS error: %s", e)
        await msg.reply_text(caption, parse_mode="Markdown", reply_markup=skip_kb)


async def _handle_pronunciation_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pron_word = context.user_data["pron_word"]
    status = await update.message.reply_text("🎤 Слушаю...")
    voice = update.message.voice or update.message.audio
    tg_file = await voice.get_file()
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        await tg_file.download_to_drive(tmp.name)
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as af:
            transcript = await _openai.audio.transcriptions.create(
                model="whisper-1", file=af, language="zh", response_format="text",
            )
        recognized = transcript.strip()
    except Exception as e:
        logger.error("Whisper error: %s", e)
        await status.edit_text("❌ Не удалось распознать. Попробуй ещё раз или нажми «Пропустить».")
        return
    finally:
        os.unlink(tmp_path)
    hanzi = pron_word["hanzi"]
    pinyin = pron_word["pinyin"]
    if hanzi in recognized or recognized in hanzi:
        await status.edit_text(
            f"🔥 Мiko услышал: *{recognized}*\n"
            f"*{hanzi}* `{pinyin}` — произношение зачтено!",
            parse_mode="Markdown",
        )
        context.user_data["phase"] = "exercises"
        await _send_exercise(update.message, context)
    else:
        await status.edit_text(
            f"🎤 Слышу: *{recognized}*\n"
            f"Ожидалось: *{hanzi}* `{pinyin}` — попробуй ещё раз или пропусти 👇",
            parse_mode="Markdown",
        )


# ── keyboard helpers ─────────────────────────────────────────────────────────

def _make_exercise_keyboard(options: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(opt, callback_data=f"ans_{i}")]
         for i, opt in enumerate(options)]
    )

def _make_test_keyboard(options: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(opt, callback_data=f"tans_{i}")]
         for i, opt in enumerate(options)]
    )


# ── commands ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "你好！ Я *Мико* — твой гид по китайскому 学\n\n"
        "Буду учить тебя как друг: без скуки, с иероглифами, "
        "аудио и мнемониками. 50 уроков — весь HSK 1 и HSK 2 (~300 слов).\n\n"
        "*Что умею:*\n"
        "/lesson1 — начать урок 1\n"
        "/lessons — все уроки\n"
        "/progress — твой прогресс\n"
        "/testhsk1 / /testhsk2 — финальные тесты\n"
        "/repeat1 — повторить урок\n\n"
        "Погнали? 👉 /lesson1",
        parse_mode="Markdown",
    )


async def cmd_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_meta = lesson_engine.get_all_lesson_meta()
    progress = db.get_all_progress()
    completed_ids = {p["lesson_id"] for p in progress if p["completed"]}

    lines = ["*Уроки HSK 1:*"]
    for m in all_meta:
        if m["id"] == 26:
            lines.append("\n*Уроки HSK 2:*")
        icon = "✅" if m["id"] in completed_ids else "📖"
        lines.append(f"{icon} /lesson{m['id']} — {m['title']}")

    hsk1_done = db.get_test_result("hsk1")
    hsk2_done = db.get_test_result("hsk2")
    lines.append(
        f"\n*Тесты:*\n"
        f"{'✅' if hsk1_done['passed'] else '🔒'} /testhsk1 — Финальный тест HSK 1\n"
        f"{'✅' if hsk2_done['passed'] else '🔒'} /testhsk2 — Финальный тест HSK 2"
    )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    progress = db.get_all_progress()
    completed = sum(1 for p in progress if p["completed"])
    hsk1_count = sum(1 for p in progress if p["completed"] and p["lesson_id"] <= 25)
    hsk2_count = sum(1 for p in progress if p["completed"] and p["lesson_id"] > 25)
    hsk1_test = db.get_test_result("hsk1")
    hsk2_test = db.get_test_result("hsk2")

    bars = "█" * completed + "░" * (50 - completed)
    msg = (
        f"*Твой прогресс*\n\n"
        f"`{bars}`\n"
        f"{completed}/50 уроков завершено\n\n"
        f"*HSK 1:* {hsk1_count}/25 уроков\n"
        f"*HSK 2:* {hsk2_count}/25 уроков\n\n"
        f"*Тест HSK 1:* {'✅ Сдан' if hsk1_test['passed'] else '❌ Не сдан'}"
        f" (лучший: {int(hsk1_test['best_score'] * 100)}%)\n"
        f"*Тест HSK 2:* {'✅ Сдан' if hsk2_test['passed'] else '❌ Не сдан'}"
        f" (лучший: {int(hsk2_test['best_score'] * 100)}%)"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


# ── lesson start ──────────────────────────────────────────────────────────────

async def _start_lesson(msg, context: ContextTypes.DEFAULT_TYPE, lesson_id: int, check_unlock: bool = True):
    if check_unlock:
        progress = db.get_all_progress()
        if not lesson_engine.is_lesson_unlocked(lesson_id, progress):
            await msg.reply_text(
                f"🔒 Сначала пройди урок {lesson_id - 1}. /lesson{lesson_id - 1}"
            )
            return
    try:
        lesson = lesson_engine.load_lesson(lesson_id)
    except FileNotFoundError:
        await msg.reply_text("Урок не найден.")
        return
    theory = lesson_engine.format_lesson_theory(lesson)
    await msg.reply_text(theory, parse_mode="Markdown")
    context.user_data["lesson"] = lesson
    context.user_data["ex_idx"] = 0
    context.user_data["ex_score"] = 0

    listen_qs = _generate_listening_questions(lesson)
    if listen_qs:
        context.user_data["phase"] = "listening"
        context.user_data["listen_idx"] = 0
        context.user_data["listen_score"] = 0
        context.user_data["listen_questions"] = listen_qs
        await _send_listening_question(msg, context)
    else:
        await _send_pronunciation_prompt(msg, context)


async def _start_test(msg, context: ContextTypes.DEFAULT_TYPE, level: str):
    try:
        test = lesson_engine.load_test(level)
    except FileNotFoundError:
        await msg.reply_text("Тест не найден.")
        return
    context.user_data["test"] = test
    context.user_data["test_idx"] = 0
    context.user_data["test_score"] = 0
    await msg.reply_text(
        f"📝 *{test['title']}*\n\n"
        f"{len(test['questions'])} вопросов, порог {int(test['pass_threshold'] * 100)}%.\n\n"
        f"Мiko смотрит — не подведи! 😏",
        parse_mode="Markdown",
    )
    await _send_test_question(msg, context)


async def cmd_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        lesson_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Укажи номер урока: /lesson1")
        return
    await _start_lesson(update.message, context, lesson_id)


async def cmd_lesson_shortcut(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    m = re.match(r'^/(lesson|repeat)(\d+)', text, re.IGNORECASE)
    if not m:
        return
    lesson_id = int(m.group(2))
    context.args = [str(lesson_id)]
    await cmd_lesson(update, context)


async def cmd_test_shortcut(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    m = re.match(r'^/test(hsk[12])', text, re.IGNORECASE)
    if not m:
        return
    context.args = [m.group(1).lower()]
    await cmd_test(update, context)


async def cmd_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        lesson_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Укажи номер урока: /repeat1")
        return
    await _start_lesson(update.message, context, lesson_id, check_unlock=False)


async def cmd_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        level = context.args[0].lower()
        assert level in ("hsk1", "hsk2")
    except (IndexError, ValueError, AssertionError):
        await update.message.reply_text("Укажи уровень: /test hsk1 или /test hsk2")
        return
    await _start_test(update.message, context, level)


# ── lesson flow ───────────────────────────────────────────────────────────────

async def _send_exercise(msg, context: ContextTypes.DEFAULT_TYPE):
    lesson = context.user_data.get("lesson")
    if not lesson:
        return
    idx = context.user_data["ex_idx"]
    exercises = lesson["exercises"]
    if idx >= len(exercises):
        await _finish_lesson(msg, context)
        return
    ex = exercises[idx]
    total = len(exercises)
    await msg.reply_text(
        f"*Вопрос {idx + 1}/{total}:*\n{ex['question']}",
        parse_mode="Markdown",
        reply_markup=_make_exercise_keyboard(ex["options"]),
    )


async def handle_listening_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    questions = context.user_data.get("listen_questions")
    if not questions:
        await query.message.reply_text("⚠️ Сессия прервалась. Начни урок заново: /lesson1")
        return
    idx = context.user_data["listen_idx"]
    q = questions[idx]
    ans_idx = int(query.data.split("_")[1])
    if ans_idx == q["correct_idx"]:
        context.user_data["listen_score"] = context.user_data.get("listen_score", 0) + 1
        phrase = random.choice(_LISTEN_CORRECT).format(
            hanzi=q["hanzi"], pinyin=q["pinyin"], ru=q["ru"]
        )
        await query.message.reply_text(phrase, parse_mode="Markdown")
    else:
        phrase = random.choice(_LISTEN_WRONG).format(
            hanzi=q["hanzi"], pinyin=q["pinyin"], ru=q["ru"]
        )
        await query.message.reply_text(phrase, parse_mode="Markdown")
    context.user_data["listen_idx"] += 1
    if context.user_data["listen_idx"] >= len(questions):
        await _send_pronunciation_prompt(query.message, context)
    else:
        await _send_listening_question(query.message, context)


async def handle_exercise_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lesson = context.user_data.get("lesson")
    if not lesson:
        await query.message.reply_text(
            "⚠️ Сессия урока прервалась (бот перезапускался).\n"
            "Начни урок заново, например: /lesson1"
        )
        return
    ans_idx = int(query.data.split("_")[1])
    idx = context.user_data["ex_idx"]
    ex = lesson["exercises"][idx]
    if ans_idx == ex["answer"]:
        context.user_data["ex_score"] += 1
        await query.message.reply_text(random.choice(_CORRECT))
    else:
        correct = ex["options"][ex["answer"]]
        phrase = random.choice(_WRONG).format(correct=correct)
        await query.message.reply_text(phrase, parse_mode="Markdown")
    context.user_data["ex_idx"] += 1
    await _send_exercise(query.message, context)


async def _finish_lesson(msg, context: ContextTypes.DEFAULT_TYPE):
    lesson = context.user_data["lesson"]
    score = context.user_data["ex_score"]
    total = len(lesson["exercises"])
    pct = score / total
    lesson_id = lesson["id"]

    db.save_lesson_result(lesson_id, pct)
    passed = pct >= 0.5

    next_id = lesson_id + 1 if lesson_id < 50 else None
    keyboard = []
    if passed and next_id:
        keyboard.append([InlineKeyboardButton(
            f"Следующий урок {next_id} →",
            callback_data=f"next_{next_id}",
        )])
    keyboard.append([InlineKeyboardButton(
        "🔄 Повторить урок",
        callback_data=f"redo_{lesson_id}",
    )])

    if passed:
        result_text = (
            f"🔥 *Урок {lesson_id} пройден!*\n\n"
            f"Результат: {score}/{total} ({int(pct * 100)}%)\n\n"
            f"Мико кивает с одобрением 😏 Двигаемся дальше!"
        )
    else:
        result_text = (
            f"😤 *Урок {lesson_id} — почти!*\n\n"
            f"Результат: {score}/{total} ({int(pct * 100)}%)\n\n"
            f"Нужно ≥50% для зачёта. Мико говорит: не сдавайся, "
            f"повтори и попробуй снова 💪"
        )
    await msg.reply_text(
        result_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    context.user_data.pop("lesson", None)


# ── test flow ─────────────────────────────────────────────────────────────────

async def _send_test_question(msg, context: ContextTypes.DEFAULT_TYPE):
    test = context.user_data.get("test")
    if not test:
        return
    idx = context.user_data["test_idx"]
    questions = test["questions"]
    if idx >= len(questions):
        await _finish_test(msg, context)
        return
    q = questions[idx]
    total = len(questions)
    await msg.reply_text(
        f"*Вопрос {idx + 1}/{total}:*\n{q['question']}",
        parse_mode="Markdown",
        reply_markup=_make_test_keyboard(q["options"]),
    )


async def handle_test_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    test = context.user_data.get("test")
    if not test:
        await query.message.reply_text(
            "⚠️ Сессия теста прервалась (бот перезапускался).\n"
            "Начни тест заново: /test hsk1 или /test hsk2"
        )
        return
    ans_idx = int(query.data.split("_")[1])
    idx = context.user_data["test_idx"]
    q = test["questions"][idx]
    if ans_idx == q["answer"]:
        context.user_data["test_score"] += 1
        await query.message.reply_text("✅")
    else:
        correct = q["options"][q["answer"]]
        await query.message.reply_text(f"❌ *{correct}*", parse_mode="Markdown")
    context.user_data["test_idx"] += 1
    await _send_test_question(query.message, context)


async def _finish_test(msg, context: ContextTypes.DEFAULT_TYPE):
    test = context.user_data["test"]
    score = context.user_data["test_score"]
    total = len(test["questions"])
    pct = score / total
    level = test["level"]

    db.save_test_result(level, pct, test["pass_threshold"])
    passed = pct >= test["pass_threshold"]

    keyboard = [[InlineKeyboardButton("🔄 Пересдать", callback_data=f"retest_{level}")]]
    if passed:
        result = (
            f"🏆 *Тест сдан!*\n\n"
            f"Результат: {score}/{total} ({int(pct * 100)}%)\n\n"
            f"Мiko снимает шляпу 🫡 Ты реально молодец!"
        )
    else:
        result = (
            f"📚 *Тест не сдан*\n\n"
            f"Результат: {score}/{total} ({int(pct * 100)}%)\n\n"
            f"Нужно {int(test['pass_threshold'] * 100)}%. "
            f"Мiko говорит: повтори уроки и ты точно справишься 加油！"
        )
    await msg.reply_text(
        result,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    context.user_data.pop("test", None)


# ── navigation callbacks ──────────────────────────────────────────────────────

async def handle_nav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("next_"):
        lesson_id = int(data[5:])
        await _start_lesson(query.message, context, lesson_id)

    elif data.startswith("redo_"):
        lesson_id = int(data[5:])
        await _start_lesson(query.message, context, lesson_id, check_unlock=False)

    elif data.startswith("retest_"):
        level = data[7:]
        await _start_test(query.message, context, level)

    elif data == "skip_pron":
        context.user_data["phase"] = "exercises"
        await _send_exercise(query.message, context)


# ── voice / pronunciation ─────────────────────────────────────────────────────

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _openai.api_key:
        await update.message.reply_text("OPENAI_API_KEY не задан.")
        return

    # In-lesson pronunciation evaluation
    if context.user_data.get("phase") == "pronunciation" and context.user_data.get("pron_word"):
        await _handle_pronunciation_voice(update, context)
        return

    # Free-form practice outside lessons
    msg = await update.message.reply_text("🎤 Слушаю...")
    voice = update.message.voice or update.message.audio
    tg_file = await voice.get_file()
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        await tg_file.download_to_drive(tmp.name)
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as audio_f:
            transcript = await _openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_f,
                language="zh",
                response_format="text",
            )
        recognized = transcript.strip()
    except Exception as e:
        logger.error("Whisper error: %s", e)
        await msg.edit_text("❌ Не удалось распознать аудио. Попробуй ещё раз.")
        return
    finally:
        os.unlink(tmp_path)

    if not recognized:
        await msg.edit_text("🤔 Ничего не расслышал. Говори чётче и ближе к микрофону — Мiko ждёт!")
        return

    matched = []
    for hanzi, (pinyin, ru) in _all_words.items():
        if hanzi in recognized:
            matched.append((hanzi, pinyin, ru))

    if matched:
        lines = [f"🎤 Слышу: *{recognized}*\n"]
        for hanzi, pinyin, ru in matched:
            lines.append(f"✅ *{hanzi}* `{pinyin}` — {ru}")
        lines.append("\nКрутая практика! 加油！🔥")
        await msg.edit_text("\n".join(lines), parse_mode="Markdown")
    else:
        await msg.edit_text(
            f"🎤 Слышу: *{recognized}*\n\n"
            "🤔 Такого слова пока нет в наших уроках.\n"
            "Попробуй слово из текущего урока — Мiko оценит 😏",
            parse_mode="Markdown",
        )


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    db.init_db()
    _build_word_index()
    logger.info("Word index loaded: %d words", len(_all_words))

    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable not set")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("lessons", cmd_lessons))
    app.add_handler(CommandHandler("progress", cmd_progress))
    app.add_handler(CommandHandler("lesson", cmd_lesson))
    app.add_handler(CommandHandler("repeat", cmd_repeat))
    app.add_handler(CommandHandler("test", cmd_test))

    app.add_handler(MessageHandler(
        filters.COMMAND & filters.Regex(r'^/(lesson|repeat)\d+'),
        cmd_lesson_shortcut,
    ))
    app.add_handler(MessageHandler(
        filters.COMMAND & filters.Regex(r'^/test(hsk1|hsk2)'),
        cmd_test_shortcut,
    ))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(CallbackQueryHandler(handle_listening_answer, pattern=r"^lans_\d+$"))
    app.add_handler(CallbackQueryHandler(handle_exercise_answer, pattern=r"^ans_\d+$"))
    app.add_handler(CallbackQueryHandler(handle_test_answer, pattern=r"^tans_\d+$"))
    app.add_handler(CallbackQueryHandler(handle_nav, pattern=r"^(next_|redo_|retest_|skip_pron)"))

    logger.info("Bot started. Polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
