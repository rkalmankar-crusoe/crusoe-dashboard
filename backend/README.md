# Crusoe Cloud Dashboard - Backend

Backend tools and scripts for the Crusoe Cloud GPU Infrastructure Dashboard.

## Overview

This backend provides:
1. **Flask API Server** - Web server with REST API for live data refresh
2. **Real-time metrics** from deployed customer instances via Crusoe CLI
3. **Physical datacenter inventory** from admin API with hierarchical drill-down
4. **Capacity query tools** for quickly finding available GPUs for POCs

## Quick Start

Start the dashboard server:

```bash
cd /Users/rkalmankar/Documents/GitHub/crusoe-dashboard
./start-dashboard.sh
```

Then open your browser to:
- **Capacity Dashboard**: http://localhost:5000
- **Customer Dashboard**: http://localhost:5000/index.html

Click the "Refresh" button in the dashboard to trigger a live data update with progress tracking.

## Directory Structure

```
backend/
├── app.py                              # Flask API server (NEW!)
├── data/
│   ├── metrics.json                    # Customer-facing metrics (deployed instances)
│   ├── admin_nodes_inventory.json      # Raw admin node inventory (all physical nodes)
│   └── datacenter_inventory.json       # Processed hierarchical inventory
├── scripts/
│   ├── update_metrics.py               # Fetch customer metrics via Crusoe CLI
│   ├── process_admin_inventory.py      # Process admin inventory into hierarchy
│   └── query_capacity.py               # Query available capacity for POCs
└── requirements.txt
```

## Setup

### Prerequisites

1. **Crusoe CLI** - Customer-facing API
   ```bash
   brew install crusoe-cloud/tap/crusoe
   crusoe config init
   ```

2. **cloud-admin CLI** - Admin API (internal tool)
   ```bash
   # cloud-admin should be installed at /Users/rkalmankar/go/bin/cloud-admin
   cloud-admin --version
   ```

3. **Python Dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

## Flask API Server

The backend now includes a Flask web server (`app.py`) that serves both dashboards and provides REST API endpoints for live data refresh.

### Starting the Server

```bash
# From the repository root
./start-dashboard.sh

# Or manually
cd backend
python3 app.py
```

The server will start at `http://localhost:5000`

### Available Dashboards

- **Capacity Dashboard** (`/`): Hierarchical datacenter inventory with drill-down (Region → Floor → IB Fabric → Rack → Node → GPU)
- **Customer Dashboard** (`/index.html`): Deployed instances and customer metrics

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/refresh` | Trigger background data refresh (cloud-admin fetch + processing) |
| `GET` | `/api/refresh/status` | Get current refresh progress (0-100%) and status message |
| `GET` | `/api/data/inventory` | Fetch datacenter inventory JSON |
| `GET` | `/api/data/metrics` | Fetch customer metrics JSON |

### Live Refresh with Progress Tracking

The dashboards now support **live data refresh** from the UI:

1. Click the "Refresh" button in either dashboard
2. Backend triggers three-step refresh process:
   - **Step 1 (10%)**: Fetch raw inventory from `cloud-admin nodes list`
   - **Step 2 (50%)**: Process into hierarchical structure
   - **Step 3 (80%)**: Update customer metrics via Crusoe CLI
3. Frontend polls `/api/refresh/status` every 500ms
4. Animated progress bar shows current status
5. Dashboard automatically reloads when refresh completes (100%)

**Refresh Process** (typically 30-60 seconds):
```
Fetching node inventory from cloud-admin... →
Processing datacenter hierarchy... →
Updating customer metrics... →
Refresh complete!
```

### API Usage Examples

**Trigger data refresh:**
```bash
curl -X POST http://localhost:5000/api/refresh
```

**Check refresh status:**
```bash
curl http://localhost:5000/api/refresh/status
# Returns: {"in_progress": true, "progress": 50, "message": "Processing datacenter hierarchy...", "error": null}
```

**Fetch inventory data:**
```bash
curl http://localhost:5000/api/data/inventory | jq '.global_stats'
```

## Usage (Command-Line Scripts)

### 1. Fetch Customer Metrics (Deployed Instances)

This fetches metrics about currently deployed customer instances:

```bash
python3 scripts/update_metrics.py
```

**Output**: `data/metrics.json`

**Data**: 216 deployed nodes, 1,077 GPUs across customer projects

### 2. Fetch Physical Datacenter Inventory

This fetches the complete physical datacenter capacity (all nodes, not just deployed):

```bash
# Fetch raw inventory from cloud-admin
/Users/rkalmankar/go/bin/cloud-admin nodes list --format json > data/admin_nodes_inventory.json

