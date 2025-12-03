import os
import sys
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# ===========================
#   FIX PYTHON PATH
# ===========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYZER_DIR = os.path.join(BASE_DIR, "analyzer")

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

if ANALYZER_DIR not in sys.path:
    sys.path.append(ANALYZER_DIR)

# ===========================
#   IMPORT MODULES
# ===========================
from analyzer.face_detector import detect_face_info
from analyzer.emotion_model import interpret_emotions
from analyzer.stress_model import detect_microstress
from analyzer.personality_model import build_personality_profile
from analyzer.professional_profile import build_professional_profile
from analyzer.report_builder import build_full_report

from database import init_db, save_report, get_user_reports

# ===========================
#   BOT TOKEN
# ===========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing! Add it in Railway → Variables.")

ADMIN_IDS = [270799202]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

init_db()


# ===========================
#      START COMMAND
# ===========================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 Надішли фото — я створю психологічний портрет.\n"
        "• Історія аналізів\n"
        "• Порівняння стану: /compare\n"
        "• HR-звіт: /summary <user_id>"
    )


# ===========================
#     PHOTO HANDLER
# ===========================
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    await message.answer("⏳ Аналізую фото…")

    user_id = message.from_user.id
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)

    os.makedirs("photos", exist_ok=True)
    img_path = f"photos/{user_id}_{file_id}.jpg"
    await bot.download_file(file.file_path, img_path)

    # Face analysis
    face_info = detect_face_info(img_path)
    if face_info is None:
        return await message.answer("⚠️ Обличчя не розпізнано.")

    # Emotion
    emotion_data = interpret_emotions(face_info["emotion"])

    # Microstress
    stress_data = detect_microstress(img_path)

    # Personality
    personality = build_personality_profile(face_info, emotion_data, stress_data)

    # Professional profile
    professional = build_professional_profile(personality)

    # Report
    full_report = build_full_report(
        face_info, emotion_data, stress_data, personality, professional
    )

    # Save to DB
    save_report(
        user_id, img_path, face_info, emotion_data,
        stress_data, personality, professional, full_report
    )

    # Send parts
    chunk = 3500
    for i in range(0, len(full_report), chunk):
        await message.answer(full_report[i:i+chunk])

    await message.answer("💾 Звіт збережено. /compare — порівняти стан.")


# ===========================
#      COMPARE REPORTS
# ===========================
@dp.message(Command("compare"))
async def compare(message: types.Message):
    user_id = message.from_user.id
    reports = get_user_reports(user_id)

    if len(reports) < 2:
        return await message.answer("Потрібно 2 фото.")

    import json
    latest = reports[0]
    prev = reports[1]

    emo1 = json.loads(latest[4])
    stress1 = json.loads(latest[5])

    emo2 = json.loads(prev[4])
    stress2 = json.loads(prev[5])

    result = f"""
📊 **Порівняння**

1️⃣ Останнє:
• Емоція: {emo1['dominant_emotion']}
• Валентність: {emo1['valence']}
• Стрес: {stress1['microstress_level']}

2️⃣ Попереднє:
• Емоція: {emo2['dominant_emotion']}
• Валентність: {emo2['valence']}
• Стрес: {stress2['microstress_level']}

🔥 **Динаміка:**
• Емоційність: {'покращилась' if emo1['valence'] > emo2['valence'] else 'погіршилась'}
• Стрес: {'зріс' if stress1['microstress_level'] > stress2['microstress_level'] else 'знизився'}
"""

    await message.answer(result)


# ===========================
#      ADMIN SUMMARY
# ===========================
@dp.message(Command("summary"))
async def admin_summary(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("⛔ Немає доступу.")

    parts = message.text.split()
    if len(parts) != 2:
        return await message.answer("Формат: /summary user_id")

    target = int(parts[1])
    reports = get_user_reports(target)

    if not reports:
        return await message.answer("Немає даних.")

    import json
    data = json.loads(reports[0][6])
    professional = json.loads(reports[0][7])

    summary = f"""
👤 HR Summary для {target}

Психотип:
• {data['radical']}

Big Five:
• Openness: {data['big_five_scores']['openness']}
• Conscientiousness: {data['big_five_scores']['conscientiousness']}
• Extraversion: {data['big_five_scores']['extraversion']}
• Agreeableness: {data['big_five_scores']['agreeableness']}
• Neuroticism: {data['big_five_scores']['neuroticism']}

Рекомендації:
• {professional['recommended_roles'][0]}
"""

    await message.answer(summary)


# ===========================
#      RUN BOT
# ===========================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())