import os
import sqlite3
import asyncio
import gdown
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

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
        resposta += f"{classe}: {perc:.1f}%\n"
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
# FLASK + WEBHOOK
# -----------------------------
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = "https://mapbiomas-bot.onrender.com"

flask_app = Flask(__name__)
bot_app = ApplicationBuilder().token(TOKEN).build()

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.TEXT, responder))

# Inicializa tudo em uma única chamada async
async def setup():
    await bot_app.initialize()
    await bot_app.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    print("Webhook configurado!")

asyncio.run(setup())

# -----------------------------
# ROTA DO WEBHOOK
# -----------------------------
@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), bot_app.bot)
    asyncio.run(bot_app.process_update(update))
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
