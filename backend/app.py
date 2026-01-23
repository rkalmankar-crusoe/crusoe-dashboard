#!/usr/bin/env python3
"""
Crusoe Dashboard API Server

Simple Flask server that serves the dashboard and provides API endpoints
for refreshing datacenter inventory data.

IMPORTANT: Only performs READ operations via CLI tools.
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import subprocess
import json
from pathlib import Path
import threading
import time

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Configuration
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# Track refresh status
refresh_status = {
    "in_progress": False,
    "progress": 0,
    "message": "",
    "error": None,
    "last_updated": None
}

def run_refresh_task():
    """Background task to refresh datacenter inventory."""
    global refresh_status

    try:
        refresh_status["in_progress"] = True
        refresh_status["progress"] = 10
        refresh_status["message"] = "Fetching node inventory from cloud-admin..."
        refresh_status["error"] = None

        # Step 1: Fetch raw inventory from cloud-admin
        admin_inventory_file = DATA_DIR / "admin_nodes_inventory.json"
        cmd = [
            str(Path.home() / "go/bin/cloud-admin"),
            "nodes", "list", "--format", "json"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        with open(admin_inventory_file, 'w') as f:
            f.write(result.stdout)

        refresh_status["progress"] = 50
        refresh_status["message"] = "Processing datacenter hierarchy..."
        time.sleep(0.5)  # Small delay to show progress

        # Step 2: Process inventory into hierarchy
        process_script = BASE_DIR / "scripts" / "process_admin_inventory.py"
        subprocess.run(["python3", str(process_script)], check=True)

        refresh_status["progress"] = 80
        refresh_status["message"] = "Updating customer metrics..."
        time.sleep(0.5)

        # Step 3: Update customer metrics
        metrics_script = BASE_DIR / "scripts" / "update_metrics.py"
        subprocess.run(["python3", str(metrics_script)], check=True)

        refresh_status["progress"] = 100
        refresh_status["message"] = "Refresh complete!"
        refresh_status["last_updated"] = time.time()

    except subprocess.CalledProcessError as e:
        refresh_status["error"] = f"Command failed: {e.stderr if e.stderr else str(e)}"
        refresh_status["message"] = "Refresh failed"
    except Exception as e:
        refresh_status["error"] = str(e)
        refresh_status["message"] = "Refresh failed"
    finally:
        time.sleep(1)  # Keep status visible for a moment
        refresh_status["in_progress"] = False


@app.route('/')
def index():
    """Serve the capacity dashboard."""
    return send_from_directory(str(FRONTEND_DIR), 'capacity.html')


@app.route('/index.html')
def customer_dashboard():
    """Serve the customer-facing dashboard."""
    return send_from_directory(str(FRONTEND_DIR), 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory(str(FRONTEND_DIR), path)


@app.route('/api/refresh', methods=['POST'])
def trigger_refresh():
    """Trigger a data refresh."""
    global refresh_status

    if refresh_status["in_progress"]:
        return jsonify({
            "status": "in_progress",
            "message": "Refresh already in progress"
        }), 409

    # Start refresh in background thread
    thread = threading.Thread(target=run_refresh_task)
    thread.daemon = True
    thread.start()

    return jsonify({
        "status": "started",
        "message": "Data refresh started"
    })


@app.route('/api/refresh/status', methods=['GET'])
def get_refresh_status():
    """Get current refresh status."""
    return jsonify(refresh_status)


@app.route('/api/data/inventory', methods=['GET'])
def get_inventory():
    """Get datacenter inventory."""
    inventory_file = DATA_DIR / "datacenter_inventory.json"
    try:
        with open(inventory_file, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "Inventory data not found"}), 404


@app.route('/api/data/metrics', methods=['GET'])
def get_metrics():
    """Get customer metrics."""
    metrics_file = DATA_DIR / "metrics.json"
    try:
        with open(metrics_file, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "Metrics data not found"}), 404


if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001

    print("=" * 60)
    print("Crusoe Dashboard Server")
    print("=" * 60)
    print(f"\nStarting server at http://localhost:{port}")
    print("\nAvailable dashboards:")
    print(f"  - Capacity Dashboard: http://localhost:{port}/")
    print(f"  - Customer Dashboard: http://localhost:{port}/index.html")
    print("\nAPI Endpoints:")
    print("  - POST /api/refresh - Trigger data refresh")
    print("  - GET /api/refresh/status - Get refresh status")
    print("  - GET /api/data/inventory - Get inventory data")
    print("  - GET /api/data/metrics - Get metrics data")
    print("\n" + "=" * 60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=port)