# Process into hierarchical structure
python3 scripts/process_admin_inventory.py
```

**Output**: `data/datacenter_inventory.json`

**Data**: 3,642 total physical nodes, 23,986 GPUs

**Hierarchy**: Region → Floor → Rack → IB Fabric → Node → GPU

### 3. Query Available Capacity

Find available GPUs for POC provisioning:

```bash
python3 scripts/query_capacity.py
```

**Features**:
- Filter by GPU type (H100, H200, GB200, L40S, etc.)
- Filter by location (Iceland, Virginia, Dallas, US West)
- Filter by floor, rack, or IB fabric
- Find nodes with minimum GPU count
- Summary by location, GPU type, and IB fabric

## Data Overview

### Customer Metrics (metrics.json)

Tracks **deployed instances** (what customers are currently using):

```json
{
  "global_summary": {
    "total_nodes": 216,
    "total_gpus": 1077,
    "available_nodes": 168
  },
  "gpu_models": {
    "GB200-NVL-186GB": {"gpus": 660},
    "L40S-48GB": {"gpus": 137},
    "H100-SXM-80GB": {"gpus": 112}
  }
}
```

### Datacenter Inventory (datacenter_inventory.json)

Tracks **physical datacenter capacity** (total infrastructure):

```json
{
  "global_stats": {
    "total_nodes": 3642,
    "total_gpus": 23986,
    "available_nodes": 669,
    "available_gpus": 3688
  },
  "locations": {
    "icat-m": {
      "name": "Iceland",
      "total_nodes": 2455,
      "total_gpus": 16336,
      "available_gpus": 2452,
      "floors": {
        "m11a": {
          "racks": {
            "r102": {
              "ib_fabrics": {
                "8822f711-05c6-4f...": {
                  "nodes": [...]
                }
              }
            }
          }
        }
      }
    }
  }
}
```

## GPU Fleet Breakdown

### Physical Datacenter Capacity (Total: 23,986 GPUs)

| GPU Model | Total GPUs | Available | Percentage |
|-----------|------------|-----------|------------|
| H200-SXM-141GB | 8,160 | 2,088 | 34.0% |
| H100-SXM-80GB | 6,384 | 432 | 26.6% |
| B200-SXM-180GB | 4,080 | 64 | 17.0% |
| GB200-NVL-186GB | 2,304 | 260 | 9.6% |
| L40S-48GB | 1,920 | 584 | 8.0% |
| A100-SXM-80GB | 512 | 144 | 2.1% |
| MI300X-192GB (AMD) | 504 | 16 | 2.1% |
| A100-PCIe-80GB | 122 | 100 | 0.5% |

### By Location

| Location | Nodes | GPUs | Available GPUs | Floors |
|----------|-------|------|----------------|--------|
| Iceland | 2,455 | 16,336 | 2,452 | 14 |
| Virginia | 659 | 4,626 | 615 | 6 |
| Dallas | 440 | 2,944 | 544 | 4 |
| US West | 88 | 80 | 77 | 1 |

## Query Examples

### Find all available H100 nodes

```python
from scripts.query_capacity import find_available_capacity, summarize_capacity

