from fastapi import FastAPI, Request
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
        "message": "Welcome to the FreshBooks - MCP server.",
        "available_routes": ["/mcp/context"]
    }

@app.post("/mcp/context")
async def mcp_handler(request: Request):
    try:
        msg = await request.json()

        # ✅ Validate JSON-RPC structure
        if msg.get("jsonrpc") != "2.0" or "method" not in msg or "id" not in msg:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "error": {
                    "code": -32600,
                    "message": "Invalid Request"
                }
            })

        method = msg["method"]
        req_id = msg["id"]

        # ✅ Handle supported method
        if method == "getContext":
            headers = {
                "Authorization": f"Bearer {FRESHBOOKS_TOKEN}",
                "Api-Version": "alpha"
            }

            url = f"https://api.freshbooks.com/accounting/account/{ACCOUNT_ID}/invoices/invoices"
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32000,
                        "message": "Failed to fetch invoices"
                    }
                })

            invoices = response.json().get("response", {}).get("result", {}).get("invoices", [])

            return JSONResponse({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
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
            })

        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": "Method not found"
                }
            })

    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32099,
                "message": str(e)
            }
        })