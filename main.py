"""Main FastAPI application entry point."""

import argparse
import logging
import requests
import yaml
import uvicorn
import urllib.parse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.llms import Ollama
from google.oauth2 import service_account
from googleapiclient.discovery import build

from models import ReportBody, ChangeStatusBody, ReportIdsModel, SentimentEnum
from database_functions import save_report, init_db, update_report, get_reports_from_db, get_report_by_id

logging.basicConfig(level=logging.INFO)
parser = argparse.ArgumentParser(description="Run FastAPI app with config")
parser.add_argument('--config', type=str, default='./default.yaml', help='Path to config YAML file')
args = parser.parse_args()


def load_config(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


config = load_config(args.config)['config']

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = Ollama(
    model="llama3",
    base_url=config['ollama']['host'],
)


credentials = service_account.Credentials.from_service_account_file(
    config['google']['service_account_file_path']
).with_scopes(config['google']['scopes'])

sheets_service = build('sheets', 'v4', credentials=credentials)


async def append_to_google_sheet(values: list):
    """
    Добавляет строку в Google Sheets.
    Values — список значений, например:
    ['Дата', 'Настроение', 'Текст жалобы']
    """
    try:
        body = {
            'values': [values]
        }
        result = sheets_service.spreadsheets().values().append(
            spreadsheetId=config['google']['doc_id'],
            range='Лист1!A1',
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        logging.info(f"Appended to Google Sheet: {result}")
    except Exception as e:
        logging.error(f"Failed to append to Google Sheet: {e}")


@app.post("/report")
async def report_error(data: ReportBody):
    """
    Endpoint to receive and store user reports.
    """
    sentiment = "unknown"
    category = "другое"

    try:
        encoded_text = urllib.parse.quote(data.text)
        response = requests.post(
            config['sentiment_an']['api_layer_url'],
            headers={
                'apikey': config['sentiment_an']['api_layer_key'],
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            data=f"body={encoded_text}"
        )
        if response.status_code == 200:
            sentiment = response.json().get("sentiment", "unknown")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error while getting sentiment: {e}')

    try:
        result = llm.invoke(config['ollama']['prompt'].format(text=data.text)).lower()
        if result in ['техническая', 'оплата']:
            category = result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error while getting category: {e}')

    try:
        report_id = save_report(
            text=data.text,
            status=data.status,
            sentiment=sentiment,
            category=category,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error while saving report: {e}')

    return {
        "id": report_id,
        "status": data.status,
        "sentiment": sentiment,
        "category": category,
    }


@app.put("/change_status")
async def change_status(data: ChangeStatusBody):
    """
    Endpoint to receive and change report.
    """
    try:
        report_id = update_report(
            report_id=data.report_id,
            status=data.status,
        )
        return {
            "id": report_id,
            "new_status": data.status,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports")
async def reports_per_hour():
    """
    Endpoint to receive all reports from the last hour.
    """
    try:
        return get_reports_from_db()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/report/{report_id}")
async def report_by_id(report_id: str):
    """
    Endpoint to receive all reports from the last hour.
    """
    try:
        return get_report_by_id(report_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/notify")
async def notify(report_ids: ReportIdsModel):
    """
    Endpoint to send a notifications.
    """
    report_ids = report_ids.report_ids
    for report_id in report_ids:
        report = await report_by_id(report_id)
        if report.category == 'техническая':
            logging.info('New report of technical category')
            message_text = (f'Новая жалоба:\n\nТекст:\n{report.text}\n\n'
                            f'Настроение:\n{SentimentEnum[report.sentiment].value}')
            response = requests.post(
                f"https://api.telegram.org/bot{config['telegram_api']['bot_token']}/sendMessage",
                json={
                    "chat_id": config['telegram_api']['admin_id'],
                    "text": message_text
                }
            )
            if response.status_code != 200:
                logging.error("Failed to send Telegram message")
            try:
                change_data = ChangeStatusBody(report_id=report_id, status="closed")
                await change_status(change_data)
            except Exception as e:
                logging.error(f"Failed to change report status {e}")
        elif report.category == 'оплата':
            logging.info('New report of payment category')
            data_of_report = report.timestamp.strftime('%H:%M:%S %d-%m-%Y')
            text_of_report = report.text
            sentiment_of_report = SentimentEnum[report.sentiment].value
            row_values = [data_of_report, sentiment_of_report, text_of_report]
            await append_to_google_sheet(row_values)
            try:
                change_data = ChangeStatusBody(report_id=report_id, status="closed")
                await change_status(change_data)
            except Exception as e:
                logging.error(f"Failed to change report status {e}")
        else:
            logging.info(
                'New report of other category: %s - %s - %s',
                report.timestamp,
                report.text,
                SentimentEnum[report.sentiment].value,
            )
    return {"message": "All reports was closed!"}


if __name__ == "__main__":
    init_db()
    uvicorn.run(
        app,
        host=config['api']['host'],
        port=config['api']['port']
    )
