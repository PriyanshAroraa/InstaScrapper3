from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import time
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "OPTIONS"]}})

@app.after_request
def add_cors_headers(response):
    """Add CORS headers for cross-origin requests"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# 🔐 Bright Data API Key
API_KEY = "60a18bcb5ff44e333b12b04b65c0bbf41cf6f957a5ec2f323d019de6531015c6"

# 📊 Dataset IDs for Different Platforms
DATASETS = {
    "instagram": "gd_l1vikfch901nx3by4",
    "linkedin": "gd_l1vikfnt1wgvvqz95w",
    "twitter": "gd_lwxmeb2u1cniijd7t4",
    "facebook": "gd_lkaxegm826bjpoo9m5"
}

# 🌍 API Endpoints
TRIGGER_URL = "https://api.brightdata.com/datasets/v3/trigger"
SNAPSHOT_URL = "https://api.brightdata.com/datasets/v3/snapshot/{}?format=json"

def get_snapshot_id(platform, urls):
    """Trigger Bright Data request and get snapshot ID for the selected platform"""
    if platform not in DATASETS:
        return None

    dataset_id = DATASETS[platform]
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = json.dumps(urls)
    
    try:
        response = requests.post(f"{TRIGGER_URL}?dataset_id={dataset_id}&include_errors=true", headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        print(f"✅ Snapshot ID Triggered for {platform}: {response.json()}")
        return response.json().get("snapshot_id")
    except Exception as e:
        print(f"❌ Error in get_snapshot_id ({platform}): {str(e)}")
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
                return json_response  # Return JSON data
            
            print("⏳ Waiting for snapshot... Retrying in 30 sec...")
            time.sleep(30)

    except Exception as e:
        print(f"❌ Error in wait_for_snapshot: {str(e)}")
        return {"error": str(e)}

@app.route("/get_social_data", methods=["GET", "OPTIONS"])
def get_social_data():
    if request.method == "OPTIONS":
        return jsonify({}), 200  # Respond to preflight CORS requests

    platform = request.args.get("platform")
    username = request.args.get("username")

    if not platform or platform.lower() not in DATASETS:
        return jsonify({"error": "Invalid or missing platform"}), 400

    if not username:
        return jsonify({"error": "Username parameter is required"}), 400

    platform = platform.lower()

    # 🔄 Different API structures for each platform
    if platform == "instagram":
        urls = [{"url": f"https://www.instagram.com/{username}/"}]
    elif platform == "linkedin":
        urls = [{"url": f"https://www.linkedin.com/company/{username}"}]
    elif platform == "twitter":
        urls = [{"url": f"https://x.com/{username}", "max_number_of_posts": 10}]
    elif platform == "facebook":
        urls = [{"url": f"https://www.facebook.com/{username}/", "num_of_posts": 50}]
    else:
        return jsonify({"error": "Invalid platform"}), 400

    snapshot_id = get_snapshot_id(platform, urls)
    if not snapshot_id:
        return jsonify({"error": f"Failed to get snapshot ID for {platform}"}), 500

    json_data = wait_for_snapshot(snapshot_id)
    return jsonify(json_data)

PORT = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
