from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
import requests
import json
import time

app = Flask(__name__)

# Enable CORS for all routes and allow all origins
CORS(app, resources={r"/*": {"origins": "*"}})

# Bright Data API Key
API_KEY = "60a18bcb5ff44e333b12b04b65c0bbf41cf6f957a5ec2f323d019de6531015c6"

# Dataset ID
DATASET_ID = "gd_l1vikfch901nx3by4"

# API Endpoints
TRIGGER_URL = f"https://api.brightdata.com/datasets/v3/trigger?dataset_id={DATASET_ID}&include_errors=true"
SNAPSHOT_URL = "https://api.brightdata.com/datasets/v3/snapshot/{}?format=json"

def get_snapshot_id(instagram_username):
    """Trigger Bright Data and get snapshot ID"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = json.dumps([{"url": f"https://www.instagram.com/{instagram_username}/"}])
    response = requests.post(TRIGGER_URL, headers=headers, data=payload)
    
    if response.status_code == 200:
        return response.json().get("snapshot_id")
    return None

def wait_for_snapshot(snapshot_id):
    """Wait for snapshot to be ready and return JSON"""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    while True:
        response = requests.get(SNAPSHOT_URL.format(snapshot_id), headers=headers)
        
        # Ensure response is valid JSON before parsing
        try:
            json_response = response.json()
        except json.JSONDecodeError:
            return {"error": "Invalid response from API"}
        
        if response.status_code == 200 and "status" not in json_response:
            return json_response  # Snapshot is ready, return JSON data
        
        time.sleep(30)  # Retry every 30 seconds

@app.route("/get_instagram_data", methods=["GET"])
def get_instagram_data():
    """API Endpoint: Takes username and returns Instagram data"""
    username = request.args.get("username")
    if not username:
        return jsonify({"error": "Username parameter is required"}), 400

    snapshot_id = get_snapshot_id(username)
    if not snapshot_id:
        return jsonify({"error": "Failed to get snapshot ID"}), 500
    
    json_data = wait_for_snapshot(snapshot_id)
    
    # Explicitly set CORS headers in response
    response = jsonify(json_data)
    response.headers.add("Access-Control-Allow-Origin", "*")
    
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
