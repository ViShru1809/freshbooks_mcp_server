from fastapi import FastAPI
from fastapi.responses import JSONResponse
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

FRESHBOOKS_TOKEN = os.getenv("FRESHBOOKS_TOKEN")
ACCOUNT_ID = os.getenv("FRESHBOOKS_ACCOUNT_ID")

print("FRESHBOOKS_TOKEN is None?", FRESHBOOKS_TOKEN is None)
print("ACCOUNT_ID is:", ACCOUNT_ID)

# Create FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return JSONResponse({
        "message": "Welcome to the FreshBooks MCP server.",
        "available_routes": ["/mcp/context"]
    })

@app.get("/favicon.ico")
def favicon():
    return JSONResponse(status_code=204, content={})

@app.get("/mcp/context")
def get_context():
    if not FRESHBOOKS_TOKEN or not ACCOUNT_ID:
        return JSONResponse(status_code=500, content={
            "error": "Missing FreshBooks token or account ID"
        })

    headers = {
        "Authorization": f"Bearer {FRESHBOOKS_TOKEN}",
        "Api-Version": "alpha"
    }

    invoices_url = f"https://api.freshbooks.com/accounting/account/{ACCOUNT_ID}/invoices/invoices"
    print(f"Sending GET to: {invoices_url}")
    print(f"Using token: {'...' + FRESHBOOKS_TOKEN[-20:]}")

    response = requests.get(invoices_url, headers=headers)
    print("Response Code:", response.status_code)
    print("Response Body:", response.text)

    if response.status_code != 200:
        return JSONResponse(status_code=500, content={"error": "Failed to fetch invoices"})

    invoices = response.json().get("response", {}).get("result", {}).get("invoices", [])

    context = {
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

    return context