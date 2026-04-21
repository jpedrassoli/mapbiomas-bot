<p align="left">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/Webysther_20160322_-_Logo_USP.svg/1280px-Webysther_20160322_-_Logo_USP.svg.png" height="50"/>
  &nbsp;&nbsp;&nbsp;
  <img src="https://upload.wikimedia.org/wikipedia/pt/3/38/Logo_FFLCH-USP.png" height="50"/>
</p>

# MapBiomas Bot

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python&logoColor=white)
![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-21.9-blue?logo=telegram&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey?logo=flask&logoColor=white)
![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?logo=render&logoColor=white)
![MapBiomas](https://img.shields.io/badge/MapBiomas-Coleção%2010-green)
![License](https://img.shields.io/badge/License-CC--BY%204.0-orange)

Bot para o Telegram que permite consultar a distribuição de **uso e cobertura da terra** em municípios brasileiros, com base nos dados da **Coleção 10 do MapBiomas Brasil**.

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

---

## Fonte dos Dados

Os dados utilizados são provenientes do **MapBiomas Brasil – Coleção 10**, que cobre o período de 1985 a 2024 e classifica o território brasileiro em mais de 30 classes de uso e cobertura da terra.

- Site oficial: [mapbiomas.org](https://mapbiomas.org)
- Resolução espacial: 30 metros
- Cobertura: todos os municípios do Brasil

## Estrutura do Repositório

```
├── bot.py                    # Código principal do bot
├── preparar_db.py            # Script local para gerar o banco de dados SQLite
├── requirements.txt          # Dependências Python
├── runtime.txt               # Versão do Python
└── README.md
```

> O arquivo `dados.db` (SQLite, ~230MB) não está versionado no repositório. Ele é gerado localmente a partir dos dados originais do MapBiomas e hospedado no Google Drive. O bot realiza o download automático na inicialização caso o arquivo não esteja presente.

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
- Arquivo `dados.db` gerado localmente e hospedado no Google Drive (link público)

### Variáveis de Ambiente

| Variável | Descrição |
|---|---|
| `TELEGRAM_TOKEN` | Token do bot fornecido pelo BotFather |

### Configuração no Render

| Campo | Valor |
|---|---|
| Tipo de serviço | Web Service |
| Runtime | Python |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python bot.py` |

---

## 🛠️ Instalação Local

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/seu-repo.git
cd seu-repo

# Instale as dependências
pip install -r requirements.txt

# Gere o banco de dados (necessário ter o CSV original)
python preparar_db.py

# Configure o token
export TELEGRAM_TOKEN=seu_token_aqui

# Rode o bot
python bot.py
```

---

## Dependências

```
python-telegram-bot==21.9
flask[async]==3.0.0
gdown
```

---

## Créditos

- Dados: [MapBiomas Brasil](https://mapbiomas.org) – Coleção 10
- Desenvolvimento: Julio Pedrassoli, Ph.D., Departamento de Geografia – Universidade de São Paulo (USP)
