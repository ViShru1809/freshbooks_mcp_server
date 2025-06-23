from fastapi import FastAPI, WebSocket
from dotenv import load_dotenv
import requests
import os
from fastapi.responses import JSONResponse

load_dotenv()

FRESHBOOKS_TOKEN = os.getenv("FRESHBOOKS_TOKEN")
ACCOUNT_ID = os.getenv("FRESHBOOKS_ACCOUNT_ID")

app = FastAPI()

@app.get("/")
def home():
    return {
        "message": "Welcome to the FreshBooks MCP server (WebSocket Ready)",
        "available_routes": ["/mcp"]
    }

@app.websocket("/mcp")
async def mcp_websocket(websocket: WebSocket):
    await websocket.accept()

    if not FRESHBOOKS_TOKEN or not ACCOUNT_ID:
        await websocket.send_json({"error": "Missing FreshBooks token or account ID"})
        await websocket.close()
        return

    headers = {
        "Authorization": f"Bearer {FRESHBOOKS_TOKEN}",
        "Api-Version": "alpha"
    }

    invoices_url = f"https://api.freshbooks.com/accounting/account/{ACCOUNT_ID}/invoices/invoices"

    try:
        response = requests.get(invoices_url, headers=headers)
        if response.status_code != 200:
            await websocket.send_json({"error": "Failed to fetch invoices"})
        else:
            invoices = response.json().get("response", {}).get("result", {}).get("invoices", [])

            summary = [
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

            await websocket.send_json({"freshbooks_summary": summary})

    except Exception as e:
        await websocket.send_json({"error": str(e)})

    await websocket.close()