nodes = find_available_capacity(gpu_type="H100-SXM-80GB")
summary = summarize_capacity(nodes)
# Result: 54 nodes, 432 GPUs available
```

### Find H200 nodes in Iceland

```python
nodes = find_available_capacity(gpu_type="H200-SXM-141GB", location="Iceland")
summary = summarize_capacity(nodes)
# Result: 261 nodes, 2,088 GPUs in Iceland
#   - Floor m11a: 231 nodes (1,848 GPUs) - single IB fabric!
```

### Find any nodes with 8+ GPUs

```python
nodes = find_available_capacity(min_gpus=8)
summary = summarize_capacity(nodes)
# Result: 416 nodes, 3,328 GPUs available
```

### Find available GB200 Grace Blackwell superchips

```python
nodes = find_available_capacity(gpu_type="GB200-NVL-186GB")
summary = summarize_capacity(nodes)
# Result: 65 nodes, 260 GPUs (all in Iceland Floor m21)
```

## POC Provisioning Recommendations

### Large-scale H200 Training (100+ nodes)
- **Location**: Iceland, Floor m11a
- **IB Fabric**: `8822f711-05c6-4f...`
- **Available**: 231 nodes (1,848 GPUs)
- **Benefit**: Single IB fabric for maximum interconnect bandwidth

### GB200 Grace Blackwell Testing
- **Location**: Iceland, Floor m21
- **Available**: 65 nodes (260 GPUs)
- **Architecture**: Grace CPU + Blackwell GPUs for AI workloads

### L40S Inference Workloads
- **Location**: Virginia + Dallas
- **Available**: 73 nodes (584 GPUs)
- **Use case**: Cost-effective inference, graphics, video processing

### H100 Development/Testing
- **Location**: Dallas (highest availability)
- **Available**: 37 nodes (296 GPUs)
- **IB Fabric**: `0c2e87a3-706b-4b...` has 22 nodes

## Security & Safety

**IMPORTANT**: All scripts and API endpoints perform READ-ONLY operations:
- ✅ Query node status
- ✅ Fetch inventory data
- ✅ Read capacity information
- ✅ Serve dashboards and static files
- ❌ NO destructive actions
- ❌ NO instance creation/deletion
- ❌ NO configuration changes
- ❌ NO write access to cloud infrastructure

**Flask Server**: Runs on `localhost:5000` by default. For production deployment, consider:
- Setting up proper authentication
- Using a production WSGI server (e.g., gunicorn)
- Enabling HTTPS
- Restricting CORS origins

## Automation

### Option 1: Web UI Refresh (Recommended)

Use the "Refresh" button in the dashboard for on-demand updates with visual progress tracking.

### Option 2: Scheduled Refresh (Cron)

```bash
# Add to crontab for automatic hourly updates
0 * * * * cd /Users/rkalmankar/Documents/GitHub/crusoe-dashboard/backend && python3 scripts/update_metrics.py

# Refresh admin inventory daily
0 0 * * * /Users/rkalmankar/go/bin/cloud-admin nodes list --format json > /Users/rkalmankar/Documents/GitHub/crusoe-dashboard/backend/data/admin_nodes_inventory.json && python3 /Users/rkalmankar/Documents/GitHub/crusoe-dashboard/backend/scripts/process_admin_inventory.py
```

### Option 3: API Automation

```bash
# Trigger refresh via API
curl -X POST http://localhost:5000/api/refresh

# Or create a script to wait for completion
while true; do
  STATUS=$(curl -s http://localhost:5000/api/refresh/status | jq -r '.in_progress')
  if [ "$STATUS" = "false" ]; then
    echo "Refresh complete!"
    break
  fi
  sleep 5
done
```

## Troubleshooting

### Flask server issues

```bash
# Check if Flask is installed
pip3 list | grep -i flask

# Reinstall dependencies
pip3 install -r requirements.txt

# Check if port 5000 is already in use
lsof -i :5000

# Run with debug output
cd backend
python3 app.py
```

### cloud-admin authentication issues

```bash
# Check cloud-admin config
cat ~/.crusoe/cloud-admin

# Verify admin token exists
ls -la ~/.crusoe/admin-token-prod
```

### Crusoe CLI issues

```bash
# Re-initialize Crusoe CLI
crusoe config init

# Test API access
crusoe projects list
```

## Contact

For questions or issues with the dashboard backend, contact the infrastructure team.
