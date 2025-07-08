from fastapi import FastAPI, Request
import requests
import uvicorn
import yaml
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI()

with open('./default.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)['config']


@app.post("/notify")
async def notify(request: Request):
    data = await request.json()
    report_id = data.get("report_id")
    report_data = requests.get(
        f"http://{config['api']['host']}:{config['api']['port']}/report/{report_id}",
    )
    if report_data.status_code == 200:
        report = report_data.json()
        message_text = f'Новая жалоба:\n\nТекст:\n{report["text"]}\n\nНастроение:\n{report["sentiment"]}'
        response = requests.post(
            f"https://api.telegram.org/bot{config['telegram_api']['bot_token']}/sendMessage",
            json={
                "chat_id": config['telegram_api']['admin_id'],
                "text": message_text
            }
        )
        if response.status_code != 200:
            logging.error("Failed to send Telegram message")

        change_status = requests.put(
            f"http://{config['api']['host']}:{config['api']['port']}/change_status",
            json={
                "report_id": report_id,
                "status": "closed"
            }
        )
        if change_status.status_code != 200:
            logging.error("Failed to change report status")
            return {"error": "Status not updated"}

        return {"status": "ok"}
    else:
        return {"error": report_data.text}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=config['telegram_api']['host'],
        port=config['telegram_api']['port']
    )
