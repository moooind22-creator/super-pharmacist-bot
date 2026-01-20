import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from groq import Groq

# =========================
# ENV VARIABLES
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN or not GROQ_API_KEY:
    raise ValueError("Missing BOT_TOKEN or GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

# =========================
# GROQ MODELS (FALLBACK)
# =========================
MODELS = [
    "llama-3.1-8b-instant",
    "llama-3-8b-instruct",
]

# =========================
# GROQ CHAT FUNCTION
# =========================
def groq_chat_with_fallback(prompt: str) -> str:
    for model in MODELS:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a clinical pharmacist. "
                            "Provide concise, accurate, educational information only. "
                            "Format the answer exactly as:\n"
                            "Drug name:\n"
                            "MOA:\n"
                            "Side effects:\n"
                            "DDI:\n"
                            "Use bullet points where appropriate."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            return completion.choices[0].message.content
        except Exception as e:
            last_error = e
            continue
    return f"❌ Error contacting AI model:\n{last_error}"

# =========================
# HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً\n"
        "💊 Super Pharmacist Bot\n\n"
        "اكتب الاسم العلمي للدواء (بالإنجليزي)\n"
        "مثال:\n"
        "metformin\n"
        "omeprazole\n\n"
        "⚠️ المعلومات إرشادية فقط."
    )

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    drug_name = update.message.text.strip()

    await update.message.reply_text("🔍 جارٍ البحث عن الدواء...")

    prompt = f"""
Provide the following for the drug: {drug_name}

Required format:

Drug name:
MOA:
Side effects:
DDI:
"""

    answer = groq_chat_with_fallback(prompt)

    await update.message.reply_text(answer)

# =========================
# RUN BOT
# =========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
