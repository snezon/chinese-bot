#!/usr/bin/env python3
"""Generate HSK1 and HSK2 final test JSON files."""
import json
from pathlib import Path

OUT = Path(__file__).parent / "lessons"

test_hsk1 = {
  "level": "hsk1",
  "title": "Финальный тест HSK 1",
  "pass_threshold": 0.6,
  "questions": [
    {"type":"multiple_choice","question":"Что значит 谢谢?","options":["Спасибо","Привет","Пока","Извините"],"answer":0},
    {"type":"multiple_choice","question":"Как сказать «До свидания»?","options":["再见","你好","谢谢","请"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 七?","options":["семь","шесть","восемь","девять"],"answer":0},
    {"type":"multiple_choice","question":"Как сказать «два человека» перед счётным словом?","options":["两个人","二个人","三个人","四个人"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 她?","options":["она","он","я","ты"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 妈妈?","options":["мама","папа","сестра","тётя"],"answer":0},
    {"type":"multiple_choice","question":"Как спросить «что это»?","options":["这是什么？","这是谁？","这在哪儿？","这怎么样？"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 有?","options":["иметь/есть","быть","хотеть","мочь"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 喝?","options":["пить","есть","готовить","покупать"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 书?","options":["книга","стол","стул","ручка"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 家?","options":["дом/семья","школа","больница","магазин"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 来?","options":["приходить","уходить","возвращаться","сидеть"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 现在?","options":["сейчас","потом","вчера","завтра"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 今天?","options":["сегодня","завтра","вчера","на прошлой неделе"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 天气?","options":["погода","небо","воздух","облако"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 高兴?","options":["радостный","грустный","злой","усталый"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 听?","options":["слушать","говорить","смотреть","читать"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 老师?","options":["учитель","студент","врач","друг"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 喜欢?","options":["нравиться","ненавидеть","бояться","забывать"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 上?","options":["вверху/на","внизу/под","впереди","сзади"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 钱?","options":["деньги","цена","монета","банк"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 打电话?","options":["звонить по телефону","писать письмо","отправлять смс","смотреть ТВ"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 住?","options":["жить/проживать","работать","учиться","стоять"],"answer":0},
    {"type":"multiple_choice","question":"Для чего используется 吗?","options":["Вопрос да/нет","Завершение","Притяжательность","Соединение"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 睡觉?","options":["спать","вставать","есть","отдыхать"],"answer":0},
    {"type":"multiple_choice","question":"Как сказать «я не студент»?","options":["我不是学生","我没是学生","学生不我","我是不学生"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 水果?","options":["фрукты","овощи","еда","напиток"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 中午?","options":["полдень","утро","вечер","ночь"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 知道?","options":["знать факт","знать лично","понимать","учить"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 可以?","options":["можно/разрешено","нельзя","должен","хочу"],"answer":0}
  ]
}

test_hsk2 = {
  "level": "hsk2",
  "title": "Финальный тест HSK 2",
  "pass_threshold": 0.6,
  "questions": [
    {"type":"multiple_choice","question":"Что значит 旁边?","options":["рядом/сбоку","напротив","позади","далеко"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 已经?","options":["уже","ещё","снова","иногда"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 觉得?","options":["чувствовать/считать","знать","видеть","слышать"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 告诉?","options":["рассказать/сообщить","спросить","ответить","понять"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 开始?","options":["начинать","заканчивать","продолжать","останавливать"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 最?","options":["самый/наиболее","более","очень","слишком"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 弟弟?","options":["младший брат","старший брат","муж","сын"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 聪明?","options":["умный","красивый","серьёзный","усердный"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 游泳?","options":["плавать","бегать","прыгать","танцевать"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 旅游?","options":["путешествовать","работать","учиться","отдыхать"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 好吃?","options":["вкусный","невкусный","острый","сладкий"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 生病?","options":["заболеть","выздороветь","устать","отдыхать"],"answer":0},
    {"type":"multiple_choice","question":"Как сказать «идёт снег»?","options":["下雪","下雨","刮风","晴天"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 便宜?","options":["дешёвый","дорогой","бесплатный","качественный"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 作业?","options":["домашнее задание","работа","урок","экзамен"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 如果?","options":["если","потому что","поэтому","хотя"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 上网?","options":["выходить в интернет","звонить","писать","смотреть ТВ"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 公司?","options":["компания","магазин","завод","офис"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 把 в предложении?","options":["Акцент на объекте действия","Пассивный залог","Длящееся состояние","Прошлый опыт"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 生日?","options":["день рождения","праздник","годовщина","именины"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 小时?","options":["час (продолжительность)","минута","секунда","день"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 您?","options":["Вы (вежливое)","Ты","Он","Они"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 应该?","options":["следует/должен","можно","возможно","обязательно"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 找?","options":["искать","находить","терять","брать"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 其实?","options":["на самом деле","конечно","обязательно","наверное"],"answer":0},
    {"type":"multiple_choice","question":"Что означает 过 после глагола?","options":["Прошлый опыт","Завершение","Длящееся состояние","Будущее"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 非常?","options":["чрезвычайно/очень","обычно","немного","иногда"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 需要?","options":["нуждаться/нужно","хотеть","любить","уметь"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 马上?","options":["немедленно","медленно","потом","вчера"],"answer":0},
    {"type":"multiple_choice","question":"Что значит 一直?","options":["постоянно/всё время","иногда","редко","обычно"],"answer":0}
  ]
}

for test in [test_hsk1, test_hsk2]:
    path = OUT / f"test_{test['level']}.json"
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(test, f, ensure_ascii=False, indent=2)
    print(f"Written: {path} ({len(test['questions'])} questions)")

print("Done.")
