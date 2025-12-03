import os
import sys
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# ======================================================
#              FIX PYTHON PATH (Railway)
# ======================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYZER_DIR = os.path.join(BASE_DIR, "analyzer")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if ANALYZER_DIR not in sys.path:
    sys.path.insert(0, ANALYZER_DIR)

print("=== DEBUG PATH ===")
print("BASE_DIR:", BASE_DIR)
print("sys.path:", sys.path)
print("Analyzer exists:", os.path.exists(ANALYZER_DIR))
print("Analyzer content:", os.listdir(ANALYZER_DIR) if os.path.exists(ANALYZER_DIR) else "NONE")
print("==================")

# ======================================================
#                 IMPORT LOCAL MODULES
# ======================================================

from analyzer.face_detector import detect_face_info
from analyzer.emotion_model import interpret_emotions
from analyzer.stress_model import detect_microstress
from analyzer.personality_model import build_personality_profile
from analyzer.professional_profile import build_professional_profile
from analyzer.report_builder import build_full_report
from analyzer.physiognomy_model import build_physiognomy_profile   # 🔹 нове
from analyzer.radicals import RADICALS                             # 🔹 нове

from database import init_db, save_report, get_user_reports

# ======================================================
#                  BOT TOKEN
# ======================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")    # ← Railway Variables

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN is missing! Add it in Railway → Variables.")

ADMIN_IDS = [270799202]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

init_db()

# ======================================================
#                    START
# ======================================================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 Надішли фото — я створю розширений психологічний портрет.\n\n"
        "🧠 В основі:\n"
        "• емоційний аналіз\n"
        "• мікрострес\n"
        "• Big Five + радикали (Пономаренко)\n"
        "• фізіогномічний профіль (форма обличчя, риси, пропорції)\n\n"
        "Команди:\n"
        "• /compare — порівняння останніх двох станів\n"
        "• /summary <user_id> — HR-звіт за останнім аналізом"
    )


# ======================================================
#               PHOTO HANDLER
# ======================================================
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    await message.answer("⏳ Аналізую фото… це може зайняти кілька секунд.")

    user_id = message.from_user.id
    file_id = message.photo[-1].file_id

    file = await bot.get_file(file_id)

    os.makedirs("photos", exist_ok=True)
    img_path = f"photos/{user_id}_{file_id}.jpg"

    await bot.download_file(file.file_path, img_path)

    # --- 1. FACE (DeepFace / RetinaFace) ---
    face_info = detect_face_info(img_path)
    if face_info is None:
        return await message.answer("⚠️ Не вдалося розпізнати обличчя. Спробуй інше фото (прямий ракурс, хороше світло).")

    # --- 2. EMOTION ---
    emotion_data = interpret_emotions(face_info["emotion"])

    # --- 3. STRESS (мікроміміка / напруга) ---
    stress_data = detect_microstress(img_path)

    # --- 4. PERSONALITY (Big Five + радикал Пономаренка) ---
    personality = build_personality_profile(face_info, emotion_data, stress_data)

    # --- 5. PHYSIOGNOMY (НАУКОВИЙ ПІДХІД ДО РИС ОБЛИЧЧЯ) ---
    # очікується, що build_physiognomy_profile повертає щось типу:
    # {
    #   "face_shape": "...",
    #   "dominant_features": [...],
    #   "physiog_profile_text": "довгий опис...",
    #   "scientific_notes": "що є евристикою, а що — обережні висновки"
    # }
    physiognomy = build_physiognomy_profile(face_info)

    # --- 6. PROFESSIONAL PROFILE ---
    professional = build_professional_profile(personality)

    # --- 7. FULL REPORT (всередині підшивається радикал + фізіогноміка) ---
    # ВАЖЛИВО: у report_builder.build_full_report має бути оновлена сигнатура:
    # def build_full_report(face_info, emotion_data, stress_data, personality, professional, physiognomy):
    full_report = build_full_report(
        face_info,
        emotion_data,
        stress_data,
        personality,
        professional,
        physiognomy
    )

    # --- 8. SAVE TO DB ---
    save_report(
        user_id,
        img_path,
        face_info,
        emotion_data,
        stress_data,
        personality,
        professional,
        full_report
    )

    # --- 9. SEND CHUNKS ---
    chunk = 3500
    for i in range(0, len(full_report), chunk):
        await message.answer(full_report[i:i + chunk])

    # Коротке резюме по радикалу + фізіогноміці
    radical_code = personality.get("radical_code") or personality.get("radical_key")
    radical_info = RADICALS.get(radical_code) if radical_code else None

    short_block = ""

    if radical_info:
        short_block += f"🧩 Радикал: *{radical_info['name']}*\n" \
                       f"Коротко: {radical_info['short']}\n\n"

    if physiognomy and isinstance(physiognomy, dict):
        phys_short = physiognomy.get("short_summary") or physiognomy.get("physiog_profile_text", "")[:400]
        if phys_short:
            short_block += f"👁 Фізіогномічний профіль (коротко):\n{phys_short}\n\n"

    if short_block:
        await message.answer(short_block, parse_mode="Markdown")

    await message.answer("💾 Звіт збережено. Використай /compare, щоб відстежити динаміку.")


