from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

FRESHBOOKS_TOKEN = os.getenv("FRESHBOOKS_TOKEN")
ACCOUNT_ID = os.getenv("FRESHBOOKS_ACCOUNT_ID")

app = FastAPI()

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the FreshBooks MCP server.",
        "available_routes": ["/mcp/context"]
    }

@app.websocket("/mcp/context")
async def mcp_handler(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            print("Received:", data)

            try:
                msg = json.loads(data)

                if msg.get("type") == "connect":
                    await websocket.send_text(json.dumps({"type": "ready"}))

                elif msg.get("type") == "get":
                    # Fetch invoices from FreshBooks
                    headers = {
                        "Authorization": f"Bearer {FRESHBOOKS_TOKEN}",
                        "Api-Version": "alpha"
                    }

                    url = f"https://api.freshbooks.com/accounting/account/{ACCOUNT_ID}/invoices/invoices"
                    response = requests.get(url, headers=headers)

                    if response.status_code != 200:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Failed to fetch invoices"
                        }))
                        continue

                    invoices = response.json().get("response", {}).get("result", {}).get("invoices", [])

                    context = {
                        "type": "context",
                        "context": {
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
                    }

                    await websocket.send_text(json.dumps(context))

                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Unknown request type"
                    }))

            except Exception as e:
                print("Error:", e)
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))

    except WebSocketDisconnect:
        print("Disconnected")
