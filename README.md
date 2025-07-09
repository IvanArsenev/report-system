# Report system API

A service for processing complaints based on the API Layer service (for determining the sentiment `["positive", "negative", "neutral"]`), as well as a local llm model for determining the complaint category

## Description

The project is a web service (FastAPI) that processes complaints through third-party APIs, and also sends complaints to the administrator via a telegram bot and Google Docs.

---

## Installation

```bash
git https://github.com/IvanArsenev/report-system
```
```bash
cd report-system
```

```bash
docker compose up --build
```

```bash
docker exec -it ollama_v3 ollama pull llama3
```

---

## ⚙️ Configuration

Create a YAML configuration file (for example, `config.yml`):

```yaml
config:
  api:
    host: '127.0.0.1'
    port: 8000
  sentiment_an:
    api_layer_url: 'https://api.apilayer.com/sentiment/analysis'
    api_layer_key: 'apilayer api key'
  telegram:
    bot_token: 'token'
    admin_id: 1234567890
  ollama:
    host: 'http://localhost:11434'
    prompt: 'Ты часть программного кода, ты должен отвечать только одним из предоставленных вариантов. Определи категорию жалобы: {text}. Варианты: техническая, оплата, другое.'
  google:
    scopes: ['https://www.googleapis.com/auth/spreadsheets']
    service_account_file_path: './google_api_key.json'
    doc_id: 'id документа'
```

---

## Launch

> The launch is done automatically via docker

The server will be available at `http://127.0.0.1:8000` (can be changed in config).

---

## Endpoints

### `POST /report`

Endpoint to receive and store user reports.

**Parameters:**

* `text` (str): Text of report
* `status` ("open" or "closed", optional): Status of report ("open" by default)

**Request example:**

```
POST http://127.0.0.1:8000/report
```
```json
{
  "text": "Не приходит SMS-код"
}
```

**Response example:**

```json
{
  "id": 1, 
  "status": "open", 
  "sentiment": "neutral", 
  "category": "техническая"
}
```

---

### `PUT /change_status`

Endpoint to change the status of user reports.

**Request example:**

```
PUT http://127.0.0.1:8000/change_status
```
```json
{
  "report_id": 1,
  "status": "closed"
}
```

**Response example:**

```json
{
  "id": 1, 
  "new_status": "closed"
}
```

---

## Project structure

```
├── main.py                  # FastAPI-application
├── models.py                # Classes used by service
├── database_functions.py    # Functions to use database
├── bot.py                   # Telegram bot
├── default.yaml             # Project Configuration
├── docker-compose.yml       # Docker compose (:
├── poetry.lock
├── poetry.toml
└── README.md
```

---

## About me

• В каком часовом поясе вы находитесь?

UTC+7 (GMT+7)

---

• Готовы ли вы работать в часовом поясе, отличном от вашего?

Да

---

• Есть ли у вас возможность синхронизироваться с командой в определенные часы (например, 2–4 часа в день)?

Да, но если дейлик длится больше 1 часа, то эта хрень падает `(шутка)`:

![meme_img](https://sun9-59.userapi.com/s/v1/ig2/bGI4ggexA-vF-4buMro4MKDyAWXadxa4q35s109SbIB9BYwZsBsj3uTsRGpPeEFA4MB5xOxlhum1pGiePxCF42JP.jpg?quality=96&as=32x39,48x58,72x87,108x130,160x193,240x289,360x433,480x578,540x650,640x771,720x867,1063x1280&from=bu&cs=1063x0)

---

### Опыт работы

• Какой у вас опыт в разработке?

Если коротко, опыт коммерческой разработки около 3 лет

---

• Какие задачи в предыдущих проектах/должностях были для вас наиболее сложными?

Одним из самых сложных проектов, был - чат бот, который помогал пользователям KoronaPay решать их вопросы не через RAG или GPT, а через прописанные сценарии

---

• Есть ли у вас портфолио или кейсы, которыми можно поделиться?

В целом все проекты, которыми я могу поделиться сохранены в моем github

---

### Доступность и время
• Сколько часов в неделю вы готовы уделять работе?

40+ (иногда могу перерабатывать, особенно если горят дедлайны)

---

• Предпочитаете ли вы гибкий график или фиксированные рабочие часы?

Гибкий график предпочтительнее

---

• Как планируете совмещать эту работу с другими обязательствами (если есть)?

Я закончил 3 курс, при том совмещая фулл тайм работу в ЦФТ (Центр Финансовых Технологий), особой нагрузки не испытывал, так как учебой занимался в свободное от работы время, поэтому проблем возникнуть не должно
