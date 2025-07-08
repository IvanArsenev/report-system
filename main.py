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

from models import ReportBody, ChangeStatusBody
from database_functions import save_report, init_db, update_report, get_reports_from_db

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
            report_id=data.id,
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


if __name__ == "__main__":
    init_db()
    uvicorn.run(
        app,
        host=config['api']['host'],
        port=config['api']['port']
    )
