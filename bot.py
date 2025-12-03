import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

from analyzer.face_detector import detect_face_info
from analyzer.emotion_model import interpret_emotions
from analyzer.stress_model import detect_microstress
from analyzer.personality_model import build_personality_profile
from analyzer.professional_profile import build_professional_profile
from analyzer.report_builder import build_full_report

from database import init_db, save_report, get_user_reports

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
ADMIN_IDS = [123456789]  # сюди встав свій Telegram ID

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

init_db()


# ================================
#           START
# ================================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 Надішли фото обличчя — я сформую **розширений психологічний портрет**.\n\n"
        "📌 Доступні функції:\n"
        "• збереження історії аналізів\n"
        "• порівняння стану за фото: /compare\n"
        "• адмін-звіт HR: /summary <user_id>"
    )


# ================================
#         ОБРОБКА ФОТО
# ================================
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    await message.answer("⏳ Аналізую фото…")

    user_id = message.from_user.id
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)

    os.makedirs("photos", exist_ok=True)
    img_path = f"photos/{user_id}_{file_id}.jpg"
    await bot.download_file(file.file_path, img_path)

    # 1. Аналіз обличчя
    face_info = detect_face_info(img_path)
    if face_info is None:
        return await message.answer("⚠️ Не вдалося розпізнати обличчя.")

    # 2. Емоції
    emotion_data = interpret_emotions(face_info["emotion"])

    # 3. Стрес
    stress_data = detect_microstress(img_path)

    # 4. Особистість (Big Five + Радикал + Опис радикала)
    personality = build_personality_profile(face_info, emotion_data, stress_data)

    # 5. Професійні рекомендації
    professional = build_professional_profile(personality)

    # 6. Повний текстовий психологічний портрет
    full_report = build_full_report(
        face_info, emotion_data, stress_data,
        personality, professional
    )

    # 7. Зберігаємо в SQLite
    save_report(
        user_id, img_path, face_info,
        emotion_data, stress_data,
        personality, professional,
        full_report
    )

    # 8. Відправляємо текст по частинах (Telegram ліміт)
    chunk = 3500
    for i in range(0, len(full_report), chunk):
        await message.answer(full_report[i:i+chunk])

    await message.answer("💾 Звіт додано в історію.\nПерегляд та порівняння: /compare")


# ================================
#        ПОРІВНЯННЯ ФОТО
# ================================
@dp.message(Command("compare"))
async def compare(message: types.Message):
    user_id = message.from_user.id
    reports = get_user_reports(user_id)

    if len(reports) < 2:
        return await message.answer("Потрібно мінімум 2 фото для порівняння.")

    latest = reports[0]
    previous = reports[1]

    import json
    face1 = json.loads(latest[3])
    emo1 = json.loads(latest[4])
    stress1 = json.loads(latest[5])

    face2 = json.loads(previous[3])
    emo2 = json.loads(previous[4])
    stress2 = json.loads(previous[5])

    comparison = f"""
📊 **Порівняння двох останніх аналізів**

1️⃣ **Останнє фото**
- Емоція: {emo1['dominant_emotion']}
- Валентність: {emo1['valence']}
- Стрес: {stress1['microstress_level']}

2️⃣ **Попереднє фото**
- Емоція: {emo2['dominant_emotion']}
- Валентність: {emo2['valence']}
- Стрес: {stress2['microstress_level']}

---

### 🔄 Динаміка змін:

🧠 **Емоційність:**  
- {'Стан став більш позитивним' if emo1['valence'] > emo2['valence'] else 'Стан став менш позитивним'}

💥 **Стрес:**  
- {'Рівень стресу зріс' if stress1['microstress_level'] > stress2['microstress_level'] else 'Стрес знизився або стабілізувався'}

🙂 **Домінантна емоція змінилась:**  
з *{emo2['dominant_emotion']}* → *{emo1['dominant_emotion']}*
"""

    await message.answer(comparison)


# ================================
#              АДМІН
# ================================
@dp.message(Command("summary"))
async def admin_summary(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("⛔ Доступ заборонений.")

    parts = message.text.split()
    if len(parts) != 2:
        return await message.answer("Формат: /summary user_id")

    target_user = int(parts[1])
    reports = get_user_reports(target_user)

    if not reports:
        return await message.answer("У користувача немає збережених аналізів.")

    import json
    last = reports[0]
    personality = json.loads(last[6])
    professional = json.loads(last[7])

    summary = f"""
👤 **HR Summary для користувача {target_user}**

### Психотип (радикал):
- {personality['radical']}

### Ключові риси Big Five:
- Відкритість: {personality['big_five_scores']['openness']}
- Сумлінність: {personality['big_five_scores']['conscientiousness']}
- Екстраверсія: {personality['big_five_scores']['extraversion']}
- Доброжичливість: {personality['big_five_scores']['agreeableness']}
- Нейротизм: {personality['big_five_scores']['neuroticism']}

### Рекомендовані ролі:
- {professional['recommended_roles'][0]}

### Основні ризики:
- {professional['risks'][0]}

### Рекомендований стиль взаємодії:
- {professional['communication_style'][0]}
"""

    await message.answer(summary)


# ================================
#              RUN
# ================================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())