# ======================================================
#                   COMPARE
# ======================================================
@dp.message(Command("compare"))
async def compare(message: types.Message):
    reports = get_user_reports(message.from_user.id)

    if len(reports) < 2:
        return await message.answer("Потрібні мінімум 2 фото для порівняння стану.")

    import json

    last = reports[0]
    prev = reports[1]

    emo1 = json.loads(last[4])
    stress1 = json.loads(last[5])

    emo2 = json.loads(prev[4])
    stress2 = json.loads(prev[5])

    result = f"""
📊 **Порівняння двох аналізів**

1️⃣ Останнє:
• Емоція: {emo1['dominant_emotion']}
• Валентність: {emo1['valence']}
• Стрес: {stress1['microstress_level']}

2️⃣ Попереднє:
• Емоція: {emo2['dominant_emotion']}
• Валентність: {emo2['valence']}
• Стрес: {stress2['microstress_level']}

🔥 Динаміка:
• Емоційність: {'покращилась' if emo1['valence'] > emo2['valence'] else 'погіршилась або стабільна'}
• Стрес: {'зріс' if stress1['microstress_level'] > stress2['microstress_level'] else 'знизився або стабільний'}
"""

    await message.answer(result)


# ======================================================
#           ADMIN SUMMARY (з радикалом + описом)
# ======================================================
@dp.message(Command("summary"))
async def admin_summary(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("⛔ Доступ заборонений.")

    parts = message.text.split()
    if len(parts) != 2:
        return await message.answer("Формат: /summary user_id")

    target = int(parts[1])
    reports = get_user_reports(target)

    if not reports:
        return await message.answer("У користувача немає історії.")

    import json
    personality = json.loads(reports[0][6])
    professional = json.loads(reports[0][7])

    radical_code = personality.get("radical_code") or personality.get("radical_key")
    radical_info = RADICALS.get(radical_code) if radical_code else None

    radical_block = ""
    if radical_info:
        radical_block = (
            f"\nПровідний радикал:\n"
            f"• {radical_info['name']}\n"
            f"• Коротко: {radical_info['short']}\n\n"
            f"Детальний опис:\n{radical_info['description']}\n"
        )
    else:
        radical_block = f"\nПсихотип (текст):\n• {personality.get('radical', '—')}\n"

    summary = f"""
👤 **HR Summary для {target}**

{radical_block}

Big Five:
• Openness: {personality['big_five_scores']['openness']}
• Conscientiousness: {personality['big_five_scores']['conscientiousness']}
• Extraversion: {personality['big_five_scores']['extraversion']}
• Agreeableness: {personality['big_five_scores']['agreeableness']}
• Neuroticism: {personality['big_five_scores']['neuroticism']}

Рекомендовані ролі:
• {professional['recommended_roles'][0]}
"""

    await message.answer(summary)


# ======================================================
#                     RUN BOT
# ======================================================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())