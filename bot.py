import os
import sys
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from analyzer.radical_test import QUESTIONS, RADICALS, build_keyboard, compute_result
# ======================================================
#              FIX PYTHON PATH (Railway FIX)
# ======================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYZER_DIR = os.path.join(BASE_DIR, "analyzer")

# додаємо кореневу папку проекту
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# додаємо папку analyzer
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
        "👋 Надішли фото — я створю психологічний портрет.\n\n"
        "🧠 Функції:\n"
        "• Збереження історії\n"
        "• /compare — порівняння стану\n"
        "• /summary <user_id> — HR-звіт"
    )


# ======================================================
#               PHOTO HANDLER
# ======================================================
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    await message.answer("⏳ Аналізую фото…")

    user_id = message.from_user.id
    file_id = message.photo[-1].file_id

    file = await bot.get_file(file_id)

    os.makedirs("photos", exist_ok=True)
    img_path = f"photos/{user_id}_{file_id}.jpg"

    await bot.download_file(file.file_path, img_path)

    # --- FACE ---
    face_info = detect_face_info(img_path)
    if face_info is None:
        return await message.answer("⚠️ Не вдалося розпізнати обличчя.")

    # --- EMOTION ---
    emotion_data = interpret_emotions(face_info["emotion"])

    # --- STRESS ---
    stress_data = detect_microstress(img_path)

    # --- PERSONALITY ---
    personality = build_personality_profile(face_info, emotion_data, stress_data)

    # --- PROFESSIONAL PROFILE ---
    professional = build_professional_profile(personality)

    # --- REPORT ---
    full_report = build_full_report(
        face_info, emotion_data, stress_data, personality, professional
    )

    # --- SAVE TO DB ---
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

    # --- SEND CHUNKS ---
    chunk = 3500
    for i in range(0, len(full_report), chunk):
        await message.answer(full_report[i:i + chunk])

    await message.answer("💾 Звіт збережено. /compare — порівняти зміни.")


# ======================================================
#                   COMPARE
# ======================================================
@dp.message(Command("compare"))
async def compare(message: types.Message):
    reports = get_user_reports(message.from_user.id)

    if len(reports) < 2:
        return await message.answer("Потрібні мінімум 2 фото.")

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
• Емоційність: {'покращилась' if emo1['valence'] > emo2['valence'] else 'погіршилась'}
• Стрес: {'зріс' if stress1['microstress_level'] > stress2['microstress_level'] else 'знизився'}
"""

    await message.answer(result)

@dp.message(Command("radical_test"))
async def start_radical_test(message: types.Message, state: FSMContext):
    await state.update_data(step=0, results=RADICALS.copy())
    q = QUESTIONS[0]
    await message.answer(q["text"], reply_markup=build_keyboard(q["options"], 0))
    
@dp.callback_query(F.data.startswith("rad_"))
async def process_radical_answer(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    step, results = data["step"], data["results"]

    _, qid, answer = callback.data.split("_", 2)
    qid = int(qid)

    effects = QUESTIONS[qid]["options"][answer]
    for r, val in effects.items():
        results[r] += val

    step += 1
    await state.update_data(step=step, results=results)

    if step >= len(QUESTIONS):
        await callback.message.answer(compute_result(results))
        await state.clear()
        return

    next_q = QUESTIONS[step]
    await callback.message.answer(next_q["text"], reply_markup=build_keyboard(next_q["options"], step))
# ======================================================
#                     ADMIN SUMMARY
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

    summary = f"""
👤 **HR Summary для {target}**

Психотип:
• {personality['radical']}

Big Five:
• Openness: {personality['big_five_scores']['openness']}
• Conscientiousness: {personality['big_five_scores']['conscientiousness']}
• Extraversion: {personality['big_five_scores']['extraversion']}
• Agreeableness: {personality['big_five_scores']['agreeableness']}
• Neuroticism: {personality['big_five_scores']['neuroticism']}

Рекомендації:
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