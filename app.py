from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import openai
import gspread
from datetime import datetime
from dotenv import load_dotenv
import os
from website_search import load_website_data, find_best_match

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# CONFIG
app = Flask(__name__)

# Google Sheet Setup
gc = gspread.service_account(filename="whatsuppp-d60313f83869.json")
sheet = gc.open_by_key("1EG0zNiWHtBow_K4cjlAE_BM0kYdDlrzS2tbih2DKEwQ").worksheet("Prijslijst")
logsheet = gc.open_by_key("1EG0zNiWHtBow_K4cjlAE_BM0kYdDlrzS2tbih2DKEwQ").worksheet("Leads")  # ✅ NU OP DE JUISTE PLAATS

# Website knowledgebase
pages_data, embeddings = load_website_data()

# START MENU
menu_text = """
👋 Welkom bij Terrazzo!
Waarmee kunnen we je helpen?

1️⃣ Openingsuren
2️⃣ Onderhoud
3️⃣ Vraag stellen
4️⃣ Prijs opvragen
5️⃣ Afspraak maken
"""

# ASK CHATGPT
def ask_chatgpt(message):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": message}],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

# LEAD LOGGING
def log_lead_to_sheet(sender, vraag, antwoord, fase):
    try:
        tijd = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logsheet.append_row([tijd, sender, vraag, antwoord, fase])
    except Exception as e:
        print(f"Loggen mislukt: {e}")

# PRIJZEN
def zoek_prijs(product_naam):
    try:
        producten = sheet.get_all_records()
        for rij in producten:
            if product_naam.lower() in rij["Productnaam"].lower():
                prijs = rij.get("Prijs per m²", "onbekend")
                maat = rij.get("Afmeting", "")
                return f"🧱 {rij['Productnaam']} {maat} kost {prijs} per m²."
    except Exception as e:
        return None
    return None

# AFSPRAKEN
dagen = ["Saturday 31 May", "Sunday 01 June", "Monday 02 June"]
tijden = ["10", "13", "16"]
afspraak_state = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "")
    response = MessagingResponse()
    msg = response.message()

    if incoming_msg.lower() in ("hi", "start", "menu", "hallo", "hello") or sender not in afspraak_state:
        afspraak_state[sender] = {"fase": None}
        msg.body("Hallo! Hoe kan ik u vandaag helpen? 👋 Welkom bij Terrazzo!\n" + menu_text)
        return str(response)

    fase = afspraak_state[sender].get("fase")

    if fase == "wacht_op_vraag":
        antwoord = find_best_match(incoming_msg, pages_data, embeddings)
        if antwoord:
            msg.body(f"📄 Gevonden op de site:\n\n{antwoord}")
            log_lead_to_sheet(sender, incoming_msg, antwoord, "Vraag (website)")
        else:
            antwoord = ask_chatgpt(incoming_msg)
            msg.body(f"{antwoord}")
            log_lead_to_sheet(sender, incoming_msg, antwoord, "Vraag (GPT)")
        afspraak_state[sender]["fase"] = None
        return str(response)

    elif fase == "wacht_op_product":
        antwoord = zoek_prijs(incoming_msg)
        if antwoord:
            msg.body(f"{antwoord}")
            log_lead_to_sheet(sender, incoming_msg, antwoord, "Prijs")
        else:
            msg.body(f"❌ Sorry, dit product kon ik niet vinden. Probeer een andere naam.\n\n{menu_text}")
            log_lead_to_sheet(sender, incoming_msg, "Product niet gevonden", "Prijs")
        afspraak_state[sender]["fase"] = None
        return str(response)

    elif fase == "datum_keuze" and incoming_msg in ["1", "2", "3"]:
        afspraak_state[sender]["gekozen_dag"] = dagen[int(incoming_msg)-1]
        msg.body("Kies een tijd:\n🕙 10:00\n🕐 13:00\n🕓 16:00\nAntwoord met 10, 13 of 16")
        afspraak_state[sender]["fase"] = "tijd_keuze"
        return str(response)

    elif fase == "tijd_keuze" and incoming_msg in tijden:
        gekozen = afspraak_state[sender].get("gekozen_dag", "onbekend")
        msg.body(f"✅ Afspraak bevestigd op {gekozen} om {incoming_msg}:00. Tot dan!")
        afspraak_state[sender]["fase"] = None
        return str(response)

    elif incoming_msg == "1":
        msg.body("🕒 Onze showroom is open van maandag tot zaterdag van 10:00 tot 18:00. Zondag gesloten.")
        return str(response)

    elif incoming_msg == "2":
        msg.body("🧽 Gebruik een pH-neutraal reinigingsmiddel en vermijd agressieve producten. Zie onze onderhoudsgids.")
        return str(response)

    elif incoming_msg == "3":
        msg.body("Stel je vraag en ik geef je een persoonlijk antwoord 🤖")
        afspraak_state[sender]["fase"] = "wacht_op_vraag"
        return str(response)

    elif incoming_msg == "4":
        msg.body("Geef de naam van het product dat je zoekt (bijv. Calacatta 60x60)")
        afspraak_state[sender]["fase"] = "wacht_op_product"
        return str(response)

    elif incoming_msg == "5":
        antwoord = "Kies een datum:\n"
        for i, dag in enumerate(dagen):
            antwoord += f"{i+1}️⃣ {dag}\n"
        msg.body(antwoord)
        afspraak_state[sender]["fase"] = "datum_keuze"
        return str(response)

    else:
        antwoord = find_best_match(incoming_msg, pages_data, embeddings)
        if antwoord:
            msg.body(f"📄 Gevonden op de site:\n\n{antwoord}")
        else:
            msg.body(f"{ask_chatgpt(incoming_msg)}\n\n{menu_text}")
        return str(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)