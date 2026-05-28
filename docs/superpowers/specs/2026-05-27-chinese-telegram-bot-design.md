# Chinese Learning Telegram Bot — Design Spec
*Date: 2026-05-27*

## Overview

A personal Telegram bot that teaches Chinese (Mandarin) from zero through structured lessons covering the full HSK 1 and HSK 2 vocabulary (300 words total). Content is fully static (pre-written JSON files). No AI API required.

---

## Tech Stack

- **Language:** Python 3.11+
- **Bot library:** python-telegram-bot 20+ (async)
- **Storage:** SQLite (user progress)
- **Content:** JSON lesson files
- **Runtime:** Polling mode (no webhook)
- **Deployment:** Any VPS or local Mac via systemd/launchd

---

## Project Structure

```
chinese-bot/
├── bot.py                  # entry point, Telegram handlers
├── lesson_engine.py        # load lessons, check answers, track progress
├── db.py                   # SQLite: progress, scores
├── lessons/
│   ├── hsk1/
│   │   ├── 01_greetings.json
│   │   ├── 02_numbers.json
│   │   └── ... (25 lessons)
│   ├── hsk2/
│   │   ├── 26_directions.json
│   │   └── ... (25 lessons)
│   ├── test_hsk1.json
│   └── test_hsk2.json
├── requirements.txt
└── README.md
```

---

## Lesson JSON Schema

```json
{
  "id": 1,
  "level": "hsk1",
  "title": "Приветствия",
  "words": [
    {
      "hanzi": "你好",
      "pinyin": "nǐ hǎo",
      "ru": "Привет",
      "mnemonic": "你 (ты) = человек 人 с палочкой сверху — кто-то стоит рядом с тобой",
      "etymology": "你 изначально изображало человека, 好 = женщина 女 + ребёнок 子 = счастье"
    }
  ],
  "grammar": "Краткое объяснение грамматики урока.",
  "examples": [
    "你好！— Привет!"
  ],
  "exercises": [
    {
      "type": "multiple_choice",
      "question": "Что значит 你好?",
      "options": ["Привет", "Пока", "Спасибо", "Да"],
      "answer": 0
    }
  ]
}
```

Exercise types:
- `multiple_choice` — 4 варианта, один правильный (inline-кнопки)

Только один тип упражнений намеренно — для статического бота текстовая проверка ненадёжна.

---

## Test JSON Schema

```json
{
  "level": "hsk1",
  "title": "Финальный тест HSK 1",
  "pass_threshold": 0.6,
  "questions": [
    {
      "type": "multiple_choice",
      "question": "Что значит 谢谢?",
      "options": ["Спасибо", "Привет", "Пока", "Да"],
      "answer": 0
    }
  ]
}
```

- 30 вопросов на тест
- Порог сдачи: 60% (18/30)
- Можно пересдавать неограниченно

---

## Bot Commands & Flow

| Команда | Действие |
|---------|----------|
| `/start` | Приветствие + главное меню |
| `/lessons` | Список всех уроков с прогрессом (✅/🔒) |
| `/lesson N` | Открыть урок N |
| `/test hsk1` | Финальный тест HSK 1 |
| `/test hsk2` | Финальный тест HSK 2 |
| `/progress` | Прогресс: X/50 уроков, тесты |
| `/repeat N` | Повторить урок N |

**Урок-флоу:**
1. Бот присылает теорию: слова с иероглифами + пиньинь + перевод
2. Для каждого слова — мнемоника + краткая этимология (откуда иероглиф)
3. Примеры предложений
4. Упражнения одно за другим (inline-кнопки для multiple_choice)
5. Результат: N/M правильных
6. Кнопки: «Следующий урок» / «Повторить»

**Прогрессия:** урок N+1 разблокируется после прохождения урока N с результатом ≥ 50%.

---

## Curriculum — HSK 1 (уроки 1–25)

