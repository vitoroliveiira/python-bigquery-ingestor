from fastapi import FastAPI, Request
from google.cloud import bigquery
import json

app = FastAPI()

client = bigquery.Client(project="vitor-oliveira-analytics")

TABLE_ID = "vitor-oliveira-analytics.tracking.events_raw"


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/event")
async def event(request: Request):
    data = await request.json()

    row = {
        "event_name": data.get("event_name"),
        "user_id": data.get("user_id"),
        "timestamp": data.get("timestamp"),
        "payload": json.dumps(data)
    }

    errors = client.insert_rows_json(TABLE_ID, [row])

    if errors:
        return {"status": "error", "details": errors}

    return {"status": "ok"}