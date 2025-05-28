from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import os
import openai

# Загрузка переменных окружения
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Инициализация Flask
app = Flask(__name__)

# Кнопки FAQ
FAQ_BUTTONS = {
    "Levertijd": "Onze levertijd bedraagt meestal 2-3 werkdagen.",
    "Retour": "U kunt binnen 14 dagen retourneren via onze retourservice.",
    "Contact": "U kunt ons bereiken via info@bedrijf.nl of op 012-345678.",
    "Afspraak maken": "Wilt u een afspraak maken? Stuur ons uw gewenste datum en tijd."
}

# Сообщение при старте
START_MESSAGE = (
    "Welkom! 👋\n"
    "Kies een van de opties:\n"
    "1️⃣ Levertijd\n"
    "2️⃣ Retour\n"
    "3️⃣ Contact\n"
    "4️⃣ Afspraak maken\n\n"
    "Of stel uw vraag direct."
)

@app.route("/", methods=["GET"])
def home():
    return "Bot werkt!"

@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.values.get("Body", "").strip()
    resp = MessagingResponse()
    msg = resp.message()
    lower_msg = incoming_msg.lower()

    if lower_msg in ["hi", "hello", "start", "hallo"]:
        msg.body(START_MESSAGE)
        return str(resp)

    for key, antwoord in FAQ_BUTTONS.items():
        if key.lower() in lower_msg:
            msg.body(antwoord)
            return str(resp)

    # AI-ответ
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Beantwoord kort en professioneel vragen van klanten."},
                {"role": "user", "content": incoming_msg},
            ],
        )
        reply = completion.choices[0].message.content.strip()
        msg.body(reply)
    except Exception as e:
        msg.body("Er is een fout opgetreden. Probeer later opnieuw.")

    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)