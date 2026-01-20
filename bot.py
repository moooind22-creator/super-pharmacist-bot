from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)
import requests
from groq import Groq

# =========================
# TOKENS
# =========================
BOT_TOKEN = "PUT_YOUR_TELEGRAM_BOT_TOKEN_HERE"
GROQ_API_KEY = "PUT_YOUR_GROQ_API_KEY_HERE"

client = Groq(api_key=GROQ_API_KEY)

# =========================
# GROQ MODELS (FALLBACK)
# =========================
MODELS = [
    "llama-3.1-8b-instant",
    "llama-3-8b-instruct",
]

def groq_chat_with_fallback(prompt):
    for model in MODELS:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a clinical pharmacist."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Model failed: {model} | {e}")
            continue
    return None


# =========================
# SEARCH DRUG (DailyMed)
# =========================
def search_drug(drug_name):
    try:
        url = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json"
        params = {
            "drug_name": drug_name,
            "pagesize": 5
        }
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()
        if not data.get("data"):
            return None

        return data["data"][0]

    except Exception:
        return None


# =========================
# /start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً\n"
        "💊 Super Pharmacist Bot\n\n"
        "✍️ اكتب الاسم العلمي للدواء (بالإنجليزي)\n\n"
        "أمثلة:\n"
        "metformin\n"
        "omeprazole\n\n"
        "⚠️ المعلومات إرشادية فقط."
    )


# =========================
# MAIN REPLY
# =========================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    drug_input = update.message.text.strip()

    await update.message.reply_text("🔎 جارٍ البحث عن الدواء...")

    drug_data = search_drug(drug_input)
    if not drug_data:
        await update.message.reply_text(
            "❌ لم يتم العثور على الدواء.\n"
            "تأكد من كتابة الاسم العلمي بالإنجليزية."
        )
        return

    raw_title = drug_data.get("title", drug_input)

    drug_name = (
        raw_title
        .split(" AND ")[0]
        .split("TABLET")[0]
        .split("CAPSULE")[0]
        .split("INJECTION")[0]
        .split("FOR ")[0]
        .strip()
        .title()
    )

    prompt = f"""
You are a clinical pharmacist.

Provide concise educational information about the following drug:

Drug name: {drug_name}

Use EXACTLY this structure:

MOA:
(2 lines max)

Side effects:
• bullet points

DDI:
• bullet points

Rules:
- No dosing
- No treatment decisions
- Educational only
"""

    ai_answer = groq_chat_with_fallback(prompt)

    if not ai_answer:
        await update.message.reply_text(
            "❌ الذكاء الاصطناعي غير متاح حاليًا.\n"
            "حاول مرة أخرى لاحقًا."
        )
        return

    await update.message.reply_text(
        f"💊 Drug name:\n{drug_name}\n\n"
        f"{ai_answer}\n\n"
        "⚠️ Educational information only."
    )


# =========================
# RUN BOT
# =========================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

print("Bot is running...")
app.run_polling()
