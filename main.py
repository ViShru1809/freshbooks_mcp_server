from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
import requests
import os
import json

load_dotenv()

FRESHBOOKS_TOKEN = os.getenv("FRESHBOOKS_TOKEN")
ACCOUNT_ID = os.getenv("FRESHBOOKS_ACCOUNT_ID")

app = FastAPI()

@app.websocket("/mcp")
async def mcp_handler(websocket: WebSocket):
    await websocket.accept()
    print("✅ Claude connected via MCP")

    try:
        while True:
            data = await websocket.receive_text()
            print("⬅️ Received:", data)

            request = json.loads(data)
            req_type = request.get("type")

            # Only supporting "get_context" calls for now
            if req_type == "get_context":
                context = await fetch_freshbooks_context()
                response = {
                    "type": "context",
                    "context": context
                }
                await websocket.send_text(json.dumps(response))
                print("➡️ Sent context")
            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Unsupported request type: {req_type}"
                }))

    except WebSocketDisconnect:
        print("❌ Claude disconnected")


async def fetch_freshbooks_context():
    if not FRESHBOOKS_TOKEN or not ACCOUNT_ID:
        return {"error": "Missing credentials"}

    headers = {
        "Authorization": f"Bearer {FRESHBOOKS_TOKEN}",
        "Api-Version": "alpha"
    }

    url = f"https://api.freshbooks.com/accounting/account/{ACCOUNT_ID}/invoices/invoices"
    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        return {"error": "Failed to fetch invoices"}

    invoices = res.json().get("response", {}).get("result", {}).get("invoices", [])

    return {
        "freshbooks_summary": [
            {
                "invoice_number": inv.get("invoice_number"),
                "amount": inv.get("amount", {}).get("amount"),
                "status": inv.get("status"),
                "payment_status": inv.get("payment_status"),
                "due_date": inv.get("due_date"),
                "client": inv.get("fname")
            }
            for inv in invoices
        ]
    }