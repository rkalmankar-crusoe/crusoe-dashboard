#!/usr/bin/env python3
"""
Crusoe Dashboard API Server

Simple Flask server that serves the dashboard and provides API endpoints
for refreshing datacenter inventory data.

IMPORTANT: Only performs READ operations via CLI tools.
"""

from flask import Flask, jsonify, send_from_directory, session, request
from flask_cors import CORS
import subprocess
import json
import os
import base64
from pathlib import Path
import threading
import time
from datetime import datetime
import secrets

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.secret_key = secrets.token_hex(32)  # Generate random secret key for sessions
CORS(app, supports_credentials=True)

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

# Session management helpers
def get_token_file():
    """Get the path to the admin token file."""
    return Path.home() / ".crusoe" / "admin-token-prod"

def validate_token():
    """Check if a valid token exists."""
    token_file = get_token_file()
    if not token_file.exists():
        return False, "Token file not found"

    try:
        with open(token_file, 'r') as f:
            token = f.read().strip()

        # Decode JWT payload to verify it's valid
        parts = token.split('.')
        if len(parts) < 2:
            return False, "Invalid token format"

        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding

        decoded = base64.urlsafe_b64decode(payload)
        token_data = json.loads(decoded)

        # Check if token has expired (if exp field exists)
        if 'exp' in token_data:
            exp_time = datetime.fromtimestamp(token_data['exp'])
            if datetime.now() > exp_time:
                return False, "Token has expired"

        return True, token_data
    except Exception as e:
        return False, f"Token validation failed: {str(e)}"

def require_session(f):
    """Decorator to require valid session for endpoints."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        return f(*args, **kwargs)
    return decorated_function

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

        # Pass environment variables needed by cloud-admin (HOME, PATH, etc.)
        env = os.environ.copy()

        result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)

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


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login endpoint - creates a session if valid token exists."""
    valid, result = validate_token()

    if not valid:
        return jsonify({
            "success": False,
            "error": result
        }), 401

    # Create session
    session['authenticated'] = True
    session['user_data'] = result
    session.permanent = True

    # Get user email
    try:
        email_result = subprocess.run(
            ['git', 'config', 'user.email'],
            capture_output=True,
            text=True,
            timeout=2
        )
        user_email = email_result.stdout.strip() if email_result.returncode == 0 else os.getenv('USER', 'unknown')
    except Exception:
        user_email = os.getenv('USER', 'unknown')

    return jsonify({
        "success": True,
        "user_email": user_email
    })


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout endpoint - clears the session."""
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"})


@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Check if user is authenticated."""
    authenticated = session.get('authenticated', False)
    if authenticated:
        try:
            email_result = subprocess.run(
                ['git', 'config', 'user.email'],
                capture_output=True,
                text=True,
                timeout=2
            )
            user_email = email_result.stdout.strip() if email_result.returncode == 0 else os.getenv('USER', 'unknown')
        except Exception:
            user_email = os.getenv('USER', 'unknown')

        return jsonify({
            "authenticated": True,
            "user_email": user_email
        })
    else:
        return jsonify({"authenticated": False})


@app.route('/api/refresh', methods=['POST'])
@require_session
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
@require_session
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
@require_session
def get_metrics():
    """Get customer metrics."""
    metrics_file = DATA_DIR / "metrics.json"
    try:
        with open(metrics_file, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "Metrics data not found"}), 404


@app.route('/api/auth/info', methods=['GET'])
@require_session
def get_auth_info():
    """Get authentication information (user and token details)."""
    try:
        # Read JWT token
        token_file = Path.home() / ".crusoe" / "admin-token-prod"
        with open(token_file, 'r') as f:
            token = f.read().strip()

        # Decode JWT payload (without signature verification)
        parts = token.split('.')
        if len(parts) >= 2:
            payload = parts[1]
            # Add padding if needed
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding

            decoded = base64.urlsafe_b64decode(payload)
            token_data = json.loads(decoded)

            # Get user email from git config
            try:
                result = subprocess.run(
                    ['git', 'config', 'user.email'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                user_email = result.stdout.strip() if result.returncode == 0 else os.getenv('USER', 'unknown')
            except Exception:
                user_email = os.getenv('USER', 'unknown')

            # Extract token info
            issued_at = token_data.get('iat', 0)
            issued_datetime = datetime.fromtimestamp(issued_at) if issued_at > 0 else None

            # Check for token expiration
            expires_at = token_data.get('exp')
            expires_datetime = None
            expires_display = "No expiration"
            expires_in_seconds = None

            if expires_at:
                expires_datetime = datetime.fromtimestamp(expires_at)
                expires_in_seconds = (expires_datetime - datetime.now()).total_seconds()

                if expires_in_seconds < 0:
                    expires_display = "Expired"
                elif expires_in_seconds < 3600:  # Less than 1 hour
                    minutes = int(expires_in_seconds / 60)
                    expires_display = f"{minutes} min"
                elif expires_in_seconds < 86400:  # Less than 1 day
                    hours = int(expires_in_seconds / 3600)
                    expires_display = f"{hours} hour{'s' if hours != 1 else ''}"
                else:
                    days = int(expires_in_seconds / 86400)
                    expires_display = f"{days} day{'s' if days != 1 else ''}"

            # Calculate token age (when it was issued)
            age_display = "unknown"
            age_seconds = None
            if issued_datetime:
                age_seconds = (datetime.now() - issued_datetime).total_seconds()
                age_hours = int(age_seconds / 3600)
                age_days = int(age_hours / 24)

                if age_days > 0:
                    age_display = f"{age_days} day{'s' if age_days != 1 else ''} ago"
                elif age_hours > 0:
                    age_display = f"{age_hours} hour{'s' if age_hours != 1 else ''} ago"
                else:
                    age_display = "< 1 hour ago"

            return jsonify({
                "user_email": user_email,
                "token_issued_at": issued_datetime.isoformat() if issued_datetime else None,
                "token_age": age_display,
                "token_age_seconds": int(age_seconds) if age_seconds else None,
                "token_expires_at": expires_datetime.isoformat() if expires_datetime else None,
                "token_expires_in": expires_display,
                "token_expires_in_seconds": int(expires_in_seconds) if expires_in_seconds else None,
                "okta_subject": token_data.get('sub', 'unknown')
            })
        else:
            return jsonify({"error": "Invalid token format"}), 500

    except FileNotFoundError:
        return jsonify({"error": "Token file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    print("  - GET /api/auth/info - Get authentication info")
    print("\n" + "=" * 60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=port)
