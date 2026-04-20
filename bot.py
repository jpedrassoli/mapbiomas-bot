import os
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from flask import Flask, request

# carregar dados já processados
df = pd.read_csv("dados_processados.csv.gz")

# -----------------------------
# FUNÇÃO DE CONSULTA
# -----------------------------
def consultar(texto):
    try:
        partes = [p.strip() for p in texto.split(",")]
        municipio = partes[0]
        uf = partes[1]
        ano = int(partes[2]) if len(partes) > 2 else 2024
    except:
        return (
            "Formato inválido.\n\n"
            "Use:\n"
            "Cidade, UF\n"
            "ou\n"
            "Cidade, UF, ano\n\n"
            "Ex: Campinas, SP, 2000"
        )
    filtro = (
        (df["municipality"].str.lower() == municipio.lower()) &
        (df["state_acronym"].str.upper() == uf.upper()) &
        (df["year"] == ano)
    )
    dados = df[filtro]
    if dados.empty:
        return "Município ou ano não encontrado."
    total = dados["area_ha"].sum()
    dados = dados.sort_values(by="area_ha", ascending=False)
    resposta = f"📍 {municipio} ({uf}) - {ano}\n"
    resposta += "Fonte: MapBiomas – Coleção 10\n\n"
    for _, row in dados.iterrows():
        perc = (row["area_ha"] / total) * 100
        resposta += f"{row['class_level_4']}: {perc:.1f}%\n"
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

# -----------------------------
# INICIALIZAÇÃO
# -----------------------------
import asyncio

async def main():
    await bot_app.initialize()
    await bot_app.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    print("Webhook configurado!")

if __name__ == "__main__":
    asyncio.run(main())
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)
