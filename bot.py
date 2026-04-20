import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

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

    # ordenar todas as classes (SEM limitar)
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
# INICIALIZAÇÃO DO BOT
# -----------------------------
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, responder))

print("Bot rodando...")
app.run_polling()