from fastapi import FastAPI, Request, HTTPException
from google.cloud import bigquery
from datetime import datetime, UTC
import hashlib
import hmac
import json
import os

app = FastAPI()

client = bigquery.Client(project="vitor-oliveira-analytics")

TABLE_ID = "vitor-oliveira-analytics.tracking.events_raw"

SECRET_KEY = os.getenv("SECRET_KEY", "minha_chave_secreta")


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/event")
async def event(request: Request):

    # 1. pega assinatura do header
    received_signature = request.headers.get("x-signature")

    if not received_signature:
        raise HTTPException(
            status_code=401,
            detail="Missing signature"
        )

    # 2. lê JSON do evento
    data = await request.json()

    # 3. pega timestamp original em ms
    timestamp_ms = (
        data.get("x-sst-system_properties", {})
        .get("request_start_time_ms")
    )

    # 4. converte timestamp para formato aceito pelo BigQuery
    timestamp = None

    if timestamp_ms:
        timestamp = datetime.fromtimestamp(
            int(timestamp_ms) / 1000,
            UTC
        ).isoformat()

    # 5. reconstrói exatamente a string usada no GTM
    raw_string = (
        f"{data.get('event_name')}|"
        f"{data.get('client_id')}|"
        f"{timestamp_ms}|"
        f"{SECRET_KEY}"
    )

    # 6. gera hash SHA256
    generated_signature = hashlib.sha256(
        raw_string.encode("utf-8")
    ).hexdigest()

    # logs
    print("RAW STRING:", raw_string)
    print("TIMESTAMP_MS:", timestamp_ms)
    print("TIMESTAMP:", timestamp)
    print("RECEIVED SIGNATURE:", received_signature)
    print("GENERATED SIGNATURE:", generated_signature)

    # 7. valida assinatura
    if not hmac.compare_digest(
        received_signature,
        generated_signature
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid signature"
        )

    # 8. insere no BigQuery
    row = {
        "event_name": data.get("event_name"),
        "user_id": data.get("client_id"),
        "timestamp": timestamp,
        "payload": json.dumps(data)
    }

    errors = client.insert_rows_json(TABLE_ID, [row])

    if errors:
        print(errors)

        return {
            "status": "error",
            "details": errors
        }
    print("TESTE3")
    return {"status": "ok"}