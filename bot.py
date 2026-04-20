import os
import csv
import gzip
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# -----------------------------
# CARREGAR DADOS SEM PANDAS
# -----------------------------
dados = []
with gzip.open("dados_processados.csv.gz", "rt", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        dados.append({
            "municipality": row["municipality"],
            "state_acronym": row["state_acronym"],
            "year": row["year"],
            "area_ha": float(row["area_ha"]),
            "class_level_4": row["class_level_4"]
        })

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

    filtrados = [
        r for r in dados
        if r["municipality"].lower() == municipio.lower()
        and r["state_acronym"].upper() == uf.upper()
        and r["year"] == ano
    ]

    if not filtrados:
        return "Município ou ano não encontrado."

    total = sum(r["area_ha"] for r in filtrados)
    filtrados.sort(key=lambda r: r["area_ha"], reverse=True)

    resposta = f"📍 {municipio} ({uf}) - {ano}\n"
    resposta += "Fonte: MapBiomas – Coleção 10\n\n"
    for r in filtrados:
        perc = (r["area_ha"] / total) * 100
        resposta += f"{r['class_level_4']}: {perc:.1f}%\n"
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

@flask_app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    await bot_app.initialize()
    update = Update.de_json(request.get_json(), bot_app.bot)
    await bot_app.process_update(update)
    return "OK"

@flask_app.route("/")
def index():
    return "Bot online!"

import asyncio

async def main():
    await bot_app.initialize()
    await bot_app.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    print("Webhook configurado!")

if __name__ == "__main__":
    asyncio.run(main())
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)
