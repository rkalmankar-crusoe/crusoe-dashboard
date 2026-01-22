#!/usr/bin/env python3
"""
Crusoe Cloud GPU Infrastructure Metrics Updater

This script fetches GPU infrastructure metrics from Crusoe Cloud using the CLI
and updates the metrics.json file used by the dashboard.

IMPORTANT: This script only performs READ operations via the Crusoe CLI.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
METRICS_FILE = DATA_DIR / "metrics.json"

# GPU pricing estimates (monthly per GPU in USD)
GPU_PRICING = {
    "A100-PCIe-40GB": 1000,
    "A100-PCIe-80GB": 1200,
    "A100-SXM-80GB": 1500,
    "L40S-48GB": 800,
    "H100-80GB": 2500,
    "H200-141GB": 3000,
    "MI300X": 2500,
}

def run_crusoe_command(args):
    """
    Execute Crusoe CLI command safely (READ-only)

    Args:
        args (list): Command arguments

    Returns:
        dict: Parsed JSON response
    """
    try:
        cmd = ["crusoe"] + args + ["--json"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from command output: {e}")
        return None

def fetch_all_projects():
    """Fetch all projects (READ-only)"""
    print("→ Fetching projects...")
    projects = run_crusoe_command(["projects", "list"])
    if projects:
        print(f"  Found {len(projects)} projects")
    return projects or []

def fetch_vm_types():
    """Fetch available VM types (READ-only)"""
    print("→ Fetching VM types...")
    return run_crusoe_command(["compute", "vms", "types"])

def fetch_locations():
    """Fetch available locations (READ-only)"""
    print("→ Fetching locations...")
    return run_crusoe_command(["locations", "list"])

def fetch_instances_for_project(project_id):
    """Fetch all instances for a project (READ-only)"""
    return run_crusoe_command(["compute", "vms", "list", "--project-id", project_id])

def fetch_crusoe_metrics():
    """
    Fetch current infrastructure metrics from Crusoe Cloud CLI (READ-only)

    Returns:
        dict: Infrastructure metrics data
    """
    print("\n" + "="*60)
    print("FETCHING CRUSOE CLOUD INFRASTRUCTURE METRICS (READ-ONLY)")
    print("="*60 + "\n")

    # Fetch available VM types for GPU info
    vm_types = fetch_vm_types()

    # Fetch all projects
    projects = fetch_all_projects()

    # Fetch locations
    locations = fetch_locations() or []

    # Aggregate metrics
    gpu_counts = defaultdict(int)
    location_counts = defaultdict(lambda: {"nodes": 0, "gpus": 0})
    state_counts = defaultdict(int)
    total_nodes = 0
    total_gpus = 0

    print("\n→ Fetching instances across all projects...")

    # Query instances from each project
    for project in projects:
        project_id = project.get("id")
        project_name = project.get("name")

        instances = fetch_instances_for_project(project_id)
        if not instances:
            continue

        print(f"  {project_name}: {len(instances)} instances")

        for instance in instances:
            vm_type = instance.get("type", "")
            location = instance.get("location", "unknown")
            state = instance.get("state", "unknown")

            # Find GPU info from VM types
            gpu_type = None
            num_gpus = 0

            if vm_types:
                for vt in vm_types:
                    if vt.get("product_name") == vm_type:
                        gpu_type = vt.get("gpu_type", "")
                        num_gpus = vt.get("num_gpu", 0)
                        break

            if gpu_type and num_gpus > 0:
                gpu_counts[gpu_type] += num_gpus
                location_counts[location]["nodes"] += 1
                location_counts[location]["gpus"] += num_gpus
                total_nodes += 1
                total_gpus += num_gpus
                state_counts[state] += 1

    # Calculate vendor split
    nvidia_gpus = sum(count for gpu, count in gpu_counts.items() if "MI300X" not in gpu)
    amd_gpus = gpu_counts.get("MI300X", 0)

    # Calculate estimated revenue
    monthly_revenue = sum(
        count * GPU_PRICING.get(gpu_type, 1000)
        for gpu_type, count in gpu_counts.items()
    )

    # Map location codes to friendly names
    location_map = {
        "us-southcentral1-a": "dallas",
        "us-east1-a": "virginia",
        "eu-iceland1-a": "iceland",
        "us-west1-a": "us-west"
    }

    # Build metrics structure
    metrics = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "global_summary": {
            "total_nodes": total_nodes,
            "total_gpus": total_gpus,
            "monthly_revenue": int(monthly_revenue),
            "available_nodes": state_counts.get("STATE_RUNNING", 0)
        },
        "vendors": {
            "nvidia": {"gpus": nvidia_gpus, "percentage": 0},
            "amd": {"gpus": amd_gpus, "percentage": 0}
        },
        "regions": {},
        "gpu_models": {},
        "states": dict(state_counts),
        "raw_location_data": dict(location_counts)
    }

    # Add region details
    for location_code, data in location_counts.items():
        friendly_name = location_map.get(location_code, location_code)
        metrics["regions"][friendly_name] = {
            "name": location_code,
            "nodes": data["nodes"],
            "gpus": data["gpus"],
            "monthly_revenue": int(data["gpus"] * 1500)  # Estimate
        }

    # Add GPU model details
    for gpu_type, count in gpu_counts.items():
        metrics["gpu_models"][gpu_type] = {
            "gpus": count,
            "percentage": 0  # Will be calculated later
        }

    print(f"\n✓ Aggregated {total_nodes} nodes with {total_gpus} GPUs")
    print(f"  NVIDIA: {nvidia_gpus} GPUs")
    print(f"  AMD: {amd_gpus} GPUs")
    print(f"  Estimated Revenue: ${monthly_revenue:,.0f}/month\n")

    return metrics

def calculate_derived_metrics(metrics):
    """
    Calculate derived metrics like percentages, revenue, etc.
    
    Args:
        metrics (dict): Raw metrics data
        
    Returns:
        dict: Metrics with derived values added
    """
    # Calculate vendor percentages
    total_gpus = metrics["global_summary"]["total_gpus"]
    if total_gpus > 0:
        nvidia_gpus = metrics["vendors"]["nvidia"]["gpus"]
        amd_gpus = metrics["vendors"]["amd"]["gpus"]
        metrics["vendors"]["nvidia"]["percentage"] = round((nvidia_gpus / total_gpus) * 100, 1)
        metrics["vendors"]["amd"]["percentage"] = round((amd_gpus / total_gpus) * 100, 1)
    
    # Calculate GPU model percentages
    for model in metrics.get("gpu_models", {}).values():
        if total_gpus > 0:
            model["percentage"] = round((model["gpus"] / total_gpus) * 100)
    
    return metrics

def save_metrics(metrics):
    """
    Save metrics to JSON file
    
    Args:
        metrics (dict): Metrics data to save
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"Metrics saved to {METRICS_FILE}")

def main():
    """Main execution function"""
    try:
        # Fetch metrics from API
        raw_metrics = fetch_crusoe_metrics()
        
        # Calculate derived metrics
        processed_metrics = calculate_derived_metrics(raw_metrics)
        
        # Save to file
        save_metrics(processed_metrics)
        
        print("✓ Metrics update completed successfully")
        
    except Exception as e:
        print(f"✗ Error updating metrics: {e}")
        raise

if __name__ == "__main__":
    main()
