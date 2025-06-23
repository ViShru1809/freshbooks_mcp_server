from flask import Flask, jsonify
from dotenv import load_dotenv
import requests
import os

load_dotenv()

FRESHBOOKS_TOKEN = os.getenv("FRESHBOOKS_TOKEN")
ACCOUNT_ID = os.getenv("FRESHBOOKS_ACCOUNT_ID")

print("FRESHBOOKS_TOKEN is None?", FRESHBOOKS_TOKEN is None)
print("ACCOUNT_ID is:", ACCOUNT_ID)

app = Flask(__name__)

@app.route("/mcp/context", methods=["GET"])
def get_context():
    if not FRESHBOOKS_TOKEN or not ACCOUNT_ID:
        return jsonify({"error": "Missing FreshBooks token or account ID"}), 500

    headers = {
        "Authorization": f"Bearer {FRESHBOOKS_TOKEN}",
        "Api-Version": "alpha"
    }

    invoices_url = f"https://api.freshbooks.com/accounting/account/{ACCOUNT_ID}/invoices/invoices"
    print(f"Sending GET to: {invoices_url}")
    print(f"Using token: {'...' + FRESHBOOKS_TOKEN[-20:]}")  # Hide full token

    response = requests.get(invoices_url, headers=headers)
    print("Response Code:", response.status_code)
    print("Response Body:", response.text)

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch invoices"}), 500

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

    return jsonify(context)

if __name__ == "__main__":
    print("Starting MCP Server on http://localhost:5001/mcp/context")
    app.run(port=5001, debug=True)