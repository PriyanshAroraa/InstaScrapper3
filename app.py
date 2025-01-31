from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import time
import os

app = Flask(__name__)

# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "OPTIONS"]}})

# Explicitly add CORS headers
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# Bright Data API Key
API_KEY = "60a18bcb5ff44e333b12b04b65c0bbf41cf6f957a5ec2f323d019de6531015c6"
DATASET_ID = "gd_l1vikfch901nx3by4"

# API Endpoints
TRIGGER_URL = f"https://api.brightdata.com/datasets/v3/trigger?dataset_id={DATASET_ID}&include_errors=true"
SNAPSHOT_URL = "https://api.brightdata.com/datasets/v3/snapshot/{}?format=json"

def get_snapshot_id(instagram_username):
    """Trigger Bright Data request and get snapshot ID"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = json.dumps([{"url": f"https://www.instagram.com/{instagram_username}/"}])

    try:
        response = requests.post(TRIGGER_URL, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        print(f"✅ Snapshot ID Triggered: {response.json()}")
        return response.json().get("snapshot_id")
    except Exception as e:
        print(f"❌ Error in get_snapshot_id: {str(e)}")
        return None

def wait_for_snapshot(snapshot_id):
    """Wait for snapshot to be ready"""
    headers = {"Authorization": f"Bearer {API_KEY}"}

    try:
        while True:
            response = requests.get(SNAPSHOT_URL.format(snapshot_id), headers=headers, timeout=10)
            response.raise_for_status()

            json_response = response.json()
            if "status" not in json_response:
                print("✅ Snapshot Ready!")
                return json_response  # Return the JSON data

            print("⏳ Waiting for snapshot... Retrying in 30 sec...")
            time.sleep(30)

    except Exception as e:
        print(f"❌ Error in wait_for_snapshot: {str(e)}")
        return {"error": str(e)}

@app.route("/get_instagram_data", methods=["GET", "OPTIONS"])
def get_instagram_data():
    if request.method == "OPTIONS":
        return jsonify({}), 200  # Respond to preflight CORS requests

    username = request.args.get("username")
    if not username:
        return jsonify({"error": "Username parameter is required"}), 400

    snapshot_id = get_snapshot_id(username)
    if not snapshot_id:
        return jsonify({"error": "Failed to get snapshot ID"}), 500
    
    json_data = wait_for_snapshot(snapshot_id)
    return jsonify(json_data)

# Use Railway's assigned port or default to 5000
PORT = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
