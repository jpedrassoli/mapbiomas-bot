<p align="left">
  <img src="https://scs.usp.br/identidadevisual/wp-content/uploads/2022/08/usp-logo-png-768x576.png" height="100"/>
</p>

# MapBiomas Bot

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python&logoColor=white)
![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-21.9-blue?logo=telegram&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey?logo=flask&logoColor=white)
![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?logo=render&logoColor=white)
![MapBiomas](https://img.shields.io/badge/MapBiomas-Coleção%2010-green)
![Groq](https://img.shields.io/badge/LLM-Groq%20%7C%20Llama%203.1-orange)
![License](https://img.shields.io/badge/License-CC--BY%204.0-orange)

Bot para o Telegram que permite consultar a distribuição de **uso e cobertura da terra** em municípios brasileiros, com base nos dados da **Coleção 10 do MapBiomas Brasil**. Além dos dados brutos, o bot gera uma **análise contextual automática** por meio de um modelo de linguagem (LLM), com base nas mudanças observadas entre 1985 e 2024.

Para usar no Telegram, procure por @mapbiomas_bot

Desenvolvido no âmbito do **Departamento de Geografia da Universidade de São Paulo (USP)**.

---

## Funcionalidades

- Consulta por município e estado (UF)
- Consulta por ano específico (1985–2024), com padrão para 2024
- Exibe todas as classes de uso e cobertura da terra com:
  - Nome oficial em português (nomenclatura MapBiomas)
  - Proporção percentual da área
  - Área em hectares por classe
  - Área total do município
- Exibe mudanças absolutas e percentuais de cada classe entre **1985 e 2024**
- Rankings nacionais e estaduais de mudança de cobertura:
  - Perda de Formação Florestal
  - Perda de Vegetação Nativa Total
  - Expansão de Pastagem
  - Expansão de Área Urbanizada
  - Expansão de Agricultura
- Análise contextual gerada por LLM com base exclusivamente nos dados do município

---

## Fonte dos Dados

Os dados utilizados são provenientes do **MapBiomas Brasil – Coleção 10**, que cobre o período de 1985 a 2024 e classifica o território brasileiro em mais de 30 classes de uso e cobertura da terra.

- Site oficial: [mapbiomas.org](https://mapbiomas.org)
- Resolução espacial: 30 metros
- Cobertura: todos os municípios do Brasil

---

## Arquitetura

```
Telegram → Webhook → Flask (Render Web Service) → SQLite → Resposta
                                                 ↘ Groq API (LLM) ↗
```

| Componente | Tecnologia |
|---|---|
| Linguagem | Python 3.14 |
| Framework web | Flask 3.0 |
| Bot | python-telegram-bot 21.9 |
| Banco de dados | SQLite (~280MB, hospedado no Google Drive) |
| Hospedagem | Render (Web Service, plano gratuito) |
| Integração Telegram | Webhook |
| Modelo de linguagem | Llama 3.1 8B via Groq API (gratuito) |

---

## Análise por LLM

A análise é gerada pelo modelo **Llama 3.1 8B** via [Groq API](https://groq.com), com instruções estritas para:

- Usar **exclusivamente** os dados fornecidos pelo banco
- Não fazer projeções futuras
- Não atribuir causas externas aos dados
- Não mencionar contexto histórico ou político não evidenciado nos dados

Os dados passados ao modelo incluem a cobertura completa de **1985 e 2024**, as variações por classe e os rankings de mudança nacional e estadual.

---

## Estrutura do Repositório

```
├── bot.py                    # Código principal do bot
├── preparar_db.py            # Script local para gerar o banco de dados SQLite
├── requirements.txt          # Dependências Python
├── runtime.txt               # Versão do Python
└── README.md
```

> O arquivo `dados.db` (SQLite, ~280MB) não está versionado no repositório. Ele é gerado localmente pelo script `preparar_db.py` a partir dos dados originais do MapBiomas e hospedado no Google Drive. O bot realiza o download automático na inicialização caso o arquivo não esteja presente.

---

## Como Usar o Bot

No Telegram, envie uma mensagem no formato:

```
Cidade, UF
```

ou com ano específico:

```
Cidade, UF, ano
```

**Exemplos:**
```
Campinas, SP
Belém, PA, 2000
São Paulo, SP, 2010
```

---

## Deploy

### Pré-requisitos

- Conta no [Render](https://render.com)
- Token de bot do Telegram (via [@BotFather](https://t.me/BotFather))
- Chave de API do Groq (via [console.groq.com](https://console.groq.com))
- Arquivo `dados.db` gerado localmente e hospedado no Google Drive (link público)

### Variáveis de Ambiente

| Variável | Descrição |
|---|---|
| `TELEGRAM_TOKEN` | Token do bot fornecido pelo BotFather |
| `GROQ_API_KEY` | Chave de API do Groq (gratuita) |

### Configuração no Render

| Campo | Valor |
|---|---|
| Tipo de serviço | Web Service |
| Runtime | Python |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python bot.py` |

---

## Instalação Local

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/seu-repo.git
cd seu-repo

# Instale as dependências
pip install -r requirements.txt

# Gere o banco de dados (necessário ter o CSV original)
python preparar_db.py

# Configure as variáveis de ambiente
export TELEGRAM_TOKEN=seu_token_aqui
export GROQ_API_KEY=sua_chave_groq

# Rode o bot
python bot.py
```

---

## Dependências

```
python-telegram-bot==21.9
flask[async]==3.0.0
gdown
requests
```

---

## Créditos

- Dados: [MapBiomas Brasil](https://mapbiomas.org) – Coleção 10
- Desenvolvimento: Julio Pedrassoli, Ph.D., Departamento de Geografia – Universidade de São Paulo (USP)

