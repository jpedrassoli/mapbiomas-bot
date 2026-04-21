import os
import sqlite3
import asyncio
import threading
import gdown
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# -----------------------------
# TRADUÇÃO DAS CLASSES
# -----------------------------
CLASSES_PT = {
    "1.1. Forest Formation": "1.1. Formação Florestal",
    "1.2. Savanna Formation": "1.2. Formação Savânica",
    "1.3. Mangrove": "1.3. Mangue",
    "1.4 Floodable Forest": "1.4. Floresta Alagável",
    "1.5. Wooded Sandbank Vegetation": "1.5. Restinga Arbórea",
    "2.1. Wetland": "2.1. Campo Alagado e Área Pantanosa",
    "2.2. Grassland": "2.2. Formação Campestre",
    "2.3. Hypersaline Tidal Flat": "2.3. Apicum",
    "2.4. Herbaceous Sandbank Vegetation": "2.4. Restinga Herbácea",
    "2.4. Rocky Outcrop": "2.4. Afloramento Rochoso",
    "2.6. Other non Forest Formations": "2.6. Outras Formações não Florestais",
    "3.1. Pasture": "3.1. Pastagem",
    "3.2.1.1. Soybean": "3.2.1.1. Soja",
    "3.2.1.2. Sugar cane": "3.2.1.2. Cana",
    "3.2.1.3. Rice": "3.2.1.3. Arroz",
    "3.2.1.4. Cotton": "3.2.1.4. Algodão",
    "3.2.1.5. Other Temporary Crops": "3.2.1.5. Outras Lavouras Temporárias",
    "3.2.2.1. Coffee": "3.2.2.1. Café",
    "3.2.2.2. Citrus": "3.2.2.2. Citrus",
    "3.2.2.3. Palm Oil": "3.2.2.3. Dendê",
    "3.2.2.4. Other Perennial Crops": "3.2.2.4. Outras Lavouras Perenes",
    "3.3. Forest Plantation": "3.3. Silvicultura",
    "3.4. Mosaic of Uses": "3.4. Mosaico de Usos",
    "4.1. Beach, Dune and Sand Spot": "4.1. Praia, Duna e Areal",
    "4.2. Urban Area": "4.2. Área Urbanizada",
    "4.3. Mining": "4.3. Mineração",
    "4.4. Photovoltaic Project": "4.4. Usina Fotovoltaica",
    "4.5. Other non Vegetated Areas": "4.5. Outras Áreas não Vegetadas",
    "5.1. River, Lake and Ocean": "5.1. Rio, Lago e Oceano",
    "5.2. Aquaculture": "5.2. Aquicultura",
    "6. Not Observed": "6. Não observado",
}

# -----------------------------
# BAIXAR DADOS DO GOOGLE DRIVE
# -----------------------------
if not os.path.exists("dados.db"):
    print("Baixando dados.db do Google Drive...")
    gdown.download(
        "https://drive.google.com/uc?id=18j-3I7VukvW47O1jd7crlsP1UQw9u1GJ",
        "dados.db", quiet=False
    )
    print("Download concluído!")

# -----------------------------
# FUNÇÃO DE CONSULTA
# -----------------------------
def consultar(texto):
    try:
        partes = [p.strip() for p in texto.split(",")]
        municipio = partes[0]
        uf = partes[1]
        ano = partes[2].strip() if len(partes) > 2 else "2024"
    except:
        return (
            "Formato inválido.\n\n"
            "Use:\nCidade, UF\nou\nCidade, UF, ano\n\n"
            "Ex: Campinas, SP, 2000"
        )

    conn = sqlite3.connect("dados.db")
    cursor = conn.execute(
        "SELECT class_level_4, area_ha FROM cobertura "
        "WHERE LOWER(municipality)=LOWER(?) AND UPPER(state_acronym)=UPPER(?) AND year=? "
        "ORDER BY area_ha DESC",
        (municipio, uf, ano)
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "Município ou ano não encontrado."

    total = sum(r[1] for r in rows)
    resposta = f"📍 {municipio} ({uf}) - {ano}\n"
    resposta += "Fonte: MapBiomas – Coleção 10\n\n"
    for classe, area in rows:
        perc = (area / total) * 100
        nome = CLASSES_PT.get(classe, classe)
        resposta += f"{nome}: {perc:.1f}% ({area:.1f} ha)\n"
    resposta += f"\n🗺️ Área Total: {total:.1f} ha"
    return resposta

# -----------------------------
# COMANDO /start
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = (
        "🌎 *Consulta de Uso e Cobertura da Terra (MapBiomas)*\n\n"
        "Este bot permite consultar a distribuição de uso e cobertura da terra "
        "para municípios do Brasil.\n\n"
        "📌 *Como usar:*\n"
        "Digite o nome da cidade e a sigla do estado:\n"
        "`Campinas, SP`\n\n"
        "📅 *Ano (opcional):*\n"
        "Você pode especificar um ano entre 1985 e 2024:\n"
        "`Campinas, SP, 2000`\n\n"
        "⚠️ *Dicas importantes:*\n"
        "- Separe os campos com vírgula\n"
        "- Use a sigla do estado (SP, MG, PA...)\n"
        "- Use o nome completo do município\n\n"
        "Se não informar o ano, será utilizado 2024."
    )
    await update.message.reply_text(mensagem, parse_mode="Markdown")

# -----------------------------
# RESPOSTA GERAL
# -----------------------------
async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    resposta = consultar(texto)
    await update.message.reply_text(resposta)

# -----------------------------
# LOOP PERSISTENTE EM BACKGROUND
# -----------------------------
loop = asyncio.new_event_loop()

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

thread = threading.Thread(target=start_loop, args=(loop,), daemon=True)
thread.start()

# -----------------------------
# FLASK + WEBHOOK
# -----------------------------
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = "https://mapbiomas-bot.onrender.com"

flask_app = Flask(__name__)
bot_app = ApplicationBuilder().token(TOKEN).build()

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.TEXT, responder))

async def setup():
    await bot_app.initialize()
    await bot_app.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    print("Webhook configurado!")

asyncio.run_coroutine_threadsafe(setup(), loop).result()

# -----------------------------
# ROTA DO WEBHOOK
# -----------------------------
@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), bot_app.bot)
    asyncio.run_coroutine_threadsafe(bot_app.process_update(update), loop)
    return "OK"

@flask_app.route("/")
def index():
    return "Bot online!"

# -----------------------------
# INICIALIZAÇÃO
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)
