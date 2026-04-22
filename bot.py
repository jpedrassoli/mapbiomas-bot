import os
import sqlite3
import asyncio
import threading
import requests
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
if not os.path.exists("dados_llm.db"):
    print("Baixando dados_llm.db do Google Drive...")
    gdown.download(
        "https://drive.google.com/uc?id=1YK85GefVLSI5tXvGHhOhYcj4oDb3IrUY",
        "dados_llm.db", quiet=False
    )
    print("Download concluído!")

# -----------------------------
# CONSULTA PRINCIPAL
# -----------------------------
def buscar_ano(municipio, uf, ano):
    conn = sqlite3.connect("dados_llm.db")
    cursor = conn.execute(
        "SELECT class_level_4, area_ha FROM cobertura "
        "WHERE LOWER(municipality)=LOWER(?) AND UPPER(state_acronym)=UPPER(?) AND year=? "
        "ORDER BY area_ha DESC",
        (municipio, uf, str(ano))
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def buscar_rankings(municipio, uf):
    conn = sqlite3.connect("dados_llm.db")
    cursor = conn.execute(
        "SELECT * FROM rankings "
        "WHERE LOWER(municipality)=LOWER(?) AND UPPER(state_acronym)=UPPER(?)",
        (municipio, uf)
    )
    row = cursor.fetchone()
    conn.close()
    return row

def formatar_sinal(valor):
    return f"+{valor:.1f}" if valor >= 0 else f"{valor:.1f}"

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

    rows_ano = buscar_ano(municipio, uf, ano)
    if not rows_ano:
        return "Município ou ano não encontrado."

    rows_1985 = buscar_ano(municipio, uf, 1985)
    rows_2024 = buscar_ano(municipio, uf, 2024)
    rankings  = buscar_rankings(municipio, uf)

    # ---- Dados do ano consultado ----
    total = sum(r[1] for r in rows_ano)
    resposta = f"📍 {municipio} ({uf}) - {ano}\n"
    resposta += "Fonte: MapBiomas – Coleção 10\n\n"
    for classe, area in rows_ano:
        perc = (area / total) * 100
        nome = CLASSES_PT.get(classe, classe)
        resposta += f"{nome}: {perc:.1f}% ({area:.1f} ha)\n"
    resposta += f"\n🗺️ Área Total: {total:.1f} ha"

    # ---- Mudanças 1985–2024 ----
    if rows_1985 and rows_2024:
        dict_1985 = {r[0]: r[1] for r in rows_1985}
        dict_2024 = {r[0]: r[1] for r in rows_2024}
        todas_classes = sorted(set(dict_1985.keys()) | set(dict_2024.keys()))

        resposta += "\n\n━━━━━━━━━━━━━━━━━━━━━━"
        resposta += "\n📊 MUDANÇAS 1985–2024"
        resposta += "\n━━━━━━━━━━━━━━━━━━━━━━\n"
        for classe in todas_classes:
            ha_85 = dict_1985.get(classe, 0)
            ha_24 = dict_2024.get(classe, 0)
            delta_ha  = ha_24 - ha_85
            delta_pct = ((ha_24 - ha_85) / ha_85 * 100) if ha_85 > 0 else 0
            nome = CLASSES_PT.get(classe, classe)
            resposta += f"{nome}: {formatar_sinal(delta_ha)} ha ({formatar_sinal(delta_pct)}%)\n"

    # ---- Rankings ----
    if rankings:
        (_, _,
         fl_ha, fl_pct, fl_rbr, fl_ruf, fl_tbr, fl_tuf, fl_pbr, fl_puf,
         na_ha, na_pct, na_rbr, na_ruf, na_tbr, na_tuf, na_pbr, na_puf,
         pa_ha, pa_pct, pa_rbr, pa_ruf, pa_tbr, pa_tuf, pa_pbr, pa_puf,
         ur_ha, ur_pct, ur_rbr, ur_ruf, ur_tbr, ur_tuf, ur_pbr, ur_puf,
         ag_ha, ag_pct, ag_rbr, ag_ruf, ag_tbr, ag_tuf, ag_pbr, ag_puf,
        ) = rankings

        resposta += "\n━━━━━━━━━━━━━━━━━━━━━━"
        resposta += "\n🏆 RANKING BRASIL"
        resposta += "\n━━━━━━━━━━━━━━━━━━━━━━\n"
        resposta += f"Perda Florestal:      {fl_rbr}º de {fl_tbr} (top {fl_pbr:.0f}%)\n"
        resposta += f"Perda Veg. Nativa:    {na_rbr}º de {na_tbr} (top {na_pbr:.0f}%)\n"
        resposta += f"Expansão Pastagem:    {pa_rbr}º de {pa_tbr} (top {pa_pbr:.0f}%)\n"
        resposta += f"Expansão Urbana:      {ur_rbr}º de {ur_tbr} (top {ur_pbr:.0f}%)\n"
        resposta += f"Expansão Agricultura: {ag_rbr}º de {ag_tbr} (top {ag_pbr:.0f}%)\n"

        resposta += f"\n━━━━━━━━━━━━━━━━━━━━━━"
        resposta += f"\n🏆 RANKING {uf.upper()}"
        resposta += "\n━━━━━━━━━━━━━━━━━━━━━━\n"
        resposta += f"Perda Florestal:      {fl_ruf}º de {fl_tuf} (top {fl_puf:.0f}%)\n"
        resposta += f"Perda Veg. Nativa:    {na_ruf}º de {na_tuf} (top {na_puf:.0f}%)\n"
        resposta += f"Expansão Pastagem:    {pa_ruf}º de {pa_tuf} (top {pa_puf:.0f}%)\n"
        resposta += f"Expansão Urbana:      {ur_ruf}º de {ur_tuf} (top {ur_puf:.0f}%)\n"
        resposta += f"Expansão Agricultura: {ag_ruf}º de {ag_tuf} (top {ag_puf:.0f}%)\n"

    # ---- Análise LLM ----
    analise = gerar_analise(municipio, uf, rows_1985, rows_2024, rankings)
    if analise:
        resposta += "\n━━━━━━━━━━━━━━━━━━━━━━"
        resposta += "\n🤖 ANÁLISE"
        resposta += "\n━━━━━━━━━━━━━━━━━━━━━━\n"
        resposta += analise

    return resposta

# -----------------------------
# ANÁLISE COM LLM (GROQ)
# -----------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def formatar_dados_para_llm(rows):
    if not rows:
        return "Sem dados."
    total = sum(r[1] for r in rows)
    linhas = []
    for classe, area in rows:
        nome = CLASSES_PT.get(classe, classe)
        pct  = (area / total * 100)
        linhas.append(f"  {nome}: {area:.1f} ha ({pct:.1f}%)")
    return "\n".join(linhas)

def formatar_rankings_para_llm(rankings):
    if not rankings:
        return "Sem dados de ranking."
    (_, _,
     fl_ha, fl_pct, fl_rbr, fl_ruf, fl_tbr, fl_tuf, fl_pbr, fl_puf,
     na_ha, na_pct, na_rbr, na_ruf, na_tbr, na_tuf, na_pbr, na_puf,
     pa_ha, pa_pct, pa_rbr, pa_ruf, pa_tbr, pa_tuf, pa_pbr, pa_puf,
     ur_ha, ur_pct, ur_rbr, ur_ruf, ur_tbr, ur_tuf, ur_pbr, ur_puf,
     ag_ha, ag_pct, ag_rbr, ag_ruf, ag_tbr, ag_tuf, ag_pbr, ag_puf,
    ) = rankings
    return (
        f"  Perda Florestal: {fl_ha:.1f} ha ({fl_pct:.1f}%) | "
        f"BR: {fl_rbr}º/{fl_tbr} | UF: {fl_ruf}º/{fl_tuf}\n"
        f"  Perda Veg. Nativa: {na_ha:.1f} ha ({na_pct:.1f}%) | "
        f"BR: {na_rbr}º/{na_tbr} | UF: {na_ruf}º/{na_tuf}\n"
        f"  Expansão Pastagem: {pa_ha:.1f} ha ({pa_pct:.1f}%) | "
        f"BR: {pa_rbr}º/{pa_tbr} | UF: {pa_ruf}º/{pa_tuf}\n"
        f"  Expansão Urbana: {ur_ha:.1f} ha ({ur_pct:.1f}%) | "
        f"BR: {ur_rbr}º/{ur_tbr} | UF: {ur_ruf}º/{ur_tuf}\n"
        f"  Expansão Agricultura: {ag_ha:.1f} ha ({ag_pct:.1f}%) | "
        f"BR: {ag_rbr}º/{ag_tbr} | UF: {ag_ruf}º/{ag_tuf}\n"
    )

def gerar_analise(municipio, uf, rows_1985, rows_2024, rankings):
    if not GROQ_API_KEY:
        return None

    prompt = f"""Você é um analista de dados geográficos e ambientais.
Com base EXCLUSIVAMENTE nos dados fornecidos abaixo, faça uma análise objetiva em português do uso e cobertura da terra do município de {municipio} ({uf}) entre 1985 e 2024.

REGRAS OBRIGATÓRIAS:
- Use apenas os números fornecidos. Não invente dados.
- Não faça projeções futuras.
- Não atribua causas que não estejam evidentes nos dados.
- Não mencione eventos históricos, políticas públicas ou contexto externo.
- Seja conciso: no máximo 5 frases.
- Escreva em português.
- Ao final inclua uma frase concisa iniciada por "Segundo a análise do Llama 3.1", seguida de uma análise de contexto baseada nos dados, indicando o processo de mudança de uso da terra predominante.

DADOS DE COBERTURA EM 1985:
{formatar_dados_para_llm(rows_1985)}

DADOS DE COBERTURA EM 2024:
{formatar_dados_para_llm(rows_2024)}

RANKINGS (mudanças 1985–2024):
{formatar_rankings_para_llm(rankings)}
"""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
                "temperature": 0.2
            },
            timeout=15
        )
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Erro na LLM: {e}")
        return None

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
TOKEN       = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = "https://mapbiomas-bot.onrender.com"

flask_app = Flask(__name__)
bot_app   = ApplicationBuilder().token(TOKEN).build()

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.TEXT, responder))

async def setup():
    await bot_app.initialize()
    await bot_app.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    print("Webhook configurado!")

asyncio.run_coroutine_threadsafe(setup(), loop).result()

@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), bot_app.bot)
    asyncio.run_coroutine_threadsafe(bot_app.process_update(update), loop)
    return "OK"

@flask_app.route("/")
def index():
    return "Bot online!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)