| # | Тема | Слова |
|---|------|-------|
| 1 | Приветствия | 你好, 再见, 谢谢, 不客气, 对不起 |
| 2 | Числа 1–10 | 一二三四五六七八九十 |
| 3 | Числа 11–100 + 零 | 十一, 二十, 百... |
| 4 | Местоимения | 我,你,他,她,我们,你们,他们 |
| 5 | Семья | 爸爸,妈妈,哥哥,姐姐,弟弟,妹妹 |
| 6 | Вопросительные слова | 什么,哪,谁,怎么,为什么,几 |
| 7 | Глагол 是 и отрицание 不 | 是,不是,不,没有 |
| 8 | Еда и напитки | 吃,喝,饭,水,茶,咖啡,面条 |
| 9 | Фрукты и продукты | 苹果,鸡蛋,肉,菜,米饭 |
| 10 | Места | 学校,医院,商店,家,这里,那里 |
| 11 | Транспорт | 出租车,公共汽车,飞机,火车,骑 |
| 12 | Время: часы | 点,分,上午,下午,现在,时候 |
| 13 | Дни недели и месяцы | 星期,月,今天,明天,昨天 |
| 14 | Погода | 天气,下雨,下雪,热,冷,好 |
| 15 | Цвета | 红,白,黑,大,小 |
| 16 | Глаголы движения | 去,来,回,走,进,出 |
| 17 | Глаголы действия | 做,说,看,听,写,读 |
| 18 | Хотеть и нравиться | 想,要,喜欢,爱 |
| 19 | Деньги и покупки | 钱,买,卖,块,多少 |
| 20 | Работа и учёба | 工作,学习,学生,老师,医生 |
| 21 | Прилагательные 1 | 好,坏,多,少,高,矮,长,短 |
| 22 | Тело и здоровье | 身体,头,手,眼睛,生病,药 |
| 23 | Спорт и хобби | 踢足球,打篮球,游泳,跑步,上网 |
| 24 | Меры и счётные слова | 个,本,张,杯,瓶,斤 |
| 25 | Повторение HSK 1 | Микс всех тем |

---

## Curriculum — HSK 2 (уроки 26–50)

| # | Тема |
|---|------|
| 26–28 | Направления и локации (左,右,上,下,旁边,附近) |
| 29–31 | Время и частота (经常,有时候,已经,还,又,再) |
| 32–34 | Характер и чувства (高兴,难过,担心,生气,觉得) |
| 35–37 | Более сложные глаголы (帮助,开始,结束,告诉,知道) |
| 38–40 | Сравнения (比,一样,更,最,非常) |
| 41–43 | Профессии и работа (公司,同事,老板,经理,工资) |
| 44–46 | Путешествия (旅游,宾馆,护照,行李,地图) |
| 47–49 | Расширение грамматики (把,被,得,过,着) |
| 50 | Повторение HSK 2 |

---

## Database Schema

```sql
CREATE TABLE progress (
    lesson_id   INTEGER PRIMARY KEY,
    completed   INTEGER DEFAULT 0,  -- 1 = passed
    score       REAL,               -- 0.0–1.0
    attempts    INTEGER DEFAULT 0,
    updated_at  TEXT
);

CREATE TABLE test_results (
    level       TEXT PRIMARY KEY,   -- 'hsk1' | 'hsk2'
    passed      INTEGER DEFAULT 0,
    best_score  REAL,
    attempts    INTEGER DEFAULT 0,
    updated_at  TEXT
);
```

---

## Error Handling

- Неверный номер урока → «Урок не найден»
- Попытка открыть заблокированный урок → «Сначала пройди урок N»
- Текстовый ответ на multiple_choice вопрос → игнорировать, ждать нажатия кнопки
- Нет соединения с SQLite → crash с понятным сообщением (личный бот, не критично)

---

## Deployment

```bash
pip install python-telegram-bot
BOT_TOKEN=xxx python bot.py
```

Для постоянной работы — systemd unit или `screen`/`tmux` на VPS.
